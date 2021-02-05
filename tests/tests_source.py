import unittest

from gcp_pilot.source import SourceRepository
from tests import ClientTestMixin


class TestSourceRepository(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = SourceRepository
