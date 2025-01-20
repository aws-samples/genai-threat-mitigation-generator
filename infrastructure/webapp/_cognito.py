from typing import Optional, List, Dict, Sequence

from aws_cdk import (
    aws_ec2 as ec2,
    aws_lambda,
    aws_iam as iam,
    Duration,
    DockerImage,
    BundlingOptions,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cognito as cognito,
    aws_cloudfront_origins as origins,
    aws_kms as kms,
    aws_s3_deployment as s3_deployment,
    RemovalPolicy,
    Names,
)
from constructs import Construct


class _Cognito(Construct):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        redirect_url: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.user_pool = cognito.UserPool(
            self,
            "Resource",
            self_sign_up_enabled=False,
            account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            standard_attributes=cognito.StandardAttributes(
                email=cognito.StandardAttribute(
                    required=True,
                    mutable=True,
                )
            ),
            password_policy=cognito.PasswordPolicy(
                min_length=12,
                require_digits=True,
                require_lowercase=True,
                require_uppercase=True,
                require_symbols=True,
            ),
            advanced_security_mode=cognito.AdvancedSecurityMode.ENFORCED,
            removal_policy=RemovalPolicy.DESTROY,
        )
        cognito_domain = self.node.try_get_context("webapp-cognito-domain")
        self.domain = self.user_pool.add_domain(
            "UserPoolDomain",
            cognito_domain=(
                None
                if cognito_domain
                else cognito.CognitoDomainOptions(
                    domain_prefix=self.node.get_context("webapp-cognito-domain-prefix")
                )
            ),
            custom_domain=(
                cognito.CustomDomainOptions(
                    domain_name=cognito_domain,
                    certificate_arn=self.node.get_context(
                        "webapp-cognito-certificate-arn"
                    ),
                )
                if cognito_domain
                else None
            ),
        )

        self.client = cognito.UserPoolClient(
            self,
            "UserPoolClient",
            user_pool=self.user_pool,
            generate_secret=False,
            auth_flows=cognito.AuthFlow(
                user_password=True,
            ),
            o_auth=cognito.OAuthSettings(
                callback_urls=[redirect_url],
                logout_urls=[redirect_url],
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                ),
                scopes=[
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.PROFILE,
                    cognito.OAuthScope.OPENID,
                ],
            ),
            prevent_user_existence_errors=True,
        )

        self.identity_pool = cognito.CfnIdentityPool(
            self,
            "IdentityPool",
            allow_unauthenticated_identities=False,
            cognito_identity_providers=[
                cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
                    client_id=self.client.user_pool_client_id,
                    provider_name=self.user_pool.user_pool_provider_name,
                )
            ],
        )

        self.authenticated_role = iam.Role(
            self,
            "CognitoDefaultAuthenticatedRole",
            assumed_by=iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                {
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": self.identity_pool.ref,
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "authenticated",
                    },
                },
                "sts:AssumeRoleWithWebIdentity",
            ),
        )

        cognito.CfnIdentityPoolRoleAttachment(
            self,
            "IdentityPoolRoleAttachment",
            identity_pool_id=self.identity_pool.ref,
            roles={"authenticated": self.authenticated_role.role_arn},
        )
