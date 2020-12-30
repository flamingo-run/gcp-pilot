import uuid
from datetime import datetime, timedelta

from google.api_core.exceptions import FailedPrecondition
from google.cloud import tasks_v2
from google.protobuf import timestamp_pb2

from gcp_pilot.base import GoogleCloudPilotAPI


class CloudTasks(GoogleCloudPilotAPI):
    _client_class = tasks_v2.CloudTasksClient
    DEFAULT_METHOD = tasks_v2.HttpMethod.POST

    def _parent_path(self, project_id: str = None, location: str = None) -> str:
        return f'projects/{project_id or self.project_id}/locations/{location or self.location}'

    def _queue_path(self, queue: str, project_id: str = None, location: str = None) -> str:
        return self.client.queue_path(
            project=project_id or self.project_id,
            location=location or self.location,
            queue=queue,
        )

    def _task_path(self, task: str, queue: str, project_id: str = None, location: str = None) -> str:
        return self.client.task_path(
            project=project_id or self.project_id,
            location=location or self.location,
            queue=queue,
            task=task,
        )

    async def push(
            self,
            task_name: str,
            queue_name: str,
            url: str,
            payload: str,
            method: int = DEFAULT_METHOD,
            delay_in_seconds: int = 0,
            project_id: str = None,
            location: str = None,
            unique: bool = True,
            use_oidc_auth: bool = True,
    ) -> tasks_v2.Task:
        queue_path = self.client.queue_path(
            project=project_id or self.project_id,
            location=location or self.location,
            queue=queue_name,
        )
        if unique:
            task_name = f"{task_name}-{str(uuid.uuid4())}"

        task_path = self.client.task_path(
            project=project_id or self.project_id,
            location=location or self.location,
            queue=queue_name,
            task=task_name,
        )
        task = tasks_v2.Task(
            name=task_path,
            http_request=tasks_v2.HttpRequest(
                http_method=method,
                url=url,
                body=payload.encode(),
                **(self.oidc_token if use_oidc_auth else {}),
            )
        )

        if delay_in_seconds:
            target_date = datetime.utcnow() + timedelta(seconds=delay_in_seconds)
            timestamp = timestamp_pb2.Timestamp()
            timestamp.FromDatetime(target_date)

            task.schedule_time = timestamp

        try:
            response = self.client.create_task(parent=queue_path, task=task)
        except FailedPrecondition as e:
            if e.message != 'Queue does not exist.':
                raise

            self._create_queue(queue_name=queue_name, location=location, project_id=project_id)
            response = self.client.create_task(parent=queue_path, task=task)
        return response

    def _create_queue(
            self,
            queue_name: str,
            project_id: str = None,
            location: str = None,
    ) -> tasks_v2.Queue:
        parent = self._parent_path(project_id=project_id, location=location)
        queue_path = self._queue_path(queue=queue_name, project_id=project_id, location=location)

        queue = tasks_v2.Queue(
            name=queue_path,
        )
        return self.client.create_queue(
            parent=parent,
            queue=queue,
        )
