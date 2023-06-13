# https://googleapis.dev/python/pubsub/latest/index.html
import base64
import json
import logging
from collections.abc import Callable, Generator
from dataclasses import dataclass
from typing import Any

from google.api_core.exceptions import AlreadyExists, NotFound
from google.cloud import pubsub_v1
from google.protobuf.duration_pb2 import Duration
from google.protobuf.field_mask_pb2 import FieldMask
from google.pubsub_v1 import DeadLetterPolicy, ExpirationPolicy, PushConfig, RetryPolicy, Subscription, Topic, types

from gcp_pilot.base import GoogleCloudPilotAPI
from gcp_pilot.exceptions import ValidationError

logger = logging.getLogger()


class CloudPublisher(GoogleCloudPilotAPI):
    _client_class = pubsub_v1.PublisherClient
    _service_name = "Cloud Pub/Sub"
    _google_managed_service = True

    def __init__(self, enable_message_ordering: bool = False, **kwargs):
        if publisher_options := kwargs.pop("publisher_options", None):
            publisher_options.enable_message_ordering = enable_message_ordering
        else:
            publisher_options = pubsub_v1.types.PublisherOptions(
                enable_message_ordering=enable_message_ordering,
            )
        super().__init__(publisher_options=publisher_options, **kwargs)

    def create_topic(
        self,
        topic_id: str,
        project_id: str | None = None,
        exists_ok: bool = True,
        labels: dict[str, str] | None = None,
    ) -> types.Topic:
        topic_path = self.client.topic_path(
            project=project_id or self.project_id,
            topic=topic_id,
        )
        topic_obj = types.Topic(
            name=topic_path,
            labels=labels,
        )
        try:
            topic = self.client.create_topic(
                request=topic_obj,
            )
        except AlreadyExists:
            if not exists_ok:
                raise
            topic = self.get_topic(topic_id=topic_id, project_id=project_id)
        return topic

    def update_topic(
        self,
        topic_id: str,
        project_id: str | None = None,
        labels: dict[str, str] | None = None,
    ) -> types.Topic:
        topic_path = self.client.topic_path(
            project=project_id or self.project_id,
            topic=topic_id,
        )
        topic_obj = types.Topic(
            name=topic_path,
            labels=labels,
        )
        return self.client.update_topic(
            request=types.UpdateTopicRequest(
                topic=topic_obj,
                update_mask=FieldMask(paths=["labels"]),
            ),
        )

    def get_topic(self, topic_id: str, project_id: str | None = None):
        topic_path = self.client.topic_path(
            project=project_id or self.project_id,
            topic=topic_id,
        )
        return self.client.get_topic(
            topic=topic_path,
        )

    def list_topics(
        self,
        prefix: str = "",
        suffix: str = "",
        project_id: str | None = None,
    ) -> Generator[Topic, None, None]:
        project_path = self._project_path(project_id=project_id)
        topics = self.client.list_topics(
            project=project_path,
        )
        for topic in topics:
            name = topic.name.split("/topics/")[-1]
            if name.startswith(prefix) and name.endswith(suffix):
                yield topic

    def publish(
        self,
        message: str,
        topic_id: str,
        project_id: str | None = None,
        attributes: dict[str, Any] | None = None,
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
            self.create_topic(
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
    _service_name = "Cloud Pub/Sub"
    _google_managed_service = True

    def list_subscriptions(
        self,
        prefix: str = "",
        suffix: str = "",
        project_id: str | None = None,
    ) -> Generator[Subscription, None, None]:
        all_subscriptions = self.client.list_subscriptions(
            project=f"projects/{project_id or self.project_id}",
        )
        for subscription in all_subscriptions:
            name = subscription.name.split("/subscriptions/")[-1]
            if name.startswith(prefix) and name.endswith(suffix):
                yield subscription

    def get_subscription(self, subscription_id: str, project_id: str | None = None) -> Subscription:
        subscription_path = self.client.subscription_path(
            project=project_id or self.project_id,
            subscription=subscription_id,
        )

        return self.client.get_subscription(
            subscription=subscription_path,
        )

    def delete_subscription(self, subscription_id: str, project_id: str | None = None) -> None:
        subscription_path = self.client.subscription_path(
            project=project_id or self.project_id,
            subscription=subscription_id,
        )

        return self.client.delete_subscription(
            subscription=subscription_path,
        )

    def create_subscription(
        self,
        topic_id: str,
        subscription_id: str,
        project_id: str | None = None,
        exists_ok: bool = True,
        auto_create_topic: bool = True,
        enable_message_ordering: bool = False,
        push_to_url: str | None = None,
        use_oidc_auth: bool = False,
        dead_letter_topic_id: str | None = None,
        dead_letter_subscription_id: str | None = None,
        max_retries: int | None = None,
        min_backoff: int | None = 10,
        max_backoff: int | None = 600,
        expiration_ttl: int | None = 31,
        enable_exactly_once_delivery: bool = False,
        message_filter: str | None = None,
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
                **(self.get_oidc_token(audience=push_to_url) if use_oidc_auth else {}),
            )

        if max_retries and not dead_letter_topic_id:
            raise ValidationError("max_retries requires dead_letter_topic_id")

        extra_config = {}

        if dead_letter_topic_id:
            dead_letter_policy = DeadLetterPolicy(
                dead_letter_topic=self.client.topic_path(
                    project=project_id or self.project_id,
                    topic=dead_letter_topic_id,
                ),
                max_delivery_attempts=max_retries,
            )
            extra_config["dead_letter_policy"] = dead_letter_policy

        expiration_policy = (
            ExpirationPolicy(ttl=Duration(seconds=expiration_ttl * 24 * 60 * 60))
            if expiration_ttl
            else ExpirationPolicy()
        )
        extra_config["expiration_policy"] = expiration_policy

        if min_backoff is not None or max_backoff is not None:
            retry_policy = RetryPolicy(
                minimum_backoff=Duration(seconds=min_backoff or 10),
                maximum_backoff=Duration(seconds=max_backoff or 600),
            )
            extra_config["retry_policy"] = retry_policy

        if message_filter:
            extra_config["filter"] = message_filter

        subscription = Subscription(
            name=subscription_path,
            topic=topic_path,
            push_config=push_config,
            enable_message_ordering=enable_message_ordering,
            enable_exactly_once_delivery=enable_exactly_once_delivery,
            **extra_config,
        )

        try:
            return self.client.create_subscription(request=subscription)
        except NotFound:
            if not auto_create_topic:
                raise

            CloudPublisher().create_topic(
                topic_id=topic_id,
                project_id=project_id,
            )
            if dead_letter_topic_id:
                logger.info(
                    f"Creating dead-letter topic {dead_letter_topic_id} & subscription {dead_letter_subscription_id}",
                )
                self.create_or_update_subscription(
                    topic_id=dead_letter_topic_id,
                    subscription_id=dead_letter_subscription_id,
                    expiration_ttl=None,  # dead letters should never expire
                )

            return self.client.create_subscription(request=subscription)
        except AlreadyExists:
            if not exists_ok:
                raise
            return self.get_subscription(subscription_id=subscription_id, project_id=project_id)

    def patch_subscription(
        self,
        topic_id: str,
        subscription_id: str,
        project_id: str | None = None,
        push_to_url: str | None = None,
        use_oidc_auth: bool = False,
        dead_letter_topic_id: str | None = None,
        dead_letter_subscription_id: str | None = None,
        max_retries: int | None = None,
        min_backoff: int | None = 10,
        max_backoff: int | None = 600,
        expiration_ttl: int | None = 31,
    ) -> Subscription:
        topic_path = self.client.topic_path(
            project=project_id or self.project_id,
            topic=topic_id,
        )
        subscription_path = self.client.subscription_path(
            project=project_id or self.project_id,
            subscription=subscription_id,
        )

        update_paths = []

        push_config = None
        if push_to_url:
            push_config = PushConfig(
                push_endpoint=push_to_url,
                **(self.get_oidc_token(audience=push_to_url) if use_oidc_auth else {}),
            )
            update_paths.append("push_config")

        if max_retries and not dead_letter_topic_id:
            raise ValidationError("max_retries requires dead_letter_topic_id")

        extra_config = {}

        if dead_letter_topic_id:
            dead_letter_policy = DeadLetterPolicy(
                dead_letter_topic=self.client.topic_path(
                    project=project_id or self.project_id,
                    topic=dead_letter_topic_id,
                ),
                max_delivery_attempts=max_retries or 100,
            )
            extra_config["dead_letter_policy"] = dead_letter_policy
            update_paths.append("dead_letter_policy")

        expiration_policy = (
            ExpirationPolicy(ttl=Duration(seconds=expiration_ttl * 24 * 60 * 60))
            if expiration_ttl
            else ExpirationPolicy()
        )

        extra_config["expiration_policy"] = expiration_policy
        update_paths.append("expiration_policy")

        retry_policy = RetryPolicy(
            minimum_backoff=Duration(seconds=min_backoff),
            maximum_backoff=Duration(seconds=max_backoff),
        )
        extra_config["retry_policy"] = retry_policy
        update_paths.append("retry_policy")

        subscription = Subscription(name=subscription_path, topic=topic_path, push_config=push_config, **extra_config)

        update_mask = FieldMask(paths=update_paths)

        try:
            return self.client.update_subscription(request={"subscription": subscription, "update_mask": update_mask})
        except NotFound:
            logger.info(
                f"Creating dead-letter topic {dead_letter_topic_id} & subscription {dead_letter_subscription_id}",
            )
            self.create_or_update_subscription(
                topic_id=dead_letter_topic_id,
                subscription_id=dead_letter_subscription_id,
            )

            return self.client.update_subscription(request={"subscription": subscription, "update_mask": update_mask})

    def update_subscription(
        self,
        topic_id: str,
        subscription_id: str,
        project_id: str | None = None,
        push_to_url: str | None = None,
        use_oidc_auth: bool = False,
        dead_letter_topic_id: str | None = None,
        dead_letter_subscription_id: str | None = None,
        max_retries: int | None = None,
        min_backoff: int | None = 10,
        max_backoff: int | None = 600,
        expiration_ttl: int | None = 31,
        message_filter: str | None = None,
    ) -> Subscription:
        kwargs = {
            "topic_id": topic_id,
            "subscription_id": subscription_id,
            "project_id": project_id,
            "push_to_url": push_to_url,
            "use_oidc_auth": use_oidc_auth,
            "dead_letter_topic_id": dead_letter_topic_id,
            "dead_letter_subscription_id": dead_letter_subscription_id,
            "max_retries": max_retries,
            "min_backoff": min_backoff,
            "max_backoff": max_backoff,
            "expiration_ttl": expiration_ttl,
        }
        if message_filter:
            # Subscription filters cannot be updated, so we need to delete and recreate the subscription (if needed)
            subscription = self.get_subscription(subscription_id=subscription_id, project_id=project_id)
            if subscription.filter != message_filter:
                self.delete_subscription(subscription_id=subscription_id, project_id=project_id)
                return self.create_subscription(message_filter=message_filter, **kwargs)
        self.patch_subscription(**kwargs)

    def create_or_update_subscription(
        self,
        topic_id: str,
        subscription_id: str,
        project_id: str | None = None,
        auto_create_topic: bool = True,
        enable_message_ordering: bool = False,
        push_to_url: str | None = None,
        use_oidc_auth: bool = False,
        dead_letter_topic_id: str | None = None,
        dead_letter_subscription_id: str | None = None,
        max_retries: int | None = None,
        min_backoff: int | None = 10,
        max_backoff: int | None = 600,
        expiration_ttl: int | None = 31,
        message_filter: str | None = None,
    ) -> Subscription:
        if not subscription_id:
            raise ValidationError("subscription_id is mandatory to create or update a Subscription")
        try:
            return self.create_subscription(
                topic_id=topic_id,
                subscription_id=subscription_id,
                project_id=project_id,
                exists_ok=False,
                auto_create_topic=auto_create_topic,
                enable_message_ordering=enable_message_ordering,
                push_to_url=push_to_url,
                use_oidc_auth=use_oidc_auth,
                dead_letter_topic_id=dead_letter_topic_id,
                dead_letter_subscription_id=dead_letter_subscription_id,
                max_retries=max_retries,
                min_backoff=min_backoff,
                max_backoff=max_backoff,
                expiration_ttl=expiration_ttl,
                message_filter=message_filter,
            )
        except AlreadyExists:
            return self.update_subscription(
                topic_id=topic_id,
                subscription_id=subscription_id,
                project_id=project_id,
                push_to_url=push_to_url,
                use_oidc_auth=use_oidc_auth,
                dead_letter_topic_id=dead_letter_topic_id,
                dead_letter_subscription_id=dead_letter_subscription_id,
                max_retries=max_retries,
                min_backoff=min_backoff,
                max_backoff=max_backoff,
                expiration_ttl=expiration_ttl,
                message_filter=message_filter,
            )

    def subscribe(self, topic_id: str, subscription_id: str, callback: Callable, project_id: str | None = None):
        self.create_subscription(
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


@dataclass
class Message:
    id: str
    data: Any
    attributes: dict[str, Any]
    subscription: str

    @classmethod
    def load(cls, body: str | bytes | dict, parser: Callable = json.loads) -> "Message":
        # https://cloud.google.com/pubsub/docs/push#receiving_messages
        if isinstance(body, bytes):
            body = body.decode()
        if isinstance(body, str):
            body = json.loads(body)

        return Message(
            id=body["message"]["messageId"],
            attributes=body["message"]["attributes"],
            subscription=body["subscription"],
            data=parser(base64.b64decode(body["message"]["data"]).decode("utf-8")),
        )

    def dump(self, parser: Callable = json.dumps) -> str:
        body = {
            "message": {
                "messageId": self.id,
                "attributes": self.attributes,
                "data": base64.b64encode(parser(self.data).encode("utf-8")).decode(),
            },
            "subscription": self.subscription,
        }
        return json.dumps(body)


__all__ = (
    "CloudPublisher",
    "CloudSubscriber",
    "Message",
)
