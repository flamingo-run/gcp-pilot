from datetime import datetime
from pathlib import Path
from typing import Any

from google.cloud import bigquery
from google.cloud.bigquery import DatasetReference, Table

from gcp_pilot import exceptions
from gcp_pilot.base import GoogleCloudPilotAPI, friendly_http_error
from gcp_pilot.storage import CloudStorage


class BigQuery(GoogleCloudPilotAPI):
    _client_class = bigquery.Client

    def _get_project_default_location(self, project_id: str | None = None) -> str | None:
        return "us"

    def _dataset_ref(self, dataset_name: str, project_id: str | None = None) -> DatasetReference:
        return self.client.dataset(
            dataset_id=dataset_name,
            project=project_id or self.project_id,
        )

    def list_datasets(self):
        yield from self.client.list_datasets()

    def list_tables(self, dataset_id: str):
        yield from self.client.list_tables(dataset=dataset_id)

    @friendly_http_error
    def create_table(self, table: Table):
        return self.client.create_table(table=table)

    @friendly_http_error
    def delete_table(self, table: Table):
        return self.client.delete_table(table=table)

    def execute(
        self,
        sql: str,
        params: dict[str, Any] | None = None,
        destination_table_name: str | None = None,
        destination_dataset_name: str | None = None,
        destination_project: str | None = None,
        truncate: bool | None = None,
    ):
        job_config = bigquery.QueryJobConfig()
        if destination_table_name or destination_dataset_name:
            if not destination_table_name and destination_dataset_name:
                raise exceptions.ValidationError(
                    "Both destination_dataset_name and destination_table_name must be provided.",
                )
            destination_project = destination_project or self.project_id
            destination_dataset = destination_dataset_name
            destination = f"{destination_project}.{destination_dataset}.{destination_table_name}"
            job_config.destination = destination
            if truncate:
                job_config.write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
            elif truncate is False:
                job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND

        if params:
            query_params = [_BigQueryParam.parse(key, value) for key, value in params.items()]
            job_config.query_parameters = query_params

        query_job = self.client.query(sql, job_config=job_config)
        return self._wait_for_job(job=query_job)

    def insert_rows(self, dataset_name: str, table_name: str, rows, project_id: str | None = None):
        table = self.get_table(
            table_name=table_name,
            project_id=project_id,
            dataset_name=dataset_name,
        )
        errors = self.client.insert_rows(table=table, rows=rows)
        if errors:
            raise ValueError(f"Bigquery insert error: {errors}")

    def get_table(self, table_name: str, project_id: str | None = None, dataset_name: str | None = None) -> Table:
        dataset_ref = self._dataset_ref(project_id=project_id, dataset_name=dataset_name)
        table_ref = dataset_ref.table(table_id=table_name)
        return self.client.get_table(table_ref)

    def load(
        self,
        table_name: str,
        filename: str,
        project_id: str | None = None,
        dataset_name: str | None = None,
        schema=None,
        wait: bool = False,
        truncate: bool | None = None,
        gcs_bucket: str | None = None,
    ) -> None:
        job_config = bigquery.LoadJobConfig()
        if schema:
            job_config.schema = schema
        else:
            job_config.autodetect = True

        extension = filename.split(".")[-1]
        if extension == "json":
            source_format = bigquery.job.SourceFormat.NEWLINE_DELIMITED_JSON
        elif extension == "csv":
            source_format = bigquery.job.SourceFormat.CSV
        else:
            message = f"Unsupported BigQuery Source format {extension}"
            raise exceptions.UnsupportedFormatException(message)

        job_config.source_format = source_format
        if truncate:
            job_config.write_disposition = bigquery.WriteDisposition.WRITE_TRUNCATE
        elif truncate is False:
            job_config.write_disposition = bigquery.WriteDisposition.WRITE_APPEND

        dataset_ref = self._dataset_ref(
            project_id=project_id or self.project_id,
            dataset_name=dataset_name,
        )
        target_ref = dataset_ref.table(table_name)

        is_gcs = filename.startswith("gs://")
        if not is_gcs:
            if gcs_bucket:
                gcs = CloudStorage(project_id=self.project_id)
                blob = gcs.upload(
                    source_file=filename,
                    bucket_name=gcs_bucket,
                )
                file_url = gcs.get_uri(blob=blob)

                load_job = self.client.load_table_from_uri(
                    source_uris=file_url,
                    destination=target_ref,
                    job_config=job_config,
                )
            else:
                with Path(filename).open("rb") as file:
                    load_job = self.client.load_table_from_file(
                        file_obj=file,
                        destination=target_ref,
                        job_config=job_config,
                    )
        else:
            load_job = self.client.load_table_from_uri(
                source_uris=filename,
                destination=target_ref,
                job_config=job_config,
            )

        if wait:
            self._wait_for_job(job=load_job)

    def copy(
        self,
        source_dataset_name: str,
        source_table_name: str,
        destination_table_name: str,
        destination_dataset_name: str,
        destination_project: str | None = None,
        wait: bool = False,
    ) -> None:
        source_ref = self.get_table(dataset_name=source_dataset_name, table_name=source_table_name)
        dataset_ref = self._dataset_ref(
            project_id=destination_project or self.project_id,
            dataset_name=destination_dataset_name,
        )
        target_ref = dataset_ref.table(destination_table_name)

        job = self.client.copy_table(sources=source_ref, destination=target_ref)
        if wait:
            self._wait_for_job(job=job)

    @classmethod
    def date_to_str(cls, dt, table_suffix=False):
        if table_suffix:
            mask = "%Y%m%d"
        elif isinstance(dt, datetime):
            mask = "%Y-%m-%d %H:%M:%S"
        else:
            mask = "%Y-%m-%d"
        return dt.strftime(mask)

    def _wait_for_job(self, job):
        try:
            return job.result()
        except Exception as exc:
            raise exceptions.BigQueryJobError(job) from exc

    def add_external_gcs_source(
        self,
        gcs_url: str,
        dataset_name: str,
        table_name: str,
        skip_rows: int = 0,
        delimiter: str = ",",
        quote: str = '"',
        source_format: str = "CSV",
        project_id: str | None = None,
    ):
        dataset_ref = self._dataset_ref(dataset_name=dataset_name, project_id=project_id)
        table = dataset_ref.table(table_name)

        external_config = bigquery.ExternalConfig(source_format=source_format)
        external_config.autodetect = True
        external_config.source_uris = [gcs_url]
        external_config.options.skip_leading_rows = skip_rows
        external_config.options.field_delimiter = delimiter
        external_config.options.quote = quote

        table.external_data_configuration = external_config

        return self.client.create_table(table)


