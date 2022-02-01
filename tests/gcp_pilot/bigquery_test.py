import unittest

from gcp_pilot.big_query import BigQuery
from tests import ClientTestMixin


class TestBigQuery(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = BigQuery
