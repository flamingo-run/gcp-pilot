from datetime import datetime
from typing import Any

from google.cloud import bigquery
from google.cloud.bigquery import Table, DatasetReference

from gcp_pilot import exceptions
from gcp_pilot.base import GoogleCloudPilotAPI


class BigQuery(GoogleCloudPilotAPI):
    _client_class = bigquery.Client

    def _dataset_ref(self, dataset_name: str, project_id: str = None) -> DatasetReference:
        return self.client.dataset(
            dataset_id=dataset_name,
            project=project_id or self.project_id,
        )

    def _to_sql_format(self, value: Any) -> Any:
        if isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, datetime):
            return f"'{self.date_to_str(value)}'"
        return value

    def _get_type(self, variable):
        TYPES = {
            'int': 'INT64',
            'str': 'STRING',
            'datetime': 'DATETIME',
            'date': 'DATE',
            'bool': 'BOOL',
            'float': 'FLOAT64',
            'Decimal': 'FLOAT64',
        }

        python_type = type(variable).__name__
        param_type = TYPES.get(python_type, None)
        if param_type is None:
            raise Exception('Parameter with type {param_type} not supported')
        return param_type

    def _get_value(self, variable):
        TYPES = {
            'Decimal': float,
        }
        python_type = type(variable).__name__
        param_type = TYPES.get(python_type, None)
        if param_type is not None:
            return param_type(variable)
        return variable

    def _create_param(self, key, value):
        if isinstance(value, list):
            param_type = self._get_type(variable=value[0])
            param_class = bigquery.ArrayQueryParameter
        else:
            param_type = self._get_type(variable=value)
            param_class = bigquery.ScalarQueryParameter
        return param_class(key, param_type, self._get_value(value))

    def execute(
            self,
            sql,
            params=None,
            legacy_sql=False,
            job_id=None,
            destination_table_name=None,
            destination_dataset_name=None,
            destination_project=None,
            write_disposition=None
    ):
        job_config = bigquery.QueryJobConfig()
        if destination_table_name or destination_dataset_name:
            if not destination_table_name and destination_dataset_name:
                raise exceptions.ValidationError(
                    f"Both destination_dataset_name and destination_table_name must be provided."
                )
            destination_project = destination_project or self.project_id
            destination_dataset = destination_dataset_name
            destination = f'{destination_project}.{destination_dataset}.{destination_table_name}'
            job_config.destination = destination
            job_config.write_disposition = write_disposition or 'WRITE_EMPTY'

        if params:
            query_params = [
                self._create_param(key, value) for key, value in params.items()
            ]
            job_config.query_parameters = query_params
        job_config.use_legacy_sql = legacy_sql

        query_job = self.client.query(sql, job_id=job_id, job_config=job_config)
        return self._wait_for_job(job=query_job)

    def insert_rows(self, dataset_name: str, table_name: str, rows, project_id: str = None):
        table = self.get_table(
            table_name=table_name,
            project_id=project_id,
            dataset_name=dataset_name,
        )
        errors = self.client.insert_rows(table=table, rows=rows)
        if errors:
            raise Exception(f'Bigquery insert error: {errors}')

    def get_table(self, table_name, project_id=None, dataset_name=None) -> Table:
        dataset_ref = self._dataset_ref(project_id=project_id, dataset_name=dataset_name)
        table_ref = dataset_ref.table(table_name)
        return self.client.get_table(table_ref)

    def load(
            self,
            table_name,
            gcs_file,
            project_id=None,
            dataset_name=None,
            schema=None,
            sync=False,
            truncate=None,
    ):
        job_config = bigquery.LoadJobConfig()
        if schema:
            job_config.schema = schema
        else:
            job_config.autodetect = True
            job_config._properties['load']['schemaUpdateOptions'] = ['ALLOW_FIELD_ADDITION']

        extension = gcs_file.split('.')[-1]
        if extension == 'json':
            source_format = bigquery.job.SourceFormat.NEWLINE_DELIMITED_JSON
        elif extension == 'csv':
            source_format = bigquery.job.SourceFormat.CSV
        else:
            message = 'Unsupported BigQuery Source format {}'.format(extension)
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
        load_job = self.client.load_table_from_uri(
            source_uris=gcs_file,
            destination=target_ref,
            job_config=job_config,
        )

        if sync:
            self._wait_for_job(job=load_job)

    def copy(
            self,
            source_table_name,
            destination_table_name,
            destination_dataset_name,
            destination_project=None,
            sync=False,
            **kwargs,
    ):
        source_ref = self.get_table(table_name=source_table_name)
        dataset_ref = self._dataset_ref(
            project_id=destination_project or self.project_id,
            dataset_name=destination_dataset_name,
        )
        target_ref = dataset_ref.table(destination_table_name)

        job = self.client.copy_table(source_ref, target_ref, **kwargs)
        if sync:
            self._wait_for_job(job=job)

    @classmethod
    def date_to_str(cls, dt, table_suffix=False):
        if table_suffix:
            mask = '%Y%m%d'
        elif isinstance(dt, datetime):
            mask = '%Y-%m-%d %H:%M:%S'
        else:
            mask = '%Y-%m-%d'
        return dt.strftime(mask)

    def _wait_for_job(self, job):
        try:
            return job.result()
        except Exception as e:
            raise exceptions.BigQueryJobError(job) from e
