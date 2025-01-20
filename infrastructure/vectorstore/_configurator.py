import os

import cdk_nag
from aws_cdk import (
    aws_ec2 as ec2,
    aws_lambda,
    aws_rds as rds,
    aws_iam as iam,
    Duration,
    aws_logs as logs,
    custom_resources as cr,
    CustomResource,
    Stack,
)
from enum import StrEnum
from constructs import Construct


class _VectorStoreUserRole(StrEnum):
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"


class _VectorStoreConfigurator(Construct):

    _read_only_users = []
    _read_write_users = []

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.IVpc,
        database: rds.DatabaseCluster,
        database_name: str,
        layer: aws_lambda.LayerVersion,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self._database = database
        self._database_name = database_name

        sg = ec2.SecurityGroup(self, "SecurityGroup", vpc=vpc)

        self.function = aws_lambda.Function(
            self,
            "Resource",
            code=aws_lambda.Code.from_asset(
                os.path.join(
                    os.path.dirname(os.path.realpath(__file__)),
                    "_configurator_custom_resource_lambda",
                ),
            ),
            handler="index.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.minutes(1),
            memory_size=512,
            architecture=aws_lambda.Architecture.ARM_64,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
            ),
            layers=[layer],
            security_groups=[sg],
            environment={
                "DB_SECRET": database.secret.secret_arn,
                "DB_HOST": database.cluster_endpoint.hostname,
            },
        )

        database.secret.grant_read(self.function)
        database.connections.allow_from(
            ec2.Peer.security_group_id(sg.security_group_id),
            ec2.Port.tcp(5432),
        )
        configurator_custom_resource_role = iam.Role(
            self,
            "CustomResourceRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaVPCAccessExecutionRole"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )
        self.function.grant_invoke(configurator_custom_resource_role)
        cdk_nag.NagSuppressions.add_resource_suppressions_by_path(
            stack=Stack.of(self),
            path=self.node.path + "/CustomResourceRole/DefaultPolicy/Resource",
            suppressions=[
                cdk_nag.NagPackSuppression(
                    id="AwsSolutions-IAM5",
                    reason="Custom resource lambda is allowed to invoke target lambda",
                )
            ],
            apply_to_children=True,
        )

        self._provider = cr.Provider(
            self,
            "Provider",
            on_event_handler=self.function,
            log_retention=logs.RetentionDays.INFINITE,
            role=configurator_custom_resource_role,
        )

        # ensure custom resource will be executed after the database is ready
        self._provider.node.add_dependency(database)
        self.custom_resource_initialized = CustomResource(
            self,
            "CustomResource",
            service_token=self._provider.service_token,
            properties={
                "host": database.cluster_endpoint.hostname,
                "database": database_name,
                "secret": database.secret.secret_arn,
            },
        )
        self.custom_resource_initialized.node.add_dependency(self.function)

    def _grant_access(
        self,
        grantee: iam.IGrantable,
        security_group: ec2.SecurityGroup,
        username: str,
        role: _VectorStoreUserRole,
    ):
        self._database.connections.allow_from(
            ec2.Peer.security_group_id(security_group.security_group_id),
            ec2.Port.tcp(5432),
        )
        self._database.grant_connect(grantee, username)
        custom_res = CustomResource(
            self,
            f"CustomResourceForUser_{username}",
            service_token=self._provider.service_token,
            properties={
                "host": self._database.cluster_endpoint.hostname,
                "database": self._database_name,
                "secret": self._database.secret.secret_arn,
                "username": username,
                "role": role,
            },
        )
        custom_res.node.add_dependency(self.custom_resource_initialized)
        custom_res.node.add_dependency(self.function)

    def grant_read_only_access(
        self, grantee: iam.IGrantable, security_group: ec2.SecurityGroup, username: str
    ):
        self._grant_access(
            grantee, security_group, username, _VectorStoreUserRole.READ_ONLY
        )

    def grant_read_write_access(
        self, grantee: iam.IGrantable, security_group: ec2.SecurityGroup, username: str
    ):
        self._grant_access(
            grantee, security_group, username, _VectorStoreUserRole.READ_WRITE
        )
