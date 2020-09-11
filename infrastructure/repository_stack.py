from aws_cdk import core, aws_codecommit as codecommit


class RepositoryStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        project_name = self.node.try_get_context("project")

        cms_repository = codecommit.Repository(
            self, "CmsRepository", repository_name=project_name + "-cms-repository"
        )