"""
This module is for EC2 instance processing - terraform & boto and comparison.
"""

import logging

from ..data_structures import ReportElement
from ..resource import AWSResource, register

logger = logging.getLogger(__name__)


# FIXME: this should be def InstanceResource(Resource) but it messes the dynamic loading

@register("aws_instance")
class InstanceResource(AWSResource):

    _states_found = {}
    _real_servers = {}

    def fetch_real_regional_resources(self, region):
        client = self._get_client('ec2', region)

        instances = client.describe_instances()

        if instances:
            if len(instances["Reservations"]) > 0:
                vpcs = client.describe_vpcs()

            for reservation in instances["Reservations"]:
                for instance in reservation["Instances"]:
                    logger.debug(instance)
                    # VPC Name
                    vpc = ''
                    if "VpcId" in instance:
                        vpc = _get_VPC_name(client, instance["VpcId"], vpcs)
                    elif "State" in instance:
                        vpc = "N/A (" + instance["State"]["Name"] + ")"

                    image_id = instance["ImageId"]

                    name = "Unknown"
                    ips = ""
                    public = False
                    tags = {}

                    for tag in instance['Tags']:
                        if tag["Key"] == "Name":
                            name = tag["Value"]

                        else:
                            key = tag["Key"].replace(" ", "")
                            tags[key] = tag["Value"]

                    # IP calculation
                    for interface in instance["NetworkInterfaces"]:
                        if "Ipv6Addresses" in interface:
                            for address in interface["Ipv6Addresses"]:
                                ips += " %s" % address['Ipv6Address']

                        if 'PrivateIpAddresses' in interface:
                            for address in interface["PrivateIpAddresses"]:
                                ips += " %s" % address['PrivateIpAddress']

                        if 'Association' in interface:
                            public = True
                            ips += " %s" % interface["Association"]['PublicIp']

                    # Fix for output
                    external_desc = "External"
                    if not public:
                        external_desc = "Internal"

                    self._real_servers[instance['InstanceId']] = {
                        "name": name,
                        "image": image_id,
                        "ip_address": ips,
                        "external": external_desc,
                        "tags": tags,
                        "region": region,
                        "vpc": vpc,
                        "aws_id": instance["InstanceId"],
                        "original_boto": instance,
                    }

    def process_state_resource(self, state_resource, state_filename):
        for instance in state_resource['instances']:
            instance['state_filename'] = state_filename
            self._states_found[instance['attributes']['id']] = instance

    def compare(self, config, depth):
        # this function should be called once, take the local data and return
        # an array of result elements.
        out_report = ReportElement()

        for key, val in self._states_found.items():
            if key not in self._real_servers:
                out_report.in_tf_but_not_real.append(key)
            else:
                out_report.matched.append(key)

        for key, val in self._real_servers.items():
            if key not in self._states_found:
                out_report.in_real_but_not_tf.append(key)

        return out_report


def _get_VPC_name(client, vpc_id, vpcs=None):
    if vpcs is None:
        vpcs = client.describe_vpcs()

    for vpc_data in vpcs["Vpcs"]:
        if vpc_data["VpcId"] == vpc_id:
            if "Tags" in vpc_data:
                vpc_tags = vpc_data["Tags"]
                for vpc_tag in vpc_tags:
                    if vpc_tag["Key"] == "Name":
                        return vpc_tag["Value"]
    return ''
