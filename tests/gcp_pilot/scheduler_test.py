import unittest

from gcp_pilot.scheduler import CloudScheduler
from tests import ClientTestMixin


class TestCloudScheduler(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = CloudScheduler
