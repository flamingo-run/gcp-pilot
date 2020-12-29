from gcp_pilot.base import AccountManagerMixin, GoogleCloudPilotAPI, PolicyType


class GoogleResourceManager(AccountManagerMixin, GoogleCloudPilotAPI):
    def __init__(self):
        super().__init__(
            serviceName='cloudresourcemanager',
            version='v1',
        )

    def get_policy(self, project_id: str = None, version: int = 1) -> PolicyType:
        policy = self.client.projects().getIamPolicy(
            resource=project_id or self.project_id,
            body={"options": {"requestedPolicyVersion": version}},
        ).execute()
        return policy

    def set_policy(self, policy: PolicyType, project_id: str = None) -> PolicyType:
        return self.client.projects().setIamPolicy(
            resource=project_id or self.project_id,
            body={"policy": policy, "updateMask": 'bindings'},
        ).execute()

    async def add_member(self, email: str, role: str, project_id: str = None) -> PolicyType:
        policy = self.get_policy(project_id=project_id)
        changed_policy = self.bind_email_to_policy(email=email, role=role, policy=policy)
        return self.set_policy(policy=changed_policy, project_id=project_id)

    async def remove_member(self, email: str, role: str, project_id: str = None):
        policy = self.get_policy(project_id=project_id)
        changed_policy = self.unbind_email_from_policy(email=email, role=role, policy=policy)
        return self.set_policy(policy=changed_policy, project_id=project_id)

    def get_project(self, project_id: str):
        return self.client.projects().get(
            projectId=project_id or self.project_id,
        ).execute()
