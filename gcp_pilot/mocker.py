from contextlib import ExitStack
from unittest.mock import patch

from google.oauth2.service_account import Credentials


def patch_auth(project_id: str = 'potato-dev', location: str = 'moon-dark1'):
    # Realistic: actual class to be accepted by clients during validation
    # But fake: with as few attributes as possible, any API call using the credential should fail
    credentials = Credentials(
        service_account_email='chuck@norris.com',
        signer=None,
        token_uri='',
        project_id=project_id,
    )
    managers = [
        patch('google.auth.default', return_value=(credentials, project_id)),
        patch('gcp_pilot.base.GoogleCloudPilotAPI._set_location', return_value=location),
        patch('gcp_pilot.base.AppEngineBasedService._set_location', return_value=location),
    ]
    stack = ExitStack()
    for mgr in managers:
        stack.enter_context(mgr)
    return stack
