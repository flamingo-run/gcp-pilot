import unittest

from gcp_pilot.identity_platform import IdentityPlatform
from tests import ClientTestMixin


class TestIdentityPlatform(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = IdentityPlatform
