import unittest

from gcp_pilot.speech import Speech
from tests import ClientTestMixin


class TestSpeechClient(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = Speech
