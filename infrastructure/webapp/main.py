from aws_cdk import (
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    RemovalPolicy,
    Stack,
    aws_wafv2 as wafv2,
)
import cdk_nag
from constructs import Construct

from ._cognito import _Cognito
from ._deployment import _Deployment


class WebApp(Construct):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        waf: wafv2.CfnWebACL,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        stack = Stack.of(self)

        logs = s3.Bucket(
            self,
            "Logs",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            enforce_ssl=True,
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY,
            access_control=s3.BucketAccessControl.LOG_DELIVERY_WRITE,
            server_access_logs_prefix="self/",
        )

        self.bucket = s3.Bucket(
            self,
            "Bucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            enforce_ssl=True,
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY,
            server_access_logs_bucket=logs,
            server_access_logs_prefix="origin/",
        )

        custom_domain = self.node.try_get_context("webapp-domain")
        custom_domain_certificate = None
        if custom_domain:
            custom_domain_certificate = (
                cloudfront.ViewerCertificate.from_acm_certificate(
                    self,
                    "CustomDomainCertificate",
                    self.node.get_context("webapp-certificate-arn"),
                )
            )

        self.distribution = cloudfront.Distribution(
            self,
            "Distribution",
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(
                    bucket=self.bucket,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                origin_request_policy=cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN,
                response_headers_policy=cloudfront.ResponseHeadersPolicy.CORS_ALLOW_ALL_ORIGINS_WITH_PREFLIGHT_AND_SECURITY_HEADERS,
            ),
            log_bucket=logs,
            log_file_prefix="cloudfront/",
            minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
            domain_names=custom_domain and [custom_domain] or None,
            certificate=custom_domain_certificate,
            web_acl_id=waf.attr_arn,
        )

        if not custom_domain:
            cdk_nag.NagSuppressions.add_resource_suppressions_by_path(
                stack,
                "/ThreatMitigationStack/WebApp/Distribution/Resource",
                [
                    cdk_nag.NagPackSuppression(
                        id="AwsSolutions-CFR4",
                        reason="Default Cloudfront viewer certificate is non-compliant with this rule",
                    )
                ],
            )

        self.cognito = _Cognito(
            self, "Cognito", redirect_url=f"https://{self.distribution.domain_name}"
        )

        _Deployment(
            self,
            "Deployment",
            destination_bucket=self.bucket,
            distribution=self.distribution,
        )
