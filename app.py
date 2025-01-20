#!/usr/bin/env python3
import os

import aws_cdk as cdk
import cdk_nag

from infrastructure.network_stack import NetworkStack
from infrastructure.threat_mitigation_stack import ThreatMitigationStack
from infrastructure.global_stack import GlobalStack

app = cdk.App()
cdk.Aspects.of(app).add(cdk_nag.AwsSolutionsChecks(verbose=True))

app_region = (
    app.node.try_get_context("region")
    or os.environ.get("CDK_DEFAULT_REGION")
    or os.environ.get("AWS_REGION")
    or os.environ.get("AWS_DEFAULT_REGION")
    or "us-east-1"
)

global_stack = GlobalStack(
    app,
    "ThreatMitigationGlobalStack",
    env=cdk.Environment(region="us-east-1"),
)
network_stack = NetworkStack(
    app, "ThreatMitigationNetworkStack", env=cdk.Environment(region=app_region)
)
stack = ThreatMitigationStack(
    app,
    "ThreatMitigationStack",
    cross_region_references=True,
    vpc=network_stack.vpc,
    waf=global_stack.waf,
    env=cdk.Environment(region=app_region),
)
stack.node.add_dependency(network_stack)
stack.node.add_dependency(global_stack)

cdk_nag.NagSuppressions.add_stack_suppressions(
    stack,
    [
        cdk_nag.NagPackSuppression(
            id="AwsSolutions-IAM4",
            reason="AWS managed IAM policy is used to run Lambda functions in VPC",
            applies_to=[
                "Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
                "Policy::arn:<AWS::Partition>:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole",
            ],
        )
    ],
)
cdk_nag.NagSuppressions.add_resource_suppressions_by_path(
    stack,
    "/ThreatMitigationStack/LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8a/ServiceRole/DefaultPolicy/Resource",
    [
        cdk_nag.NagPackSuppression(
            id="AwsSolutions-IAM5",
            reason="CDK generated resource to update LogRetention can access any LogGroup",
            applies_to=["Resource::*"],
        )
    ],
)
cdk_nag.NagSuppressions.add_resource_suppressions_by_path(
    stack,
    "/ThreatMitigationStack/BucketNotificationsHandler050a0587b7544547bf325f094a3db834/Role/DefaultPolicy/Resource",
    [
        cdk_nag.NagPackSuppression(
            id="AwsSolutions-IAM5",
            reason="CDK generated resource with s3:PutBucketNotification on any resource",
            applies_to=["Resource::*"],
        )
    ],
)
if cdk.Stack.of(stack).node.try_find_child("Custom::CDKBucketDeployment8693BB64968944B69AAFB0CC9EB8756C"):
    cdk_nag.NagSuppressions.add_resource_suppressions_by_path(
        stack,
        "/ThreatMitigationStack/Custom::CDKBucketDeployment8693BB64968944B69AAFB0CC9EB8756C/ServiceRole/DefaultPolicy/Resource",
        [
            cdk_nag.NagPackSuppression(
                id="AwsSolutions-IAM5",
                reason="CDK generated resource (BucketDeployment) requires S3 assets permissions",
            )
        ],
    )
    cdk_nag.NagSuppressions.add_resource_suppressions_by_path(
        stack,
        "/ThreatMitigationStack/Custom::CDKBucketDeployment8693BB64968944B69AAFB0CC9EB8756C/Resource",
        [
            cdk_nag.NagPackSuppression(
                id="AwsSolutions-L1",
                reason="CDK generated resource (BucketDeployment) uses non-latest runtime version",
            )
        ],
    )

app.synth()
