import unittest

from gcp_pilot.sql import CloudSQL
from tests import ClientTestMixin


class TestCloudSQL(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = CloudSQL
