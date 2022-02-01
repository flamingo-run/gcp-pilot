import unittest

from gcp_pilot.tasks import CloudTasks
from tests import ClientTestMixin


class TestCloudTasks(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = CloudTasks