class _BigQueryParam:
    @classmethod
    def _get_type(cls, variable: Any) -> str:
        TYPES = {
            "int": "INT64",
            "str": "STRING",
            "datetime": "DATETIME",
            "date": "DATE",
            "bool": "BOOL",
            "float": "FLOAT64",
            "Decimal": "FLOAT64",
        }

        python_type = type(variable).__name__
        param_type = TYPES.get(python_type, None)
        if param_type is None:
            raise exceptions.ValidationError(f"Parameter with type {param_type} not supported")
        return param_type

    @classmethod
    def _get_value(cls, variable: Any) -> Any:
        TYPES = {
            "Decimal": float,
        }
        python_type = type(variable).__name__
        param_type = TYPES.get(python_type, None)
        if param_type is not None:
            return param_type(variable)
        return variable

    @classmethod
    def parse(cls, key: str, value: Any) -> bigquery.ArrayQueryParameter | bigquery.ScalarQueryParameter:
        if isinstance(value, list):
            param_type = cls._get_type(variable=value[0])
            param_class = bigquery.ArrayQueryParameter
        else:
            param_type = cls._get_type(variable=value)
            param_class = bigquery.ScalarQueryParameter
        return param_class(key, param_type, cls._get_value(value))


__all__ = ("BigQuery",)
