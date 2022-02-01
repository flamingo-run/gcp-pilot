import unittest

from gcp_pilot.chats import ChatsBot, ChatsHook  # pylint: disable=unused-import
from tests import ClientTestMixin


class TestChatsBot(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = ChatsBot


class TestChatsHook(unittest.TestCase):
    pass
