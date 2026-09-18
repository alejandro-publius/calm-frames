"""The Calm Frames ingest stack.

Shape, and why each piece is what it is:

- two private S3 buckets. ``source`` takes the uploads and is never reachable
  from the internet. ``delivery`` holds the kid safe renditions, maps, posters
  and trickplay, and CloudFront reads it through origin access control, so the
  bucket itself stays private;
- one DynamoDB table on demand for the catalog, with the same fields as the
  local JSON catalog;
- one ECR repository plus one ARM64 Fargate task definition, running the same
  ingest container as the local pipeline;
- an S3 upload notification starts that task through a small Lambda. No
  EventBridge and no Step Functions, which the plan rules out while the cut
  list still has items on it;
- a VPC with ``nat_gateways=0`` and public subnets only. The CDK default is a
  NAT gateway per availability zone, which is 65 to 100 US dollars a month and
  would be the largest line on the bill by far. The task gets a public IP
  instead;
- a GitHub OIDC role for deploys, so no AWS key is ever stored in the repo or
  in GitHub;
- cost allocation tags on everything, and a 20 US dollar budget alarm.

Nothing here is deployed by this lane. It is synthesized and unit tested.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    Tags,
)
from aws_cdk import aws_budgets as budgets
from aws_cdk import aws_cloudfront as cloudfront
from aws_cdk import aws_cloudfront_origins as origins
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_notifications as s3n
from constructs import Construct

UPLOAD_PREFIX = "uploads/"
BUDGET_LIMIT_USD = 20

# The token GitHub Actions presents, and the thumbprint AWS documents for it.
GITHUB_OIDC_URL = "https://token.actions.githubusercontent.com"
GITHUB_OIDC_AUDIENCE = "sts.amazonaws.com"
GITHUB_OIDC_THUMBPRINT = "6938fd4d98bab03faadb97b34396831e3780aea1"

STARTER_CODE = """
import json
import os
import urllib.parse

import boto3

ecs = boto3.client("ecs")


def handler(event, context):
    \"\"\"Start one ingest task per uploaded object.

    The task runs the same container as the local pipeline and is handed the
    bucket and key it should read.
    \"\"\"
    started = []
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
        response = ecs.run_task(
            cluster=os.environ["CLUSTER_ARN"],
            taskDefinition=os.environ["TASK_DEFINITION_ARN"],
            launchType="FARGATE",
            count=1,
            networkConfiguration={
                "awsvpcConfiguration": {
                    "subnets": os.environ["SUBNET_IDS"].split(","),
                    "securityGroups": [os.environ["SECURITY_GROUP_ID"]],
                    # No NAT gateway in this VPC, so the task needs a public
                    # IP to reach ECR and the AWS APIs.
                    "assignPublicIp": "ENABLED",
                }
            },
            overrides={
                "containerOverrides": [
                    {
                        "name": os.environ["CONTAINER_NAME"],
                        "environment": [
                            {"name": "CALM_FRAMES_SOURCE_BUCKET", "value": bucket},
                            {"name": "CALM_FRAMES_SOURCE_KEY", "value": key},
                        ],
                    }
                ]
            },
        )
        started.append([task["taskArn"] for task in response.get("tasks", [])])
    return {"started": started}
