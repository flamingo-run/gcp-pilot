import unittest

from gcp_pilot.directory import Directory
from tests import ClientTestMixin


class TestDirectory(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = Directory

    def get_client(self, **kwargs):
        return super().get_client(email='chuck@norris.com')
