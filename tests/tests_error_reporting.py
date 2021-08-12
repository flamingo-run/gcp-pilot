import unittest

from gcp_pilot.error_reporting import CloudErrorReporting
from tests import ClientTestMixin


class TestCloudErrorReporting(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = CloudErrorReporting

    def get_client(self, **kwargs):
        return super().get_client(service_name="hogwarts-api")
