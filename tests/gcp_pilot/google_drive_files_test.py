import unittest
from unittest.mock import call

from gcp_pilot.drive import GoogleDriveFiles
from gcp_pilot.mocker import DiscoveryMixinTest, patch_auth


class GoogleDriveFilesTest(DiscoveryMixinTest, unittest.TestCase):
    @staticmethod
    def get_service_instance():
        return GoogleDriveFiles()

    def test_list(self):
        self.mocked_discovery_client.files.return_value.list.return_value.execute.return_value = {
            "files": [],
            "nextPageToken": False,
        }
        with patch_auth():
            list(self.get_service_instance().list(order_by="createdTime"))

        expected_calls = [call().list(orderBy="createdTime")]
        self.mocked_discovery_client.files.assert_has_calls(expected_calls, any_order=True)
