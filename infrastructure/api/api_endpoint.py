from typing import Optional, List, Dict, Sequence

from aws_cdk import (
    aws_ec2 as ec2,
    aws_lambda,
    aws_iam as iam,
    Duration,
    BundlingOptions,
    Stack,
)
from constructs import Construct


class ApiEndpoint(Construct):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        code: aws_lambda.Code,
        vpc: ec2.IVpc,
        timeout: Optional[Duration] = None,
        memory_size: Optional[int] = None,
        security_groups: Optional[List[ec2.SecurityGroup]] = None,
        environment: Optional[Dict[str, str]] = None,
        initial_policy: Optional[Sequence[iam.PolicyStatement]] = None,
        layers: Optional[Sequence[aws_lambda.ILayerVersion]] = None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # env
        lwa_layer = aws_lambda.LayerVersion.from_layer_version_arn(
            self,
            "LambdaWebAdapterLayer",
            f"arn:aws:lambda:{Stack.of(self).region}:753240598075:layer:LambdaAdapterLayerArm64:23",
        )
        self.security_group = ec2.SecurityGroup(
            self, "SecurityGroup", vpc=vpc, allow_all_outbound=True
        )
        self.function = aws_lambda.Function(
            self,
            "Resource",
            code=code,
            handler="index.py",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            timeout=timeout,
            memory_size=memory_size,
            architecture=aws_lambda.Architecture.ARM_64,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            security_groups=[self.security_group, *(security_groups or [])],
            environment={
                **(environment or {}),
                "POWERTOOLS_LOG_LEVEL": "INFO",
                "AWS_LAMBDA_EXEC_WRAPPER": "/opt/bootstrap",
                "AWS_LWA_INVOKE_MODE": "response_stream",
            },
            layers=[
                lwa_layer,
                *(layers or []),
            ],
            initial_policy=initial_policy,
        )
        self.function_url = self.function.add_function_url(
            invoke_mode=aws_lambda.InvokeMode.RESPONSE_STREAM,
            auth_type=aws_lambda.FunctionUrlAuthType.AWS_IAM,
            cors=aws_lambda.FunctionUrlCorsOptions(
                allowed_origins=["*"],
                allowed_headers=[
                    "authorization",
                    "content-type",
                    "x-amz-date",
                    "x-amz-security-token",
                ],
                allowed_methods=[aws_lambda.HttpMethod.POST],
            ),
        )

    @staticmethod
    def bundling_options() -> BundlingOptions:
        return BundlingOptions(
            image=aws_lambda.Runtime.PYTHON_3_12.bundling_image,
            command=[
                "bash",
                "-c",
                " && ".join(
                    [
                        "pip install -r requirements.txt -t /asset-output",
                        "cp -a . /asset-output",
                        # lambda comes with preinstalled boto libraries - remove to save space
                        "rm -rf /asset-output/boto3 /asset-output/botocore /asset-output/requirements.txt",
                    ]
                ),
            ],
            platform="linux/arm64",
        )
