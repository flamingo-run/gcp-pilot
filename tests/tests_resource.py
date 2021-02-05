import unittest

from gcp_pilot.resource import ResourceManager  # pylint: disable=unused-import
from tests import ClientTestMixin


class TestResourceManager(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = ResourceManager
