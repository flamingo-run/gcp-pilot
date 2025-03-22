import unittest
from unittest.mock import call

from gcp_pilot.drive import GoogleDrivePermissions
from gcp_pilot.mocker import DiscoveryMixinTest, patch_auth


class GoogleDrivePermissionsTest(DiscoveryMixinTest, unittest.TestCase):
    @staticmethod
    def get_service_instance():
        return GoogleDrivePermissions()

    def test_create_for_domain(self):
        expected_params = {
            "file_id": "file-id",
            "role": "reader",
            "domain": "domain.com",
            "extra_permission_body": {"photoLink": "photoLink"},
            "sendNotificationEmail": True,
        }
        with patch_auth():
            self.get_service_instance().create_for_domain(**expected_params)

        expected_body = {
            "role": expected_params["role"],
            "type": "domain",
            "domain": expected_params["domain"],
        } | expected_params["extra_permission_body"]

        expected_calls = [
            call().create(fileId=expected_params["file_id"], body=expected_body, sendNotificationEmail=True)
        ]
        self.mocked_discovery_client.permissions.assert_has_calls(expected_calls, any_order=True)

    def test_create_for_user(self):
        expected_params = {
            "file_id": "file-id",
            "role": "reader",
            "email": "user@email.io",
            "extra_permission_body": {"photoLink": "photoLink"},
            "sendNotificationEmail": True,
        }
        with patch_auth():
            self.get_service_instance().create_for_user(**expected_params)

        expected_body = {
            "role": expected_params["role"],
            "type": "user",
            "emailAddress": expected_params["email"],
        } | expected_params["extra_permission_body"]

        expected_calls = [
            call().create(fileId=expected_params["file_id"], body=expected_body, sendNotificationEmail=True)
        ]
        self.mocked_discovery_client.permissions.assert_has_calls(expected_calls, any_order=True)

    def test_create_for_group(self):
        expected_params = {
            "file_id": "file-id",
            "role": "reader",
            "email": "group@email.io",
            "extra_permission_body": {"photoLink": "photoLink"},
            "sendNotificationEmail": True,
        }
        with patch_auth():
            self.get_service_instance().create_for_group(**expected_params)

        expected_body = {
            "role": expected_params["role"],
            "type": "group",
            "emailAddress": expected_params["email"],
        } | expected_params["extra_permission_body"]

        expected_calls = [
            call().create(fileId=expected_params["file_id"], body=expected_body, sendNotificationEmail=True)
        ]
        self.mocked_discovery_client.permissions.assert_has_calls(expected_calls, any_order=True)

    def test_create_for_anyone(self):
        expected_params = {
            "file_id": "file-id",
            "role": "reader",
            "extra_permission_body": {"photoLink": "photoLink"},
            "sendNotificationEmail": True,
        }
        with patch_auth():
            self.get_service_instance().create_for_anyone(**expected_params)

        expected_body = {
            "role": expected_params["role"],
            "type": "anyone",
        } | expected_params["extra_permission_body"]

        expected_calls = [
            call().create(fileId=expected_params["file_id"], body=expected_body, sendNotificationEmail=True)
        ]
        self.mocked_discovery_client.permissions.assert_has_calls(expected_calls, any_order=True)

    def test_list(self):
        expected_file_id = "file-id"
        self.mocked_discovery_client.permissions.return_value.list.return_value.execute.return_value = {
            "permissions": [],
            "nextPageToken": False,
        }

        with patch_auth():
            list(self.get_service_instance().list(file_id=expected_file_id))

        expected_calls = [call().list(fileId=expected_file_id)]
        self.mocked_discovery_client.permissions.assert_has_calls(expected_calls, any_order=True)

    def test_get(self):
        expected_params = {"permission_id": "permission-id", "file_id": "file-id"}
        with patch_auth():
            self.get_service_instance().get(**expected_params)

        expected_calls = [
            call().get(
                fileId=expected_params["file_id"],
                permissionId=expected_params["permission_id"],
            )
        ]
        self.mocked_discovery_client.permissions.assert_has_calls(expected_calls, any_order=True)

    def test_update(self):
        expected_params = {
            "permission_id": "permission-id",
            "file_id": "file-id",
            "body": {"any": "value"},
        }
        with patch_auth():
            self.get_service_instance().update(**expected_params)

        expected_calls = [
            call().update(
                fileId=expected_params["file_id"],
                permissionId=expected_params["permission_id"],
                body=expected_params["body"],
            )
        ]
        self.mocked_discovery_client.permissions.assert_has_calls(expected_calls, any_order=True)

    def test_delete(self):
        expected_params = {"permission_id": "permission-id", "file_id": "file-id"}
        with patch_auth():
            self.get_service_instance().delete(**expected_params)

        expected_calls = [
            call().delete(
                permissionId=expected_params["permission_id"],
                fileId=expected_params["file_id"],
            )
        ]
        self.mocked_discovery_client.permissions.assert_has_calls(expected_calls, any_order=True)
