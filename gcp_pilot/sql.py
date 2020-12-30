import json
import time
from typing import Dict, Any, List

from google.api_core.exceptions import NotFound
from googleapiclient.errors import HttpError

from gcp_pilot.base import GoogleCloudPilotAPI

InstanceType = DatabaseType = UserType = Dict[str, Any]


class GoogleCloudSQL(GoogleCloudPilotAPI):
    _iam_roles = ['cloudsql.client']

    def __init__(self, **kwargs):
        super().__init__(
            serviceName='sqladmin',
            version='v1beta4',
            **kwargs,
        )

    async def list_instances(self, project_id: str = None) -> List[InstanceType]:
        return self.client.instances().list(
            project=project_id or self.project_id,
        ).execute()

    async def get_instance(self, name: str, project_id: str = None) -> InstanceType:
        return self.client.instances().get(
            instance=name,
            project=project_id or self.project_id,
        ).execute()

    async def create_instance(
            self,
            name: str,
            version: str,
            tier: str,
            region: str,
            ha: bool = False,
            project_id: str = None,
            exists_ok: bool = True,
            wait_ready: bool = True,
    ) -> InstanceType:
        body = dict(
            name=name,
            database_version=version,
            region=region,
            settings=dict(
                tier=tier,
                availability_type='ZONAL' if ha else 'REGIONAL',
            ),
        )
        try:
            sql_instance = self.client.instances().insert(
                project=project_id or self.project_id,
                body=body,
            ).execute()
            current_state = sql_instance['status']
        except HttpError as e:
            if e.resp.status == 409 and exists_ok:
                try:
                    sql_instance = await self.get_instance(name=name, project_id=project_id)
                    current_state = sql_instance['state']
                except HttpError as e:
                    if e.resp.status == 404:
                        message = f"Instance {name} was probably deleted recently. Cannot reuse name for 1 week."
                        raise NotFound(message=message) from e
                    raise e
            else:
                raise

        if not wait_ready:
            return sql_instance

        while current_state != 'RUNNABLE':
            print(f"Instance {name} is still {current_state}. Waiting until RUNNABLE.")
            time.sleep(1)  # TODO: improve this: exp backoff
            sql_instance = await self.get_instance(name=name, project_id=project_id)
            current_state = sql_instance['state']
        print(f"Instance {name} is {current_state}!")
        return sql_instance

    async def get_database(self, instance: str, database: str, project_id: str = None) -> DatabaseType:
        project_id = project_id or self.project_id
        return self.client.databases().get(
            instance=instance,
            database=database,
            project=project_id,
        ).execute()

    async def create_database(
            self,
            name: str,
            instance: str,
            project_id: str = None,
            exists_ok: bool = True,
    ) -> DatabaseType:
        body = dict(
            name=name,
        )
        try:
            return self.client.databases().insert(
                instance=instance,
                project=project_id or self.project_id,
                body=body,
            ).execute()
        except HttpError as e:
            # IDK. Weird bug that the error_details is empty if too fast
            error_details = json.loads(e.content.decode())['error']['message']

            not_ready = e.resp.status == 400 and 'is not running' in error_details
            already_exists = e.resp.status == 400 and 'already exists' in error_details and exists_ok
            if not_ready or already_exists:
                return await self.get_database(instance=instance, database=name, project_id=project_id)
            raise

    async def list_users(self, instance: str, project_id: str = None) -> List[UserType]:
        return self.client.users().list(
            instance=instance,
            project=project_id or self.project_id,
        ).execute()

    async def create_user(self, name: str, password: str, instance: str, project_id: str = None) -> UserType:
        body = dict(
            name=name,
            password=password,
        )
        return self.client.users().insert(
            instance=instance,
            project=project_id or self.project_id,
            body=body,
        ).execute()
