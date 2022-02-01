import json
import unittest

from gcp_pilot.pubsub import CloudPublisher, CloudSubscriber, Message
from tests import ClientTestMixin


class TestCloudPublisher(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = CloudPublisher


class TestCloudSubscriber(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = CloudSubscriber


class TestPubSubMessage(unittest.TestCase):
    def _sample_message(self):
        return {
            "message": {
                "attributes": {"key": "value"},
                "data": "SGVsbG8gQ2xvdWQgUHViL1N1YiEgSGVyZSBpcyBteSBtZXNzYWdlIQ==",
                "messageId": "136969346945",
            },
            "subscription": "projects/myproject/subscriptions/mysubscription",
        }

    def assertSampleMessage(self, message):
        self.assertEqual("136969346945", message.id)
        self.assertEqual("Hello Cloud Pub/Sub! Here is my message!", message.data)
        self.assertEqual({"key": "value"}, message.attributes)
        self.assertEqual("projects/myproject/subscriptions/mysubscription", message.subscription)

    def test_load_from_dict(self):
        body = self._sample_message()
        message = Message.load(body=body, parser=str)
        self.assertSampleMessage(message=message)

    def test_load_from_str(self):
        body = json.dumps(self._sample_message())
        message = Message.load(body=body, parser=str)
        self.assertSampleMessage(message=message)

    def test_load_from_bytes(self):
        body = json.dumps(self._sample_message()).encode()
        message = Message.load(body=body, parser=str)
        self.assertSampleMessage(message=message)
