# More Information: https://cloud.google.com/sql/docs/mysql/apis#rest-api
import json
import logging
import time
from collections.abc import Generator
from typing import Any

from googleapiclient.errors import HttpError

from gcp_pilot import exceptions
from gcp_pilot.base import DiscoveryMixin, GoogleCloudPilotAPI

InstanceType = DatabaseType = UserType = dict[str, Any]


logger = logging.getLogger("gcp-pilot")


class CloudSQL(DiscoveryMixin, GoogleCloudPilotAPI):
    _iam_roles = ["cloudsql.client"]

    def __init__(self, **kwargs):
        super().__init__(
            serviceName="sqladmin",
            version="v1beta4",
            cache_discovery=False,
            **kwargs,
        )

    def list_instances(self, project_id: str | None = None) -> Generator[InstanceType, None, None]:
        params = dict(project=project_id or self.project_id)
        instances = self._paginate(
            method=self.client.instances().list,
            result_key="items",
            params=params,
        )
        yield from instances

    def get_instance(self, name: str, project_id: str | None = None) -> InstanceType:
        return self._execute(
            method=self.client.instances().get,
            instance=name,
            project=project_id or self.project_id,
        )

    def create_instance(
        self,
        name: str,
        version: str,
        tier: str,
        region: str,
        ha: bool = False,
        project_id: str | None = None,
        exists_ok: bool = True,
        wait_ready: bool = True,
    ) -> InstanceType:
        body = dict(
            name=name,
            database_version=version,
            region=region,
            settings=dict(
                tier=tier,
                availability_type="ZONAL" if ha else "REGIONAL",
            ),
        )
        try:
            sql_instance = self._execute(
                method=self.client.instances().insert,
                project=project_id or self.project_id,
                body=body,
            )
            current_state = sql_instance["status"]
        except exceptions.AlreadyExists:
            if not exists_ok:
                raise

            try:
                sql_instance = self.get_instance(name=name, project_id=project_id)
                current_state = sql_instance["state"]
            except exceptions.NotFound as exc:
                raise exceptions.DeletedRecently(resource=f"Instance {name}") from exc

        if not wait_ready:
            return sql_instance

        while current_state != "RUNNABLE":
            logger.info(f"Instance {name} is still {current_state}. Waiting until RUNNABLE.")
            time.sleep(1)  # TODO: improve this: exp backoff
            sql_instance = self.get_instance(name=name, project_id=project_id)
            current_state = sql_instance["state"]
        logger.info(f"Instance {name} is {current_state}!")
        return sql_instance

    def get_database(self, instance: str, database: str, project_id: str | None = None) -> DatabaseType:
        project_id = project_id or self.project_id
        return self._execute(
            method=self.client.databases().get,
            instance=instance,
            database=database,
            project=project_id,
        )

    def create_database(
        self,
        name: str,
        instance: str,
        project_id: str | None = None,
        exists_ok: bool = True,
    ) -> DatabaseType:
        body = dict(
            name=name,
        )
        try:
            return (
                self.client.databases()
                .insert(
                    instance=instance,
                    project=project_id or self.project_id,
                    body=body,
                )
                .execute()
            )
        except HttpError as exc:
            # IDK. Weird bug that the error_details is empty if too fast
            error_details = json.loads(exc.content.decode())["error"]["message"]

            not_ready = exc.resp.status == 400 and "is not running" in error_details
            already_exists = exc.resp.status == 400 and "already exists" in error_details and exists_ok
            if not_ready or already_exists:
                return self.get_database(instance=instance, database=name, project_id=project_id)
            raise

    def list_users(self, instance: str, project_id: str | None = None) -> Generator[UserType, None, None]:
        params = dict(
            instance=instance,
            project=project_id or self.project_id,
        )
        users = self._paginate(
            method=self.client.users().list,
            params=params,
        )
        yield from users

    def create_user(self, name: str, password: str, instance: str, project_id: str | None = None) -> UserType:
        body = dict(
            name=name,
            password=password,
        )
        return self._execute(
            method=self.client.users().insert,
            instance=instance,
            project=project_id or self.project_id,
            body=body,
        )


__all__ = ("CloudSQL",)
