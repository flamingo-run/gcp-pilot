# More Information: https://googleapis.dev/python/storage/latest/index.html
import io
from collections.abc import Generator
from datetime import timedelta
from pathlib import Path

import requests
from google.cloud import storage
from google.cloud.exceptions import Conflict
from google.cloud.storage import Blob, Bucket

from gcp_pilot import exceptions
from gcp_pilot.base import GoogleCloudPilotAPI


class CloudStorage(GoogleCloudPilotAPI):
    _client_class = storage.Client

    def create_bucket(
        self,
        name: str,
        region: str | None = None,
        project_id: str | None = None,
        exists_ok: bool = True,
    ) -> Bucket:
        bucket = self.client.bucket(name)
        try:
            return self.client.create_bucket(
                bucket_or_name=bucket,
                location=region,
                project=project_id or self.project_id,
            )
        except Conflict:
            if not exists_ok:
                raise
            return self.check_bucket(name=name)

    def check_bucket(self, name: str) -> Bucket:
        return self.client.get_bucket(bucket_or_name=name)

    def upload(
        self,
        source_file,
        bucket_name: str,
        target_file_name: str | None = None,
        chunk_size: int | None = None,
        is_public: bool = False,
        content_type: str | None = None,
    ) -> Blob:
        target_bucket = self.check_bucket(name=bucket_name)

        target_file_name = target_file_name or str(source_file).rsplit("/", maxsplit=1)[-1]
        blob = target_bucket.blob(target_file_name, chunk_size=chunk_size)

        if isinstance(source_file, str):
            if source_file.startswith("http"):
                file_obj = self._download(url=source_file)
                blob.upload_from_file(file_obj, content_type=content_type)
            elif Path(source_file).exists():
                blob.upload_from_filename(source_file, content_type=content_type)
            else:
                content = io.StringIO(source_file)
                blob.upload_from_file(content, content_type=content_type)
        elif isinstance(source_file, bytes):
            blob.upload_from_string(data=source_file, content_type=content_type)
        else:
            blob.upload_from_file(file_obj=source_file, content_type=content_type)

        if is_public:
            blob.make_public()

        return blob

    def copy(
        self,
        source_file_name,
        source_bucket_name: str,
        target_bucket_name: str,
        target_file_name: str | None = None,
        project_id: str | None = None,
        region: str | None = None,
    ) -> Blob:
        source_bucket = self.check_bucket(name=source_bucket_name)
        source_blob = source_bucket.blob(source_file_name)

        target_bucket = self.create_bucket(name=target_bucket_name, region=region, project_id=project_id)
        target_file_name = target_file_name or str(source_file_name).rsplit("/", maxsplit=1)[-1]

        obj = source_bucket.copy_blob(source_blob, target_bucket, target_file_name)
        return obj

    def move(
        self,
        source_file_name: str,
        source_bucket_name: str,
        target_bucket_name: str,
        target_file_name: str | None = None,
        project_id: str | None = None,
        region: str | None = None,
    ) -> Blob:
        data = self.copy(
            source_file_name=source_file_name,
            source_bucket_name=source_bucket_name,
            target_file_name=target_file_name,
            target_bucket_name=target_bucket_name,
            project_id=project_id,
            region=region,
        )
        self.delete(file_name=source_file_name, bucket_name=source_bucket_name)
        return data

    def delete(self, file_name: str, bucket_name: str | None = None) -> None:
        bucket = self.check_bucket(name=bucket_name)
        blob = bucket.blob(file_name)
        return blob.delete()

    def list_files(self, bucket_name: str, prefix: str | None = None) -> Generator[Blob, None, None]:
        blobs = self.client.list_blobs(
            bucket_name,
            prefix=prefix,
        )
        yield from blobs

    def get_file(self, uri: str) -> Blob:
        if not uri.startswith("gs://"):
            raise exceptions.ValidationError("GCS file must start with gs://")

        bucket_name, file_path = uri.removeprefix("gs://").split("/", 1)
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(file_path)

        return blob

    def _download(self, url: str) -> io.BytesIO:
        response = requests.get(url, stream=True, timeout=15)
        file = io.BytesIO()
        file.write(response.content)
        file.seek(0)
        return file

    def get_uri(self, blob: Blob) -> str:
        return f"gs://{blob.bucket.name}/{blob.name}"

    def get_download_url(
        self,
        bucket_name: str,
        blob_name: str,
        expiration: timedelta = timedelta(minutes=5),
        version: str = "v4",
    ):
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        return blob.generate_signed_url(
            version=version,
            expiration=expiration,
            method="GET",
            service_account_email=self.service_account_email,
            access_token=self.token,
        )


__all__ = ("CloudStorage",)
