from aws_cdk import (
    Stack,
    CfnOutput,
    aws_s3 as s3,
    RemovalPolicy,
    aws_ec2 as ec2,
    aws_wafv2 as wafv2,
)
from constructs import Construct
from .api.summary_to_threat_model import SummaryToThreatModel
from .api.diagram_to_text import DiagramToText
from .vectorstore import VectorStore
from .webapp.main import WebApp


class ThreatMitigationStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.Vpc,
        waf: wafv2.CfnWebACL,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        database_name = self.node.try_get_context("database-name") or "vectorstore"
        access_log_bucket = s3.Bucket(
            self,
            "AccessLogBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY,
            server_access_logs_prefix="self/",
        )

        vectorstore = VectorStore(
            self,
            "VectorStore",
            vpc=vpc,
            database_name=database_name,
            s3_access_logs_bucket=access_log_bucket,
            s3_access_logs_prefix="vectorstore-access-logs/",
        )

        summary_to_threat_model_username = "summary_to_threat_model"
        summary_to_threat_model = SummaryToThreatModel(
            self,
            "SummaryToThreatModelEndpoint",
            database_username=summary_to_threat_model_username,
            database_name=database_name,
            database_hostname=vectorstore.hostname,
            vpc=vpc,
            layers=[vectorstore.layer],
            s3_access_logs_bucket=access_log_bucket,
            s3_access_logs_prefix="summary-to-threat-model-endpoint-access-logs/",
        )
        vectorstore.grant_read_only_access(
            summary_to_threat_model.function,
            summary_to_threat_model.security_group,
            summary_to_threat_model_username,
        )

        diagram_to_text = DiagramToText(
            self,
            "DiagramToTextEndpoint",
            vpc=vpc,
            layers=[vectorstore.layer],
            s3_access_logs_bucket=access_log_bucket,
            s3_access_logs_prefix="diagram-to-text-endpoint-access-logs/",
        )

        webapp = WebApp(
            self,
            "WebApp",
            waf=waf,
        )

        diagram_to_text.function.grant_invoke_url(webapp.cognito.authenticated_role)
        summary_to_threat_model.function.grant_invoke_url(
            webapp.cognito.authenticated_role
        )

        CfnOutput(
            self,
            "VectorStoreDocumentsBucket",
            value=vectorstore.documents_bucket.bucket_name,
        )
        CfnOutput(self, "WebAppUrl", value=webapp.distribution.domain_name)

        CfnOutput(
            self,
            "WebAppEnvironment",
            value=Stack.of(self).to_json_string(
                {
                    "VITE_APP_AWS_REGION": Stack.of(self).region,
                    "VITE_APP_USER_POOL_ID": webapp.cognito.user_pool.user_pool_id,
                    "VITE_APP_USER_POOL_CLIENT_ID": webapp.cognito.client.user_pool_client_id,
                    "VITE_APP_COGNITO_DOMAIN": f"{webapp.cognito.domain.domain_name}.auth.{Stack.of(self).region}.amazoncognito.com",
                    "VITE_APP_IDENTITY_POOL_ID": webapp.cognito.identity_pool.ref,
                    "VITE_APP_REDIRECT_SIGN_IN_URL": f"https://{webapp.distribution.domain_name}",
                    "VITE_APP_REDIRECT_SIGN_OUT_URL": f"https://{webapp.distribution.domain_name}",
                    "VITE_APP_ENDPOINT_DIAGRAM_TO_TEXT": diagram_to_text.url,
                    "VITE_APP_ENDPOINT_SUMMARY_TO_THREAT_MODEL": summary_to_threat_model.url,
                }
            ),
        )
