# https://googleapis.dev/python/pubsub/latest/index.html
from typing import Callable, Dict, Any, AsyncIterator

from google.api_core.exceptions import AlreadyExists, NotFound
from google.cloud import pubsub_v1
from google.pubsub_v1 import PushConfig, Subscription, types

from gcp_pilot.base import GoogleCloudPilotAPI


class CloudPublisher(GoogleCloudPilotAPI):
    _client_class = pubsub_v1.PublisherClient

    async def create_topic(self, topic_id: str, project_id: str = None, exists_ok: bool = True) -> types.Topic:
        topic_path = self.client.topic_path(
            project=project_id or self.project_id,
            topic=topic_id,
        )
        try:
            topic = self.client.create_topic(request={"name": topic_path})
        except AlreadyExists:
            if not exists_ok:
                raise
            topic = await self.get_topic(topic_id=topic_id, project_id=project_id)
        return topic

    async def get_topic(self, topic_id: str, project_id: str = None):
        pass

    async def publish(
            self,
            message: str,
            topic_id: str,
            project_id: str = None,
            attributes: Dict[str, Any] = None,
    ) -> types.PublishResponse:
        topic_path = self.client.topic_path(
            project=project_id or self.project_id,
            topic=topic_id,
        )
        try:
            future = self.client.publish(
                topic=topic_path,
                data=message.encode(),
                **(attributes or {}),
            )
            return future.result()
        except NotFound:
            await self.create_topic(
                topic_id=topic_id,
                project_id=project_id,
            )
            future = self.client.publish(
                topic=topic_path,
                data=message.encode(),
                **(attributes or {}),
            )
            return future.result()


class CloudSubscriber(GoogleCloudPilotAPI):
    _client_class = pubsub_v1.SubscriberClient

    async def list_subscriptions(self, project_id: str = None) -> AsyncIterator[Subscription]:
        all_subscriptions = self.client.list_subscriptions(
            project=f'projects/{project_id or self.project_id}',
        )
        for subscription in all_subscriptions:
            yield subscription

    async def get_subscription(self, subscription_id: str, project_id: str = None) -> Subscription:
        subscription_path = self.client.subscription_path(
            project=project_id or self.project_id,
            subscription=subscription_id,
        )

        return self.client.get_subscription(
            subscription=subscription_path,
        )

    async def delete_subscription(self, subscription_id: str, project_id: str = None) -> None:
        subscription_path = self.client.subscription_path(
            project=project_id or self.project_id,
            subscription=subscription_id,
        )

        return self.client.delete_subscription(
            subscription=subscription_path,
        )

    async def create_subscription(
            self,
            topic_id: str,
            subscription_id: str,
            project_id: str = None,
            exists_ok: bool = True,
            auto_create_topic: bool = True,
            push_to_url: str = None,
            use_oidc_auth: bool = False,
    ) -> Subscription:
        topic_path = self.client.topic_path(
            project=project_id or self.project_id,
            topic=topic_id,
        )
        subscription_path = self.client.subscription_path(
            project=project_id or self.project_id,
            subscription=subscription_id,
        )

        push_config = None
        if push_to_url:
            push_config = PushConfig(
                push_endpoint=push_to_url,
                **(self.oidc_token if use_oidc_auth else {}),
            )

        try:
            return self.client.create_subscription(
                name=subscription_path,
                topic=topic_path,
                push_config=push_config,
            )
        except NotFound:
            if not auto_create_topic:
                raise
            await CloudPublisher().create_topic(
                topic_id=topic_id,
                project_id=project_id,
                exists_ok=False,
            )
            return self.client.create_subscription(
                name=subscription_path,
                topic=topic_path,
                push_config=push_config,
            )
        except AlreadyExists:
            if not exists_ok:
                raise
            return await self.get_subscription(subscription_id=subscription_id, project_id=project_id)

    async def subscribe(self, topic_id: str, subscription_id: str, callback: Callable, project_id: str = None):
        await self.create_subscription(
            topic_id=topic_id,
            subscription_id=subscription_id,
            project_id=project_id,
        )

        subscription_path = self.client.subscription_path(
            project=project_id or self.project_id,
            subscription=subscription_id,
        )
        future = self.client.subscribe(
            subscription=subscription_path,
            callback=callback,
        )
        future.result()
