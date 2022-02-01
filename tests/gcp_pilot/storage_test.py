import unittest

from gcp_pilot.storage import CloudStorage
from tests import ClientTestMixin


class TestCloudStorage(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = CloudStorage
