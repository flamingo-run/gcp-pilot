from contextlib import ExitStack
from typing import Any
from unittest.mock import Mock, patch


def patch_auth(credentials: Any = Mock(), project_id: str = 'potato-dev', location: str = 'moon-dark1'):
    managers = [
        patch('google.auth.default', return_value=(credentials, project_id)),
        patch('gcp_pilot.base.GoogleCloudPilotAPI._set_location', return_value=location)
    ]
    stack = ExitStack()
    for mgr in managers:
        stack.enter_context(mgr)
    return stack
