import unittest

from gcp_pilot.monitoring import Monitoring
from tests import ClientTestMixin


class TestMonitoring(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = Monitoring