"""


@dataclass
class StackConfig:
    """Everything an operator has to decide, in one place."""

    budget_email: str = ""
    github_repo: str = ""  # "owner/name"
    github_oidc_provider_arn: str = ""  # reuse an existing provider when set
    signing_public_key: str = ""  # PEM, turns on CloudFront signed URLs
    # An SSM SecureString holding the map signing private key. Empty means the
    # task signs nothing, which is the default: an unsigned map is refused by
    # every player, so the safe setting is the one that publishes nothing rather
    # than the one that puts a private key in the cloud. docs/SECURITY.md says
    # what you are taking on when you set it.
    signing_key_parameter: str = ""
    # One preset in the cloud. Each extra preset is another full encode of the
    # title, which is the largest line in the cost estimate.
    presets: tuple[str, ...] = ("wcag",)
    task_cpu: int = 2048
    task_memory_mib: int = 4096
    log_retention: logs.RetentionDays = logs.RetentionDays.TWO_WEEKS
    cost_tags: dict[str, str] = field(
        default_factory=lambda: {
            "Project": "calm-frames",
            "Component": "pipeline",
            "Environment": "hackathon",
            "CostCenter": "calm-frames-hackathon",
            "ManagedBy": "cdk",
        }
    )


class CalmFramesStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        config: StackConfig | None = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.config = config or StackConfig()

        for key, value in self.config.cost_tags.items():
            Tags.of(self).add(key, value)

        self.source_bucket = self._source_bucket()
        self.delivery_bucket = self._delivery_bucket()
        self.catalog_table = self._catalog_table()
        self.distribution = self._distribution()
        self.vpc, self.security_group = self._network()
        self.repository, self.cluster, self.task_definition = self._ingest_task()
        self._upload_trigger()
        self._github_deploy_role()
        self._budget()
        self._outputs()

    # Storage

    def _source_bucket(self) -> s3.Bucket:
        return s3.Bucket(
            self,
            "SourceBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    abort_incomplete_multipart_upload_after=Duration.days(3),
                    # A source file is only needed until its title is built and
                    # verified. Keeping masters around is the main storage cost.
                    expiration=Duration.days(30),
                    prefix=UPLOAD_PREFIX,
                )
            ],
        )

    def _delivery_bucket(self) -> s3.Bucket:
        return s3.Bucket(
            self,
            "DeliveryBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            cors=[
                s3.CorsRule(
                    allowed_methods=[s3.HttpMethods.GET, s3.HttpMethods.HEAD],
                    allowed_origins=["*"],
                    allowed_headers=["Range", "Origin"],
                    max_age=3600,
                )
            ],
        )

    def _catalog_table(self) -> dynamodb.Table:
        return dynamodb.Table(
            self,
            "CatalogTable",
            partition_key=dynamodb.Attribute(
                name="sha256", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            # Point in time recovery doubles the storage cost of a table that
            # can be rebuilt from the artifacts in S3.
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=False
            ),
        )

    # Delivery

    def _distribution(self) -> cloudfront.Distribution:
        trusted_key_groups = []
        if self.config.signing_public_key:
            public_key = cloudfront.PublicKey(
                self,
                "SigningPublicKey",
                encoded_key=self.config.signing_public_key,
            )
            trusted_key_groups.append(
                cloudfront.KeyGroup(self, "SigningKeyGroup", items=[public_key])
            )

        return cloudfront.Distribution(
            self,
            "Delivery",
            comment="Calm Frames kid safe renditions, maps, posters and trickplay",
            default_behavior=cloudfront.BehaviorOptions(
                # Origin access control, so the bucket stays private and only
                # this distribution can read it.
                origin=origins.S3BucketOrigin.with_origin_access_control(
                    self.delivery_bucket
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                response_headers_policy=cloudfront.ResponseHeadersPolicy.CORS_ALLOW_ALL_ORIGINS,
                trusted_key_groups=trusted_key_groups or None,
            ),
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,
            enable_logging=False,
        )

    # Compute

    def _network(self) -> tuple[ec2.Vpc, ec2.SecurityGroup]:
        vpc = ec2.Vpc(
            self,
            "Vpc",
            max_azs=2,
            # The line that keeps this stack cheap. A NAT gateway per zone
            # would cost more than everything else here put together.
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24
                )
            ],
        )
        group = ec2.SecurityGroup(
            self,
            "IngestSecurityGroup",
            vpc=vpc,
            description="Calm Frames ingest task. Outbound only.",
            allow_all_outbound=True,
        )
        return vpc, group

    def _ingest_task(self) -> tuple[ecr.Repository, ecs.Cluster, ecs.FargateTaskDefinition]:
        repository = ecr.Repository(
            self,
            "IngestImage",
            image_scan_on_push=True,
            removal_policy=RemovalPolicy.DESTROY,
            empty_on_delete=True,
            lifecycle_rules=[ecr.LifecycleRule(max_image_count=5)],
        )

        cluster = ecs.Cluster(
            self,
            "IngestCluster",
            vpc=self.vpc,
            container_insights_v2=ecs.ContainerInsights.DISABLED,
        )

        task_definition = ecs.FargateTaskDefinition(
            self,
            "IngestTask",
            cpu=self.config.task_cpu,
            memory_limit_mib=self.config.task_memory_mib,
            runtime_platform=ecs.RuntimePlatform(
                cpu_architecture=ecs.CpuArchitecture.ARM64,
                operating_system_family=ecs.OperatingSystemFamily.LINUX,
            ),
        )
        task_logs = logs.LogGroup(
            self,
            "IngestTaskLogs",
            retention=self.config.log_retention,
            removal_policy=RemovalPolicy.DESTROY,
        )
        environment = {
            "CALM_FRAMES_DELIVERY_BUCKET": self.delivery_bucket.bucket_name,
            "CALM_FRAMES_CATALOG_TABLE": self.catalog_table.table_name,
            "CALM_FRAMES_SOURCE_BUCKET": self.source_bucket.bucket_name,
            "CALM_FRAMES_PRESETS": ",".join(self.config.presets),
            "CALM_FRAMES_WORKDIR": "/work",
        }
        if self.config.signing_key_parameter:
            environment["CALM_FRAMES_SIGNING_KEY_PARAM"] = self.config.signing_key_parameter

        task_definition.add_container(
            "ingest",
            image=ecs.ContainerImage.from_ecr_repository(repository, "latest"),
            logging=ecs.LogDrivers.aws_logs(stream_prefix="ingest", log_group=task_logs),
            environment=environment,
        )

        # Least privilege: read the uploads, write the artifacts, write the
        # catalog row. Nothing else.
        self.source_bucket.grant_read(task_definition.task_role, f"{UPLOAD_PREFIX}*")
        self.delivery_bucket.grant_put(task_definition.task_role)
        self.delivery_bucket.grant_read(task_definition.task_role)
        self.catalog_table.grant_write_data(task_definition.task_role)
        repository.grant_pull(task_definition.obtain_execution_role())

        if self.config.signing_key_parameter:
            name = self.config.signing_key_parameter.lstrip("/")
            task_definition.task_role.add_to_principal_policy(
                iam.PolicyStatement(
                    actions=["ssm:GetParameter"],
                    resources=[
                        f"arn:aws:ssm:{self.region}:{self.account}:parameter/{name}"
                    ],
                )
            )
            # A SecureString is decrypted by KMS, not by SSM, so reading one
            # needs kms:Decrypt as well. The parameter is expected to use the
            # account's aws/ssm key, whose id is not known at synth time, so the
            # condition does the narrowing instead: this grant only works when
            # the call arrives through SSM in this region.
            task_definition.task_role.add_to_principal_policy(
                iam.PolicyStatement(
                    actions=["kms:Decrypt"],
                    resources=[f"arn:aws:kms:{self.region}:{self.account}:key/*"],
                    conditions={
                        "StringEquals": {
                            "kms:ViaService": f"ssm.{self.region}.amazonaws.com"
                        }
                    },
                )
            )

        return repository, cluster, task_definition

    def _upload_trigger(self) -> lambda_.Function:
        starter_logs = logs.LogGroup(
            self,
            "StartIngestLogs",
            retention=self.config.log_retention,
            removal_policy=RemovalPolicy.DESTROY,
        )
        starter = lambda_.Function(
            self,
            "StartIngest",
            runtime=lambda_.Runtime.PYTHON_3_12,
            architecture=lambda_.Architecture.ARM_64,
            handler="index.handler",
            code=lambda_.Code.from_inline(STARTER_CODE),
            timeout=Duration.seconds(30),
            memory_size=256,
            log_group=starter_logs,
            environment={
                "CLUSTER_ARN": self.cluster.cluster_arn,
                "TASK_DEFINITION_ARN": self.task_definition.task_definition_arn,
                "CONTAINER_NAME": "ingest",
                "SUBNET_IDS": ",".join(
                    subnet.subnet_id for subnet in self.vpc.public_subnets
                ),
                "SECURITY_GROUP_ID": self.security_group.security_group_id,
            },
        )

        starter.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ecs:RunTask"],
                resources=[self.task_definition.task_definition_arn],
                conditions={
                    "ArnEquals": {"ecs:cluster": self.cluster.cluster_arn}
                },
            )
        )
        starter.add_to_role_policy(
            iam.PolicyStatement(
                actions=["iam:PassRole"],
                resources=[
                    self.task_definition.task_role.role_arn,
                    self.task_definition.obtain_execution_role().role_arn,
                ],
                conditions={"StringEquals": {"iam:PassedToService": "ecs-tasks.amazonaws.com"}},
            )
        )

        self.source_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(starter),
            s3.NotificationKeyFilter(prefix=UPLOAD_PREFIX),
        )
        return starter

    # Deploys and cost

    def _github_deploy_role(self) -> iam.Role | None:
        """A role GitHub Actions assumes with an OIDC token. No stored keys.

        It can do one thing: assume the CDK bootstrap roles in this account.
        That is what ``cdk deploy`` needs and nothing more.
        """
        if not self.config.github_repo:
            return None

        if self.config.github_oidc_provider_arn:
            provider_arn = self.config.github_oidc_provider_arn
        else:
            provider = iam.CfnOIDCProvider(
                self,
                "GitHubOidcProvider",
                url=GITHUB_OIDC_URL,
                client_id_list=[GITHUB_OIDC_AUDIENCE],
                thumbprint_list=[GITHUB_OIDC_THUMBPRINT],
            )
            provider_arn = provider.attr_arn

        role = iam.Role(
            self,
            "GitHubDeployRole",
            assumed_by=iam.FederatedPrincipal(
                provider_arn,
                conditions={
                    "StringEquals": {
                        f"{GITHUB_OIDC_URL.removeprefix('https://')}:aud": (
                            GITHUB_OIDC_AUDIENCE
                        )
                    },
                    "StringLike": {
                        f"{GITHUB_OIDC_URL.removeprefix('https://')}:sub": (
                            f"repo:{self.config.github_repo}:*"
                        )
                    },
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
            description="GitHub Actions deploy role for Calm Frames. No stored keys.",
            max_session_duration=Duration.hours(1),
        )
        role.add_to_policy(
            iam.PolicyStatement(
                actions=["sts:AssumeRole"],
                resources=[
                    f"arn:aws:iam::{self.account}:role/cdk-*-deploy-role-*",
                    f"arn:aws:iam::{self.account}:role/cdk-*-file-publishing-role-*",
                    f"arn:aws:iam::{self.account}:role/cdk-*-image-publishing-role-*",
                    f"arn:aws:iam::{self.account}:role/cdk-*-lookup-role-*",
                ],
            )
        )
        return role

    def _budget(self) -> budgets.CfnBudget:
        subscribers = []
        if self.config.budget_email:
            subscribers = [
                budgets.CfnBudget.NotificationWithSubscribersProperty(
                    notification=budgets.CfnBudget.NotificationProperty(
                        comparison_operator="GREATER_THAN",
                        notification_type=notification_type,
                        threshold=threshold,
                        threshold_type="PERCENTAGE",
                    ),
                    subscribers=[
                        budgets.CfnBudget.SubscriberProperty(
                            address=self.config.budget_email,
                            subscription_type="EMAIL",
                        )
                    ],
                )
                for notification_type, threshold in (
                    ("ACTUAL", 50),
                    ("ACTUAL", 80),
                    ("FORECASTED", 100),
                )
            ]

        return budgets.CfnBudget(
            self,
            "MonthlyBudget",
            budget=budgets.CfnBudget.BudgetDataProperty(
                budget_type="COST",
                time_unit="MONTHLY",
                budget_name="calm-frames-monthly",
                budget_limit=budgets.CfnBudget.SpendProperty(
                    amount=BUDGET_LIMIT_USD, unit="USD"
                ),
                cost_filters={"TagKeyValue": ["user:Project$calm-frames"]},
            ),
            notifications_with_subscribers=subscribers,
        )

    def _outputs(self) -> None:
        CfnOutput(self, "SourceBucketName", value=self.source_bucket.bucket_name)
        CfnOutput(self, "DeliveryBucketName", value=self.delivery_bucket.bucket_name)
        CfnOutput(self, "DistributionDomain", value=self.distribution.domain_name)
        CfnOutput(self, "CatalogTableName", value=self.catalog_table.table_name)
        CfnOutput(self, "IngestImageRepository", value=self.repository.repository_uri)
