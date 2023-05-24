import unittest

from gcp_pilot.resource import ResourceManager
from tests import ClientTestMixin


class TestResourceManager(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = ResourceManager
