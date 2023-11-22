import json
import unittest
from datetime import UTC, datetime
from pathlib import Path

from gcp_pilot.factories.identity_platform import FirebaseAuthTokenFactory
from gcp_pilot.identity_platform import FirebaseAuthToken, IdentityPlatform, parse_timestamp
from gcp_pilot.mocker import patch_firebase_token
from tests import ClientTestMixin


class TestParseTimestamp(unittest.TestCase):
    def test_parse_timestamp(self):
        sometime = datetime(2022, 5, 17, 1, 2, 57, tzinfo=UTC)
        sometimestamp = int(sometime.timestamp())
        generated_time = parse_timestamp(sometimestamp)
        self.assertEqual(sometime, generated_time)


class TestIdentityPlatform(ClientTestMixin, unittest.TestCase):
    _CLIENT_KLASS = IdentityPlatform

    @classmethod
    def _load_sample_token(cls, sample_name: str) -> tuple[dict, FirebaseAuthToken]:
        sample_path = Path(__file__).parent / "samples" / "identity_platform" / f"{sample_name}.json"
        token_data = json.load(sample_path.open())
        with patch_firebase_token(return_value=token_data):
            return token_data, FirebaseAuthToken(jwt_token="potato")

    def assert_expected_sample_token(
        self,
        expected_data: dict,
        token: FirebaseAuthToken,
        is_tenant: bool,
        is_expired: bool = True,
    ):
        self.assertEqual(parse_timestamp(expected_data["exp"]), token.expiration_date)
        self.assertEqual(expected_data["event_type"], token.event_type)
        self.assertEqual(expected_data["event_id"], token.event_id)
        self.assertEqual(expected_data["ip_address"], token.ip_address)
        self.assertEqual(expected_data["sign_in_method"], token.provider_id)
        self.assertEqual(expected_data["user_agent"], token.user_agent)

        self.assertEqual(json.loads(expected_data["raw_user_info"]), token.raw_user)

        self.assertEqual(expected_data["user_record"]["uid"], token.user.id)
        self.assertEqual(expected_data["user_record"].get("email"), token.user.email)
        self.assertEqual(expected_data["user_record"].get("display_name"), token.user.name)
        self.assertEqual(expected_data["user_record"].get("photo_url"), token.user.photo_url)
        self.assertEqual(expected_data["user_record"].get("email_verified"), token.user.verified)
        self.assertEqual(expected_data["user_record"].get("disabled"), token.user.disabled)
        self.assertEqual(
            parse_timestamp(expected_data["user_record"]["metadata"]["creation_time"]),
            token.user.created_at,
        )
        self.assertEqual(
            parse_timestamp(expected_data["user_record"]["metadata"]["last_sign_in_time"]),
            token.user.last_login_at,
        )

        self.assertEqual(expected_data["oauth_access_token"], token.oauth.access_token)
        self.assertEqual(expected_data["oauth_id_token"], token.oauth.id_token)
        self.assertEqual(expected_data["oauth_refresh_token"], token.oauth.refresh_token)
        self.assertEqual(expected_data["oauth_token_secret"], token.oauth.token_secret)

        self.assertEqual(expected_data["aud"], token.jwt_info.aud)
        self.assertEqual(expected_data["iss"], token.jwt_info.iss)
        self.assertEqual(parse_timestamp(expected_data["iat"]), token.jwt_info.iat)
        self.assertEqual(parse_timestamp(expected_data["exp"]), token.jwt_info.exp)
        self.assertEqual(expected_data["sub"], token.jwt_info.sub)
        self.assertEqual(is_expired, token.jwt_info.is_expired)

        if is_tenant:
            self.assertEqual(expected_data["tenant_id"], token.tenant_id)
            self.assertEqual(expected_data["user_record"]["tenant_id"], token.user.tenant_id)
        else:
            self.assertFalse("tenant_id" in expected_data)
            self.assertIsNone(token.tenant_id)
            self.assertFalse("tenant_id" in expected_data["user_record"])
            self.assertIsNone(token.user.tenant_id)

    def test_parse_tenant_oidc_signin_token(self):
        token_data, token = self._load_sample_token("firebase_tenant_oidc_signin_decoded_token")
        self.assert_expected_sample_token(expected_data=token_data, token=token, is_tenant=True)

    def test_parse_tenant_signin_token(self):
        token_data, token = self._load_sample_token("firebase_tenant_signin_decoded_token")
        self.assert_expected_sample_token(expected_data=token_data, token=token, is_tenant=True)

    def test_parse_signin_token(self):
        token_data, token = self._load_sample_token("firebase_signin_decoded_token")
        self.assert_expected_sample_token(expected_data=token_data, token=token, is_tenant=False)

    def test_parse_firebase_factory_token(self):
        iat = int(datetime.now(tz=UTC).timestamp())
        token_data = FirebaseAuthTokenFactory.create(iat=iat)
        with patch_firebase_token(return_value=token_data):
            token = FirebaseAuthToken(jwt_token="potato")

        self.assert_expected_sample_token(expected_data=token_data, token=token, is_tenant=True, is_expired=False)
