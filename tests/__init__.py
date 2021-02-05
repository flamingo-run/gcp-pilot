from gcp_pilot.mocker import patch_auth


class ClientTestMixin:
    _CLIENT_KLASS = None

    def get_client(self, **kwargs):
        return self._CLIENT_KLASS(**kwargs)

    def test_mocked_auth(self):
        with patch_auth():
            self.get_client()
