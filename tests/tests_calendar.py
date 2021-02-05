import unittest

from gcp_pilot.calendar import Calendar
from tests import ClientTestMixin


class TestCalendar(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = Calendar

    def get_client(self, **kwargs):
        return super().get_client(email='chuck@norris.com')
