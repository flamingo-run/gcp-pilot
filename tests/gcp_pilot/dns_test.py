import unittest

from gcp_pilot.dns import CloudDNS
from tests import ClientTestMixin


class TestCloudDNS(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = CloudDNS
