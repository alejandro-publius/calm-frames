"""The CDK stack, synthesized and read back. Nothing is deployed.

The two assertions the plan calls out by name are here: zero NAT gateways, and
a budget alarm at 20 US dollars. The rest of the file checks the things that
would quietly cost money or open the buckets up.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

aws_cdk = pytest.importorskip("aws_cdk", reason="aws-cdk-lib is needed for the infra tests")

from aws_cdk import App, Environment  # noqa: E402
from aws_cdk.assertions import Match, Template  # noqa: E402

INFRA_DIR = Path(__file__).resolve().parents[1] / "infra"
if str(INFRA_DIR) not in sys.path:
    sys.path.insert(0, str(INFRA_DIR))

from calm_frames_stack import BUDGET_LIMIT_USD, CalmFramesStack, StackConfig  # noqa: E402


def synth(**config_overrides) -> Template:
    app = App()
    stack = CalmFramesStack(
        app,
        "TestStack",
        config=StackConfig(**config_overrides),
        env=Environment(account="123456789012", region="us-east-1"),
    )
    return Template.from_stack(stack)


@pytest.fixture(scope="module")
def template() -> Template:
    return synth(budget_email="alex@example.com", github_repo="owner/calm-frames")


class TestTheTwoThingsThatMatterMost:
    def test_there_are_no_nat_gateways(self, template):
        # The CDK default is one per availability zone, 65 to 100 US dollars a
        # month. This stack uses public subnets instead.
        template.resource_count_is("AWS::EC2::NatGateway", 0)

    def test_there_are_no_elastic_ips_either(self, template):
        # A NAT gateway brings an elastic IP with it, so this is the same
        # claim checked a second way.
        template.resource_count_is("AWS::EC2::EIP", 0)

    def test_the_budget_alarm_is_twenty_dollars_a_month(self, template):
        template.resource_count_is("AWS::Budgets::Budget", 1)
        template.has_resource_properties(
            "AWS::Budgets::Budget",
            {
                "Budget": Match.object_like(
                    {
                        "BudgetType": "COST",
                        "TimeUnit": "MONTHLY",
                        "BudgetLimit": {"Amount": BUDGET_LIMIT_USD, "Unit": "USD"},
                    }
                )
            },
        )
        assert BUDGET_LIMIT_USD == 20

    def test_the_budget_tells_someone(self, template):
        template.has_resource_properties(
            "AWS::Budgets::Budget",
            {
                "NotificationsWithSubscribers": Match.array_with(
                    [
                        Match.object_like(
                            {
                                "Subscribers": [
                                    {
                                        "Address": "alex@example.com",
                                        "SubscriptionType": "EMAIL",
                                    }
                                ]
                            }
                        )
                    ]
                )
            },
        )


class TestTheNetworkStaysCheap:
    def test_every_subnet_is_public(self, template):
        subnets = template.find_resources("AWS::EC2::Subnet")
        assert subnets
        for subnet in subnets.values():
            assert subnet["Properties"].get("MapPublicIpOnLaunch") is True

    def test_there_is_one_vpc_and_two_zones(self, template):
        template.resource_count_is("AWS::EC2::VPC", 1)
        assert len(template.find_resources("AWS::EC2::Subnet")) == 2

    def test_nothing_may_reach_the_ingest_task_from_outside(self, template):
        groups = template.find_resources("AWS::EC2::SecurityGroup")
        for group in groups.values():
            assert not group["Properties"].get("SecurityGroupIngress")


class TestBucketsStayPrivate:
    def test_both_buckets_block_public_access(self, template):
        buckets = template.find_resources("AWS::S3::Bucket")
        assert len(buckets) == 2
        for bucket in buckets.values():
            assert bucket["Properties"]["PublicAccessBlockConfiguration"] == {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True,
            }

    def test_both_buckets_are_encrypted(self, template):
        for bucket in template.find_resources("AWS::S3::Bucket").values():
            rules = bucket["Properties"]["BucketEncryption"][
                "ServerSideEncryptionConfiguration"
            ]
            assert rules[0]["ServerSideEncryptionByDefault"]["SSEAlgorithm"] == "AES256"

    def test_no_bucket_policy_opens_a_bucket_to_everyone(self, template):
        for policy in template.find_resources("AWS::S3::BucketPolicy").values():
            for statement in policy["Properties"]["PolicyDocument"]["Statement"]:
                if statement.get("Effect") != "Allow":
                    continue
                assert statement.get("Principal") != "*"
                assert statement.get("Principal") != {"AWS": "*"}

    def test_cloudfront_reads_the_delivery_bucket_through_origin_access_control(
        self, template
    ):
        template.resource_count_is("AWS::CloudFront::OriginAccessControl", 1)
        template.has_resource_properties(
            "AWS::CloudFront::Distribution",
            {
                "DistributionConfig": Match.object_like(
                    {
                        "DefaultCacheBehavior": Match.object_like(
                            {"ViewerProtocolPolicy": "redirect-to-https"}
                        )
                    }
                )
            },
        )

    def test_signed_urls_can_be_turned_on(self):
        template = synth(
            budget_email="alex@example.com",
            signing_public_key=(
                "-----BEGIN PUBLIC KEY-----\nMCowBQYDK2VwAyEA\n-----END PUBLIC KEY-----"
            ),
        )
        template.resource_count_is("AWS::CloudFront::KeyGroup", 1)
        template.has_resource_properties(
            "AWS::CloudFront::Distribution",
            {
                "DistributionConfig": Match.object_like(
                    {
                        "DefaultCacheBehavior": Match.object_like(
                            {"TrustedKeyGroups": Match.any_value()}
                        )
                    }
                )
            },
        )


class TestTheIngestTask:
    def test_one_fargate_task_definition_on_arm64(self, template):
        template.resource_count_is("AWS::ECS::TaskDefinition", 1)
        template.has_resource_properties(
            "AWS::ECS::TaskDefinition",
            {
                "RequiresCompatibilities": ["FARGATE"],
                "RuntimePlatform": {
                    "CpuArchitecture": "ARM64",
                    "OperatingSystemFamily": "LINUX",
                },
            },
        )

    def test_there_is_no_always_on_service(self, template):
        # A Fargate service would run around the clock. Ingest is one task per
        # upload and nothing in between.
        template.resource_count_is("AWS::ECS::Service", 0)

    def test_the_task_runs_the_image_from_this_stack(self, template):
        template.resource_count_is("AWS::ECR::Repository", 1)
        definitions = template.find_resources("AWS::ECS::TaskDefinition")
        container = list(definitions.values())[0]["Properties"]["ContainerDefinitions"][0]
        assert container["Name"] == "ingest"
        assert "Image" in container

    def test_an_upload_starts_the_task(self, template):
        template.has_resource_properties(
            "Custom::S3BucketNotifications",
            {
                "NotificationConfiguration": Match.object_like(
                    {
                        "LambdaFunctionConfigurations": Match.array_with(
                            [
                                Match.object_like(
                                    {
                                        "Events": ["s3:ObjectCreated:*"],
                                        "Filter": {
                                            "Key": {
                                                "FilterRules": [
                                                    {
                                                        "Name": "prefix",
                                                        "Value": "uploads/",
                                                    }
                                                ]
                                            }
                                        },
                                    }
                                )
                            ]
                        )
                    }
                )
            },
        )

    def test_the_catalog_table_is_on_demand(self, template):
        template.has_resource_properties(
            "AWS::DynamoDB::Table", {"BillingMode": "PAY_PER_REQUEST"}
        )

    def test_logs_do_not_pile_up_forever(self, template):
        groups = template.find_resources("AWS::Logs::LogGroup")
        assert groups
        for group in groups.values():
            assert group["Properties"].get("RetentionInDays")


class TestLeastPrivilege:
    def test_the_starter_may_only_run_this_one_task_definition(self, template):
        policies = template.find_resources("AWS::IAM::Policy")
        run_task = [
            statement
            for policy in policies.values()
            for statement in policy["Properties"]["PolicyDocument"]["Statement"]
            if "ecs:RunTask" in str(statement.get("Action"))
        ]
        assert run_task
        for statement in run_task:
            assert statement["Resource"] != "*"
            assert statement.get("Condition")

    def test_the_task_cannot_write_wherever_it_likes(self, template):
        policies = template.find_resources("AWS::IAM::Policy")
        for policy in policies.values():
            for statement in policy["Properties"]["PolicyDocument"]["Statement"]:
                actions = str(statement.get("Action"))
                if statement.get("Effect") == "Allow" and "s3:" in actions:
                    assert statement.get("Resource") != "*"

    def test_no_wildcard_admin_policy_anywhere(self, template):
        for policy in template.find_resources("AWS::IAM::Policy").values():
            for statement in policy["Properties"]["PolicyDocument"]["Statement"]:
                if statement.get("Effect") != "Allow":
                    continue
                assert statement.get("Action") != "*"
                assert statement.get("Action") != ["*"]


class TestGitHubDeploysWithoutStoredKeys:
    def test_no_iam_user_and_no_access_key_exist(self, template):
        template.resource_count_is("AWS::IAM::User", 0)
        template.resource_count_is("AWS::IAM::AccessKey", 0)

    def test_the_deploy_role_trusts_the_github_token_for_one_repository(self, template):
        roles = template.find_resources("AWS::IAM::Role")
        federated = [
            role
            for role in roles.values()
            for statement in role["Properties"]["AssumeRolePolicyDocument"]["Statement"]
            if statement.get("Action") == "sts:AssumeRoleWithWebIdentity"
        ]
        assert len(federated) == 1
        statement = federated[0]["Properties"]["AssumeRolePolicyDocument"]["Statement"][0]
        conditions = statement["Condition"]
        assert (
            conditions["StringLike"]["token.actions.githubusercontent.com:sub"]
            == "repo:owner/calm-frames:*"
        )
        assert (
            conditions["StringEquals"]["token.actions.githubusercontent.com:aud"]
            == "sts.amazonaws.com"
        )

    def test_no_deploy_role_without_a_repository(self):
        template = synth(budget_email="alex@example.com")
        roles = template.find_resources("AWS::IAM::Role")
        federated = [
            role
            for role in roles.values()
            for statement in role["Properties"]["AssumeRolePolicyDocument"]["Statement"]
            if statement.get("Action") == "sts:AssumeRoleWithWebIdentity"
        ]
        assert federated == []


class TestCostTags:
    def test_the_taggable_resources_carry_the_cost_tags(self, template):
        for resource_type in ("AWS::S3::Bucket", "AWS::DynamoDB::Table", "AWS::EC2::VPC"):
            for resource in template.find_resources(resource_type).values():
                tags = {tag["Key"]: tag["Value"] for tag in resource["Properties"]["Tags"]}
                assert tags["Project"] == "calm-frames"
                assert tags["CostCenter"] == "calm-frames-hackathon"
                assert tags["ManagedBy"] == "cdk"

    def test_the_budget_follows_the_project_tag(self, template):
        template.has_resource_properties(
            "AWS::Budgets::Budget",
            {
                "Budget": Match.object_like(
                    {"CostFilters": {"TagKeyValue": ["user:Project$calm-frames"]}}
                )
            },
        )


class TestNothingIsDeployed:
    def test_destroying_the_stack_leaves_nothing_behind(self, template):
        for resource_type in ("AWS::S3::Bucket", "AWS::DynamoDB::Table", "AWS::ECR::Repository"):
            for resource in template.find_resources(resource_type).values():
                assert resource.get("DeletionPolicy") == "Delete"
