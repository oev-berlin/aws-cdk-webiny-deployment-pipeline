from aws_cdk import (
    core,
    aws_codecommit as codecommit,
    aws_codebuild as codebuild,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_s3 as s3,
    aws_iam as iam,
)
import os


class CmsStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, stage: str,
                 **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Environment related settings
        if stage == "prod":
            branch = "master"
        elif stage == "dev":
            branch = "development"
        else:
            branch = stage

        project_name = self.node.try_get_context('project')

        codebuild_role = iam.Role(
            self,
            "CodeBuildDeploymentRole",
            assumed_by=iam.ServicePrincipal(service="codebuild.amazonaws.com"),
            description="Allows CodeBuild to deploy the cms",
            role_name=project_name + "-deployment-role-" + stage,
        )

        policy = iam.Policy(
            self,
            "DeploymentPolicy",
            roles=[codebuild_role],
            policy_name=project_name + "-deployment-policy-" + stage,
            statements=[
                iam.PolicyStatement(
                    sid="IamAccess",
                    effect=iam.Effect("ALLOW"),
                    resources=[
                        "arn:aws:iam::" + os.environ["CDK_DEFAULT_ACCOUNT"] +
                        ":*"
                    ],
                    actions=[
                        "iam:AttachRolePolicy",
                        "iam:CreateRole",
                        "iam:DeleteRole",
                        "iam:DetachRolePolicy",
                        "iam:GetRole",
                        "iam:PassRole",
                    ],
                ),
                iam.PolicyStatement(
                    sid="LambdaAccess",
                    effect=iam.Effect("ALLOW"),
                    resources=[
                        "arn:aws:lambda:" + os.environ["CDK_DEFAULT_REGION"] +
                        ":" + os.environ["CDK_DEFAULT_ACCOUNT"] +
                        ":function:*",
                    ],
                    actions=[
                        "lambda:AddPermission",
                        "lambda:AddPermission20150331v2",
                        "lambda:CreateFunction",
                        "lambda:CreateFunction20150331",
                        "lambda:DeleteFunction",
                        "lambda:DeleteFunction20150331",
                        "lambda:GetFunctionConfiguration",
                        "lambda:GetFunctionConfiguration20150331v2",
                        "lambda:UpdateFunctionCode",
                        "lambda:UpdateFunctionCode20150331v2",
                        "lambda:UpdateFunctionConfiguration",
                        "lambda:UpdateFunctionConfiguration20150331v2",
                        "lambda:PutFunctionConcurrency",
                    ],
                ),
                iam.PolicyStatement(
                    sid="ExternalLambdaPermissions",
                    effect=iam.Effect("ALLOW"),
                    resources=[
                        "arn:aws:lambda:eu-central-1:632417926021:layer:*"
                    ],
                    actions=[
                        "lambda:GetLayerVersion",
                    ],
                ),
                iam.PolicyStatement(
                    sid="S3Access",
                    effect=iam.Effect("ALLOW"),
                    resources=["arn:aws:s3:::*"],
                    actions=[
                        "s3:CreateBucket",
                        "s3:ListBucket",
                        "s3:PutAccelerateConfiguration",
                        "s3:PutBucketCORS",
                        "s3:PutBucketNotification",
                        "s3:PutObject",
                    ],
                ),
                iam.PolicyStatement(
                    sid="KmsAccess",
                    effect=iam.Effect("ALLOW"),
                    resources=[
                        "arn:aws:kms:" + os.environ["CDK_DEFAULT_REGION"] +
                        ":" + os.environ["CDK_DEFAULT_ACCOUNT"] + ":key/*"
                    ],
                    actions=[
                        "kms:CreateGrant",
                        "kms:Decrypt",
                        "kms:DescribeKey",
                        "kms:Encrypt",
                    ],
                ),
                iam.PolicyStatement(
                    sid="ApiGwAccess",
                    effect=iam.Effect("ALLOW"),
                    resources=[
                        "arn:aws:apigateway:" +
                        os.environ["CDK_DEFAULT_REGION"] + "::*"
                    ],
                    actions=[
                        "apigateway:DELETE",
                        "apigateway:GET",
                        "apigateway:POST",
                        "apigateway:PUT",
                    ],
                ),
                iam.PolicyStatement(
                    sid="CloudFrontAccess",
                    effect=iam.Effect("ALLOW"),
                    resources=["*"],
                    actions=[
                        "cloudfront:CreateDistribution",
                        "cloudfront:DeleteDistribution",
                        "cloudfront:GetDistributionConfig",
                        "cloudfront:UpdateDistribution",
                    ],
                ),
                iam.PolicyStatement(
                    sid="CognitoAccess",
                    effect=iam.Effect("ALLOW"),
                    resources=["*"],
                    actions=[
                        "cognito-idp:CreateUserPool",
                        "cognito-idp:CreateUserPoolClient",
                        "cognito-idp:DeleteUserPool",
                        "cognito-idp:UpdateUserPoolClient",
                    ],
                    # conditions={
                    #     "StringEquals": {
                    #         "aws:RequestedRegion":
                    #         "" + os.environ["CDK_DEFAULT_REGION"] + ""
                    #     }
                    # },
                ),
            ],
        )

        # environment bucket
        env_bucket = s3.Bucket(
            self,
            "EnvironmentBucket",
            bucket_name=project_name + "-environment-bucket-" + stage,
        )
        env_bucket.grant_read_write(identity=codebuild_role)

        # state bucket
        state_bucket = s3.Bucket(
            self,
            "StateBucket",
            bucket_name=project_name + "-state-bucket-" + stage,
        )
        state_bucket.grant_read_write(identity=codebuild_role)

        # CodePipeline
        pipeline = codepipeline.Pipeline(
            self,
            branch + "CodePipeline",
            pipeline_name=project_name + "-cms-pipeline-" + stage,
        )

        # CodeCommit Source
        source_output = codepipeline.Artifact()
        source_action = codepipeline_actions.CodeCommitSourceAction(
            action_name="Source",
            repository=codecommit.Repository.from_repository_name(
                self,
                "CodeCommitRepository",
                repository_name=project_name + "-cms-repository",
            ),
            output=source_output,
            branch=branch,
        )

        # CodeDeploy
        deploy_api_output = codepipeline.Artifact()
        deploy_api_project = codebuild.PipelineProject(
            self,
            "DeployApiProject",
            project_name=project_name + "-deploy-api-" + stage,
            build_spec=codebuild.BuildSpec.from_source_filename(
                "buildspec-api.yml"),
            environment=codebuild.BuildEnvironment(
                compute_type=codebuild.ComputeType.MEDIUM,
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
            ),
            role=codebuild_role,
            environment_variables={
                "ENVIRONMENT": codebuild.BuildEnvironmentVariable(value=stage)
            })

        deploy_api_action = codepipeline_actions.CodeBuildAction(
            action_name="deploy-api",
            input=source_output,
            project=deploy_api_project,
            outputs=[deploy_api_output],
        )

        deploy_apps_output = codepipeline.Artifact()
        deploy_apps_project = codebuild.PipelineProject(
            self,
            "DeployAppsProject",
            project_name=project_name + "-deploy-apps-" + stage,
            build_spec=codebuild.BuildSpec.from_source_filename(
                "buildspec-apps.yml"),
            environment=codebuild.BuildEnvironment(
                compute_type=codebuild.ComputeType.MEDIUM,
                build_image=codebuild.LinuxBuildImage.AMAZON_LINUX_2_3,
            ),
            role=codebuild_role,
            environment_variables={
                "ENVIRONMENT": codebuild.BuildEnvironmentVariable(value=stage)
            })

        deploy_apps_action = codepipeline_actions.CodeBuildAction(
            action_name="deploy-apps",
            input=source_output,
            project=deploy_apps_project,
            outputs=[deploy_apps_output],
        )

        # add pipeline stages
        pipeline.add_stage(stage_name="Source", actions=[source_action])
        pipeline.add_stage(stage_name="DeployApi", actions=[deploy_api_action])
        pipeline.add_stage(stage_name="DeployApps",
                           actions=[deploy_apps_action])
