# More Information: https://googleapis.dev/python/storage/latest/index.html
from google.cloud import storage
from google.cloud.exceptions import Conflict

from gcp_pilot.base import GoogleCloudPilotAPI


class GoogleCloudStorage(GoogleCloudPilotAPI):
    _client_class = storage.Client

    async def create_bucket(self, name: str, region: str, project_id: str = None, exists_ok: bool = True):
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

    async def check_bucket(self, name):
        return self.client.get_bucket(bucket_or_name=name)

    async def upload(
            self,
            bucket_name: str,
            source_file_name: str,
            destination_blob_name: str,
            is_public: bool = False,
    ):
        bucket = self.client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)
        blob.upload_from_filename(source_file_name)
        if is_public:
            blob.make_public()
