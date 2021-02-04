# More Information: https://googleapis.dev/python/storage/latest/index.html
import io
import os
from typing import AsyncIterator

import requests
from google.cloud import storage
from google.cloud.exceptions import Conflict
from google.cloud.storage import Bucket, Blob

from gcp_pilot.base import GoogleCloudPilotAPI


class CloudStorage(GoogleCloudPilotAPI):
    _client_class = storage.Client

    async def create_bucket(self, name: str, region: str, project_id: str = None, exists_ok: bool = True) -> Bucket:
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
            return await self.check_bucket(name=name)

    async def check_bucket(self, name: str) -> Bucket:
        return self.client.get_bucket(bucket_or_name=name)

    async def upload(
            self,
            source_file,
            bucket_name: str,
            target_file_name: str = None,
            chunk_size: int = None,
            project_id: str = None,
            region: str = None,
            is_public: bool = False,
    ) -> Blob:
        target_bucket = await self.create_bucket(name=bucket_name, project_id=project_id, region=region)

        target_file_name = target_file_name or str(source_file).rsplit('/')[-1]
        blob = target_bucket.blob(target_file_name, chunk_size=chunk_size)

        if isinstance(source_file, str):
            if source_file.startswith('http'):
                file_obj = self._download(url=source_file)
                blob.upload_from_file(file_obj)
            elif os.path.exists(source_file):
                blob.upload_from_filename(source_file)
            else:
                content = io.StringIO(source_file)
                blob.upload_from_file(content)
        else:
            blob.upload_from_file(source_file)

        if is_public:
            blob.make_public()

        return blob

    async def copy(
            self,
            source_file_name,
            source_bucket_name: str,
            target_bucket_name: str,
            target_file_name: str = None,
            project_id: str = None,
            region: str = None,
    ) -> Blob:
        source_bucket = await self.create_bucket(name=source_bucket_name, region=region, project_id=project_id)
        source_blob = source_bucket.blob(source_file_name)

        target_bucket = await self.create_bucket(name=target_bucket_name, region=region, project_id=project_id)
        target_file_name = target_file_name or str(source_file_name).rsplit('/')[-1]

        obj = source_bucket.copy_blob(source_blob, target_bucket, target_file_name)
        return obj

    async def move(
            self,
            source_file_name: str,
            source_bucket_name: str,
            target_bucket_name: str,
            target_file_name: str = None,
            project_id: str = None,
            region: str = None,
    ) -> Blob:
        data = await self.copy(
            source_file_name=source_file_name,
            source_bucket_name=source_bucket_name,
            target_file_name=target_file_name,
            target_bucket_name=target_bucket_name,
            project_id=project_id,
            region=region,
        )
        await self.delete(file_name=source_file_name, bucket_name=source_bucket_name)
        return data

    async def delete(self, file_name: str, bucket_name: str = None) -> None:
        bucket = await self.check_bucket(name=bucket_name)
        blob = bucket.blob(file_name)
        return blob.delete()

    async def list_files(self, bucket_name: str, prefix: str = None) -> AsyncIterator[Blob]:
        blobs = self.client.list_blobs(
            bucket_name,
            prefix=prefix,
        )
        for blob in blobs:
            yield blob

    def _download(self, url: str) -> io.BytesIO:
        response = requests.get(url, stream=True)
        f = io.BytesIO()
        f.write(response.content)
        f.seek(0)
        return f

    def get_uri(self, blob: Blob) -> str:
        return f'gs://{blob.bucket.name}/{blob.name}'


__all__ = (
    'CloudStorage',
)
