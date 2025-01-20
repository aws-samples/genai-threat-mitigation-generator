import os
from typing import Optional, Sequence
import cdk_nag
from aws_cdk import (
    aws_ec2 as ec2,
    aws_lambda,
    aws_iam as iam,
    aws_kms as kms,
    aws_s3 as s3,
    Duration,
    Stack,
    RemovalPolicy,
)
from .api_endpoint import ApiEndpoint
from constructs import Construct


class DiagramToText(Construct):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.Vpc,
        s3_access_logs_bucket: s3.IBucket,
        s3_access_logs_prefix: str,
        layers: Optional[Sequence[aws_lambda.ILayerVersion]] = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        kms_key = kms.Key(
            self,
            "KmsKey",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.DESTROY,
        )
        self.bucket = s3.Bucket(
            self,
            "Bucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            encryption=s3.BucketEncryption.KMS,
            encryption_key=kms_key,
            enforce_ssl=True,
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY,
            server_access_logs_bucket=s3_access_logs_bucket,
            server_access_logs_prefix=s3_access_logs_prefix,
        )
        self.endpoint = ApiEndpoint(
            self,
            "Endpoint",
            code=aws_lambda.Code.from_asset(
                os.path.join(
                    os.path.dirname(os.path.realpath(__file__)), "diagram_to_text"
                ),
                bundling=ApiEndpoint.bundling_options(),
            ),
            timeout=Duration.minutes(3),
            memory_size=512,
            environment={
                "S3_BUCKET": self.bucket.bucket_name,
            },
            vpc=vpc,
            initial_policy=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream",
                    ],
                    resources=[
                        f"arn:{Stack.of(self).partition}:bedrock:{Stack.of(self).region}::foundation-model/*",
                    ],
                )
            ],
            layers=layers,
        )
        self.bucket.grant_put(self.endpoint.function)

        cdk_nag.NagSuppressions.add_resource_suppressions_by_path(
            stack=Stack.of(self),
            path=self.node.path
            + "/Endpoint/Resource/ServiceRole/DefaultPolicy/Resource",
            suppressions=[
                cdk_nag.NagPackSuppression(
                    id="AwsSolutions-IAM5",
                    reason="Lambda is allowed to invoke bedrock model",
                    applies_to=[
                        f"Resource::arn:{Stack.of(self).partition}:bedrock:{Stack.of(self).region}::foundation-model/*",
                    ],
                ),
                cdk_nag.NagPackSuppression(
                    id="AwsSolutions-IAM5",
                    reason="Lambda is allowed to use given bucket",
                    applies_to=[
                        "Action::s3:Abort*",
                        "Resource::<DiagramToTextEndpointBucketFBE0DCD4.Arn>/*",
                    ],
                ),
                cdk_nag.NagPackSuppression(
                    id="AwsSolutions-IAM5",
                    reason="Labda is allowed to use KMS key to encrypt/decrypt files in S3",
                    applies_to=[
                        "Action::kms:GenerateDataKey*",
                        "Action::kms:ReEncrypt*",
                    ],
                ),
            ],
        )

    @property
    def function(self) -> aws_lambda.Function:
        return self.endpoint.function

    @property
    def security_group(self) -> ec2.SecurityGroup:
        return self.endpoint.security_group

    @property
    def url(self) -> str:
        return self.endpoint.function_url.url
