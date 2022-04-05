import unittest

from gcp_pilot.factories.identity_platform import FirebaseAuthTokenFactory
from gcp_pilot.identity_platform import IdentityPlatform, FirebaseAuthToken, parse_timestamp
from gcp_pilot.mocker import patch_firebase_token
from tests import ClientTestMixin


class TestIdentityPlatform(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = IdentityPlatform

    def test_parse_firebase_token(self):
        token_data = FirebaseAuthTokenFactory.create()
        with patch_firebase_token(return_value=token_data):
            token = FirebaseAuthToken(jwt_token="potato")

        self.assertEqual(parse_timestamp(token_data["exp"]), token.expiration_date)
        self.assertEqual(token_data["event_type"], token.event_type)
        self.assertEqual(token_data["ip_address"], token.ip_address)
        self.assertEqual(token_data["sign_in_method"], token.provider_id)
        # self.assertEqual(token_data["tenant_id"], token.tenant_id)  # FIXME
        self.assertEqual(token_data["user_agent"], token.user_agent)

        self.assertEqual(token_data["user_record"]["uid"], token.user.id)
        self.assertEqual(token_data["user_record"]["email"], token.user.email)
        self.assertEqual(token_data["user_record"]["display_name"], token.user.name)
        self.assertEqual(token_data["user_record"]["photo_url"], token.user.photo_url)
        self.assertEqual(token_data["user_record"]["email_verified"], token.user.verified)
        self.assertEqual(token_data["user_record"]["disabled"], token.user.disabled)
        self.assertEqual(parse_timestamp(token_data["user_record"]["metadata"]["creation_time"]), token.user.created_at)
        self.assertEqual(
            parse_timestamp(token_data["user_record"]["metadata"]["last_sign_in_time"]), token.user.last_login_at
        )

        self.assertEqual(token_data["oauth_access_token"], token.oauth.access_token)
        self.assertEqual(token_data["oauth_id_token"], token.oauth.id_token)
        self.assertEqual(token_data["oauth_refresh_token"], token.oauth.refresh_token)
        self.assertEqual(token_data["oauth_token_secret"], token.oauth.token_secret)
