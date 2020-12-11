from googleapiclient.errors import HttpError

from gcp_pilot import exceptions
from gcp_pilot.base import GoogleCloudPilotAPI


class Directory(GoogleCloudPilotAPI):
    _scopes = [
        'https://www.googleapis.com/auth/admin.directory.group',
        'https://www.googleapis.com/auth/admin.directory.user',
    ]

    def __init__(self, email):
        self.email = email
        super().__init__(
            serviceName='admin',
            version='directory_v1',
            cache_discovery=False,
        )

    def get_users(self, domain=None):
        yield from self._paginate(
            method=self.client.users().list,
            result_key='users',
            params=dict(
                customer='my_customer',  # TODO: double check this param
                domain=domain,
                orderBy='email',
            )
        )

    def get_groups(self, domain=None):
        yield from self._paginate(
            method=self.client.groups().list,
            result_key='groups',
            params=dict(
                domain=domain,
            )
        )

    def get_group(self, group_id):
        return self.client.groups().get(
            groupKey=group_id,
        ).execute()

    def create_or_update_group(self, email, name=None, description=None, group_id=None):
        body = dict(
            email=email,
            name=name,
            description=description,
        )

        if not group_id:
            return self.client.groups().insert(
                body=body,
            ).execute()
        else:
            return self.client.groups().update(
                groupKey=group_id,
                body=body,
            ).execute()

    def delete_group(self, group_id):
        try:
            return self.client.groups().delete(
                groupKey=group_id,
            ).execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise exceptions.NotFoundError()
            raise e

    def get_group_members(self, group_id):
        page_token = None

        while True:
            results = self.client.members().list(
                groupKey=group_id,
                pageToken=page_token,
            ).execute()
            for member in results.get('members', []):
                yield member

            page_token = results.get('nextPageToken')
            if not page_token:
                break

    def add_group_member(self, group_id, email, role='MEMBER'):
        body = {'email': email, 'role': role}

        try:
            return self.client.members().insert(
                groupKey=group_id,
                body=body,
            ).execute()
        except HttpError as e:
            if e.resp.status == 409:
                raise exceptions.AlreadyExistsError()

            if e.resp.status == 404:
                raise exceptions.NotFoundError()

            raise e

    def delete_group_member(self, group_id, member_id):
        try:
            return self.client.members().delete(
                groupKey=group_id,
                memberKey=member_id,
            ).execute()
        except HttpError as e:
            if e.resp.status == 404:
                raise exceptions.NotFoundError()
            raise e
