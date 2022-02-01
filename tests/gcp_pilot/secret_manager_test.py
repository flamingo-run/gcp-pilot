import unittest

from gcp_pilot.secret_manager import SecretManager
from tests import ClientTestMixin


class TestSecretManager(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = SecretManager
