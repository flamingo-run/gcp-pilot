from gcp_pilot.base import AccountManagerMixin, GoogleCloudPilotAPI, PolicyType, DiscoveryMixin


class ResourceManager(AccountManagerMixin, DiscoveryMixin, GoogleCloudPilotAPI):
    def __init__(self, **kwargs):
        super().__init__(
            serviceName='cloudresourcemanager',
            version='v1',
            cache_discovery=False,
            **kwargs,
        )

    def get_policy(self, project_id: str = None, version: int = 1) -> PolicyType:
        return self._execute(
            method=self.client.projects().getIamPolicy,
            resource=project_id or self.project_id,
            body={"options": {"requestedPolicyVersion": version}},
        )

    def set_policy(self, policy: PolicyType, project_id: str = None) -> PolicyType:
        return self._execute(
            method=self.client.projects().setIamPolicy,
            resource=project_id or self.project_id,
            body={"policy": policy, "updateMask": 'bindings'},
        )

    async def add_member(self, email: str, role: str, project_id: str = None) -> PolicyType:
        policy = self.get_policy(project_id=project_id)
        changed_policy = self.bind_email_to_policy(email=email, role=role, policy=policy)
        return self.set_policy(policy=changed_policy, project_id=project_id)

    async def remove_member(self, email: str, role: str, project_id: str = None):
        policy = self.get_policy(project_id=project_id)
        changed_policy = self.unbind_email_from_policy(email=email, role=role, policy=policy)
        return self.set_policy(policy=changed_policy, project_id=project_id)

    def get_project(self, project_id: str):
        return self._execute(
            method=self.client.projects().get,
            projectId=project_id or self.project_id,
        )
