from contextlib import ExitStack
from functools import wraps
from unittest.mock import Mock, patch

from google.oauth2.service_account import Credentials


class patch_auth:
    def __init__(self, project_id: str = "potato-dev", location: str = "moon-dark1", email: str = "chuck@norris.com"):
        # Realistic: actual class to be accepted by clients during validation
        # But fake: with as few attributes as possible, any API call using the credential should fail
        credentials = Credentials(
            service_account_email=email,
            signer=None,
            token_uri="",
            project_id=project_id,
        )
        managers = [
            patch("google.auth.default", return_value=(credentials, project_id)),
            patch("google.oauth2.service_account.Credentials.before_request", return_value=None),
            patch("google.oauth2.service_account.Credentials.refresh", return_value=None),
            patch("gcp_pilot.base.GoogleCloudPilotAPI._set_location", return_value=location),
            patch("gcp_pilot.base.AppEngineBasedService._set_location", return_value=location),
        ]
        self.stack = ExitStack()
        for mgr in managers:
            self.stack.enter_context(mgr)

    def __enter__(self):
        return self.stack.__enter__()

    def start(self):
        return self.__enter__()

    def __exit__(self, typ, val, traceback):
        return self.stack.__exit__(typ, val, traceback)

    def stop(self):
        self.__exit__(None, None, None)

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kw):
            with self:
                return func(*args, **kw)

        return wrapper


def patch_firebase_token(**kwargs):
    return patch("google.oauth2.id_token.verify_firebase_token", **kwargs)


class DiscoveryMixinTest:
    def setUp(self):
        self.mocked_discovery_client = Mock()
        _patch_build_client = patch(
            "gcp_pilot.base.GoogleCloudPilotAPI._build_client", return_value=self.mocked_discovery_client
        )
        _patch_build_client.start()
        self.addCleanup(_patch_build_client.stop)
