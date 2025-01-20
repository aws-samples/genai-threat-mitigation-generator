import os
import cdk_nag
from aws_cdk import (
    aws_ec2 as ec2,
    aws_s3 as s3,
    aws_kms as kms,
    aws_s3_notifications as s3_notifications,
    aws_lambda,
    aws_rds as rds,
    aws_iam as iam,
    Duration,
    RemovalPolicy,
    Stack,
    BundlingOptions,
)
from constructs import Construct


class _VectorStoreDocumentLoader(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        database: rds.DatabaseCluster,
        database_username: str,
        database_name: str,
        vpc: ec2.Vpc,
        layer: aws_lambda.LayerVersion,
        s3_access_logs_bucket: s3.Bucket,
        s3_access_logs_prefix: str,
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
        self.security_group = ec2.SecurityGroup(
            self,
            "SecurityGroup",
            vpc=vpc,
        )
        self.function = aws_lambda.Function(
            self,
            "Resource",
            code=aws_lambda.Code.from_asset(
                os.path.join(
                    os.path.dirname(os.path.realpath(__file__)),
                    "_document_loader_lambda",
                ),
                bundling=BundlingOptions(
                    command=[
                        "bash",
                        "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -a . /asset-output",
                    ],
                    image=aws_lambda.Runtime.PYTHON_3_12.bundling_image,
                    platform="linux/arm64",
                ),
            ),
            handler="index.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.minutes(1),
            memory_size=512,
            architecture=aws_lambda.Architecture.ARM_64,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            layers=[layer],
            security_groups=[self.security_group],
            environment={
                "BUCKET_NAME": self.bucket.bucket_name,
                "DB_NAME": database_name,
                "DB_USER": database_username,
                "DB_HOST": database.cluster_endpoint.hostname,
                "DB_PORT": str(database.cluster_endpoint.port),
            },
        )
        self.bucket.grant_read(self.function)
        self.bucket.grant_delete(self.function)
        self.function.add_to_role_policy(
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
        )
        self.bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3_notifications.LambdaDestination(self.function),
        )

        cdk_nag.NagSuppressions.add_resource_suppressions_by_path(
            stack=Stack.of(self),
            path=self.node.path + "/Resource/ServiceRole/DefaultPolicy/Resource",
            suppressions=[
                cdk_nag.NagPackSuppression(
                    id="AwsSolutions-IAM5",
                    reason="Lambda is allowed to manage objects in given bucket",
                    applies_to=[
                        "Action::s3:GetBucket*",
                        "Action::s3:GetObject*",
                        "Action::s3:DeleteObject*",
                        "Action::s3:List*",
                        "Resource::<VectorStoreDocumentLoaderBucket8B615062.Arn>/*",
                    ],
                ),
                cdk_nag.NagPackSuppression(
                    id="AwsSolutions-IAM5",
                    reason="Lambda is allowed to invoke bedrock model",
                    applies_to=[
                        f"Resource::arn:{Stack.of(self).partition}:bedrock:{Stack.of(self).region}::foundation-model/*",
                    ],
                ),
            ],
        )
