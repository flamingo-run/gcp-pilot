# More Information: https://cloud.google.com/iam/docs/
from typing import Dict, Any, Generator

from gcp_pilot import exceptions
from gcp_pilot.base import GoogleCloudPilotAPI, AccountManagerMixin, PolicyType, DiscoveryMixin

AccountType = Dict[str, Any]


class IAM(AccountManagerMixin, DiscoveryMixin, GoogleCloudPilotAPI):
    def __init__(self, **kwargs):
        super().__init__(
            serviceName='iam',
            version='v1',
            cache_discovery=False,
            **kwargs,
        )

    def _parent_path(self, project_id: str = None) -> str:
        return f'projects/{project_id or self.project_id}'

    def _service_account_path(self, email: str, project_id: str = None) -> str:
        parent_path = self._parent_path(project_id=project_id)
        return f'{parent_path}/serviceAccounts/{email}'

    def _build_service_account_email(self, name: str, project_id: str = None) -> str:
        return f'{name}@{project_id or self.project_id}.iam.gserviceaccount.com'

    async def get_service_account(self, name: str, project_id: str = None) -> AccountType:
        account_path = self._service_account_path(
            email=self._build_service_account_email(name=name, project_id=project_id),
            project_id=project_id,
        )

        return self._execute(
            method=self.client.projects().serviceAccounts().get,
            name=account_path,
        )

    async def create_service_account(
            self,
            name: str,
            display_name: str,
            project_id: str = None,
            exists_ok: bool = True,
    ) -> AccountType:
        try:
            body = {
                'accountId': name,
                'serviceAccount': {
                    'displayName': display_name
                }
            }
            service_account = self._execute(
                method=self.client.projects().serviceAccounts().create,
                name=self._parent_path(project_id=project_id),
                body=body,
            )
        except exceptions.AlreadyExists:
            if not exists_ok:
                raise
            service_account = await self.get_service_account(name=name, project_id=project_id)
        return service_account

    async def list_service_accounts(self, project_id: str = None) -> Generator[AccountType, None, None]:
        params = dict(
            name=self._parent_path(project_id=project_id),
        )
        pagination = self._paginate(
            method=self.client.projects().serviceAccounts().list,
            result_key='accounts',
            params=params,
        )
        for item in pagination:
            yield item

    def get_policy(self, email: str, project_id: str = None) -> PolicyType:
        resource = self._service_account_path(email=email, project_id=project_id)
        return self._execute(
            method=self.client.projects().serviceAccounts().getIamPolicy,
            resource=resource,
        )

    def as_member(self, email: str) -> str:
        is_service_account = email.endswith('.gserviceaccount.com')
        prefix = 'serviceAccount' if is_service_account else 'member'
        return f'{prefix}:{email}'

    async def bind_member(self, target_email: str, member_email: str, role: str, project_id=None) -> PolicyType:
        policy = self.get_policy(email=target_email, project_id=project_id)
        changed_policy = self.bind_email_to_policy(email=member_email, role=role, policy=policy)
        return self.set_policy(email=target_email, policy=changed_policy, project_id=project_id)

    async def remove_member(
            self,
            target_email: str,
            member_email: str,
            role: str,
            project_id: str = None,
    ) -> PolicyType:
        policy = self.get_policy(email=target_email, project_id=project_id)
        changed_policy = self.unbind_email_from_policy(email=member_email, role=role, policy=policy)
        return self.set_policy(email=target_email, policy=changed_policy, project_id=project_id)

    def set_policy(self, email: str, policy: PolicyType, project_id: str = None) -> PolicyType:
        resource = self._service_account_path(email=email, project_id=project_id)
        return self._execute(
            method=self.client.projects().serviceAccounts().setIamPolicy,
            resource=resource,
            body={'policy': policy, 'updateMask': 'bindings'},
        )

    def get_compute_service_account(self, project_number: str = None) -> str:
        number = project_number or self._get_project_number(project_id=self.project_id)
        return f'{number}-compute@developer.gserviceaccount.com'

    def get_cloud_build_service_account(self, project_number: str = None) -> str:
        number = project_number or self._get_project_number(project_id=self.project_id)
        return f'{number}@cloudbuild.gserviceaccount.com'

    def get_cloud_run_service_account(self, project_number=None) -> str:
        number = project_number or self._get_project_number(project_id=self.project_id)
        return f'service-{number}@serverless-robot-prod.iam.gserviceaccount.com'
