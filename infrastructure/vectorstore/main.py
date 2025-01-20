from aws_cdk import (
    aws_ec2 as ec2,
    aws_kms as kms,
    aws_rds as rds,
    aws_iam as iam,
    aws_s3 as s3,
    aws_lambda,
    RemovalPolicy,
    Duration,
    Names,
)
from constructs import Construct
from ._configurator import _VectorStoreConfigurator
from ._document_loader import _VectorStoreDocumentLoader
from ._layer import _VectorStoreLayer


class VectorStore(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.IVpc,
        database_name: str,
        s3_access_logs_bucket: s3.IBucket,
        s3_access_logs_prefix: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self._database_name = database_name
        document_loader_username = "document_loader_" + Names.unique_id(self)
        kms_key = kms.Key(
            self,
            "KmsKey",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.DESTROY,
        )
        self.db = rds.DatabaseCluster(
            self,
            "Resource",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_15_5,
            ),
            writer=rds.ClusterInstance.serverless_v2("writer"),
            serverless_v2_min_capacity=0.5,
            serverless_v2_max_capacity=10,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
            ),
            default_database_name=database_name,
            enable_data_api=True,
            iam_authentication=True,
            storage_encrypted=True,
            storage_encryption_key=kms_key,
            deletion_protection=True,
            removal_policy=RemovalPolicy.DESTROY,
        )
        self.db.add_rotation_single_user(automatically_after=Duration.days(30))
        self.layer = _VectorStoreLayer(self, "Layer").layer

        self._configurator = _VectorStoreConfigurator(
            self,
            "Configurator",
            vpc=vpc,
            database=self.db,
            database_name=database_name,
            layer=self.layer,
        )
        self._document_loader = _VectorStoreDocumentLoader(
            self,
            "DocumentLoader",
            vpc=vpc,
            database=self.db,
            database_name=database_name,
            database_username=document_loader_username,
            layer=self.layer,
            s3_access_logs_bucket=s3_access_logs_bucket,
            s3_access_logs_prefix=s3_access_logs_prefix,
        )
        self._configurator.grant_read_write_access(
            self._document_loader.function,
            self._document_loader.security_group,
            document_loader_username,
        )

        # do configure DB before creating a bucket
        self._document_loader.bucket.node.add_dependency(
            self._configurator.custom_resource_initialized
        )

    def grant_read_only_access(
        self, grantee: iam.IGrantable, security_group: ec2.SecurityGroup, username: str
    ):
        return self._configurator.grant_read_only_access(
            grantee, security_group, username
        )

    def grant_read_write_access(
        self, grantee: iam.IGrantable, security_group: ec2.SecurityGroup, username: str
    ):
        return self._configurator.grant_read_write_access(
            grantee, security_group, username
        )

    @property
    def hostname(self):
        return self.db.cluster_endpoint.hostname

    @property
    def port(self):
        return self.db.cluster_endpoint.port

    @property
    def database_name(self):
        return self._database_name

    @property
    def documents_bucket(self):
        return self._document_loader.bucket
