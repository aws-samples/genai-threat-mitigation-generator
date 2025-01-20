import os
from aws_cdk import (
    Duration,
    DockerImage,
    BundlingOptions,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_s3_deployment as s3_deployment,
    Annotations,
    ILocalBundling,
)
import jsii
import subprocess
from constructs import Construct


@jsii.implements(ILocalBundling)
class LocalNodeBundler:
    def try_bundle(self, output_dir, options):
        try:
            subprocess.run(["npm", "install"], cwd="webapp", check=True)
            subprocess.run(["npm", "run", "build"], cwd="webapp", check=True)
            subprocess.run(["mkdir", "-p", output_dir], cwd="webapp", check=True)
            subprocess.run(["cp", "-a", "build/", output_dir], cwd="webapp", check=True)
            return True
        except:
            return False


class _Deployment(Construct):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        destination_bucket: s3.Bucket,
        distribution: cloudfront.Distribution,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        enforce_local_bundling = (
            self.node.try_get_context("webapp-enforce-local-bundling") == "true"
        )

        env_exists = os.path.exists("webapp/.env")
        if not env_exists:
            Annotations.of(self).add_warning(
                "No .env file found in webapp directory. "
                "Deploy stack and run following command to create .env "
                """aws cloudformation describe-stacks --stack-name ThreatMitigationStack  | jq '.Stacks[0].Outputs[] | select(.OutputKey == "WebAppEnvironment") | .OutputValue | fromjson | to_entries[] | [.key,.value] | join("=")' --raw-output > webapp/.env"""
            )
        else:
            s3_deployment.BucketDeployment(
                self,
                "Deployment",
                sources=[
                    s3_deployment.Source.asset(
                        path="webapp",
                        bundling=BundlingOptions(
                            entrypoint=["/bin/sh", "-c"],
                            command=[
                                "npm install && npm run build && cp -a ./build/* /asset-output"
                            ],
                            image=DockerImage.from_registry("node:lts-alpine"),
                            local=(
                                LocalNodeBundler() if enforce_local_bundling else None
                            ),
                        ),
                    )
                ],
                destination_bucket=destination_bucket,
                cache_control=[
                    s3_deployment.CacheControl.max_age(Duration.days(1)),
                ],
                distribution=distribution,
            )
