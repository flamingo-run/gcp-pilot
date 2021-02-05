import unittest

from gcp_pilot.run import CloudRun
from tests import ClientTestMixin


class TestCloudRun(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = CloudRun
