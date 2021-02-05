import unittest

from gcp_pilot.build import CloudBuild
from tests import ClientTestMixin


class TestCloudBuild(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = CloudBuild
