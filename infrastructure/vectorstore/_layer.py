import os

from aws_cdk import (
    aws_lambda,
    BundlingOptions,
)
from constructs import Construct

bundling_options = BundlingOptions(
    image=aws_lambda.Runtime.PYTHON_3_12.bundling_image,
    command=[
        "bash",
        "-c",
        " && ".join(
            [
                "pip install -r requirements.txt -t /asset-output/python",
                "cp -a . /asset-output/python",
                # lambda comes with preinstalled boto libraries - remove to save space
                "rm -r /asset-output/python/boto3 /asset-output/python/botocore",
            ]
        ),
    ],
    platform="linux/arm64",
)


class _VectorStoreLayer(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.layer = aws_lambda.LayerVersion(
            self,
            "layer",
            code=aws_lambda.Code.from_asset(
                os.path.join(os.path.dirname(os.path.realpath(__file__)), "_layer"),
                bundling=bundling_options,
            ),
        )
