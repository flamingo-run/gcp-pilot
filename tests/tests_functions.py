import unittest

from gcp_pilot.functions import CloudFunctions
from tests import ClientTestMixin


class TestCloudFunctions(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = CloudFunctions
