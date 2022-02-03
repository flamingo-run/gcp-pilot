import unittest

from gcp_pilot.healthcare import HealthcareFHIR
from tests import ClientTestMixin


class TestHealthcareFHIR(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = HealthcareFHIR
