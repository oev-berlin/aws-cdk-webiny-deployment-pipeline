#!/usr/bin/env python3

from aws_cdk import core
import os

from infrastructure.cms_stack import CmsStack
from infrastructure.repository_stack import RepositoryStack

app = core.App()
project_name = app.node.try_get_context('project')
env = {
    'region': os.environ["CDK_DEFAULT_REGION"],
    'account': os.environ['CDK_DEFAULT_ACCOUNT']
}

repo = RepositoryStack(app, project_name + "-repository-stack", env=env)

prod = CmsStack(app, project_name + "-cms-stack-prod", "prod", env=env)
core.Tags.of(prod).add('project', project_name)

# dev = CmsStack(app, project_name + "-cms-stack-dev", "dev", env=env)
# core.Tags.of(dev).add('project', project_name)

# test = CmsStack(app, project_name + "-cms-stack-test", "test", env=env)
# core.Tags.of(test).add('project', project_name)


app.synth()
