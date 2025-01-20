from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
)
from constructs import Construct


class NetworkStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc(
            self,
            "Resource",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            nat_gateways=0,
            max_azs=2,
            create_internet_gateway=True,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            gateway_endpoints={
                "s3": ec2.GatewayVpcEndpointOptions(
                    service=ec2.GatewayVpcEndpointAwsService.S3
                )
            },
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="private",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
        )
        self.vpc.add_flow_log(
            "FlowLogCloudWatch",
            traffic_type=ec2.FlowLogTrafficType.REJECT,
            max_aggregation_interval=ec2.FlowLogMaxAggregationInterval.ONE_MINUTE,
        )

        self.interface_endpoints = {}
        for service in [
            ec2.InterfaceVpcEndpointAwsService.KMS,
            ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
            ec2.InterfaceVpcEndpointAwsService.RDS,
            ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
            ec2.InterfaceVpcEndpointAwsService.BEDROCK_RUNTIME,
        ]:
            endpoint = self.vpc.add_interface_endpoint(
                service.short_name, service=service, private_dns_enabled=True
            )
            self.interface_endpoints[service.short_name] = endpoint
