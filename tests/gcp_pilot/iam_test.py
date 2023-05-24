import unittest

from gcp_pilot.iam import IdentityAccessManager
from tests import ClientTestMixin


class TestIAM(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = IdentityAccessManager
