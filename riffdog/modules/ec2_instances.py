"""
This module is for EC2 instance processing - terraform & boto and comparison.
"""

import logging

from ..utils import _get_client, _get_resource
from ..data_structures import ReportElement

logger = logging.getLogger(__name__)

def _tf_process_instances(instances, state_filename):
    #id = res['id']
    #pp = pprint.PrettyPrinter(indent=2)
    #pp.pprint(res)
    outs = {}
    #print("------")
    for instance in instances['instances']:
        #print("   > %s " % instance)
        instance['state_filename'] = state_filename
        outs[instance['attributes']['id']] = instance
        #print("   > %s " % instance['attributes']['id'])
    #print("------")
    return outs


def _boto_fetch_instances(region):
    client = _get_client('ec2', region)
    
    instances = client.describe_instances()

    #print(instances)

    servers = {}

    if instances:
        if(len(instances["Reservations"]) > 0):
            ec2 = _get_resource('ec2', region)
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
                applications = ""
                tags = {}

                tag_keys = [tag["Key"] for tag in instance["Tags"]]

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

                servers[instance['InstanceId']] = {
                    "name": name,
                    "image": image_id,
                    "ip_address": ips,
                    "external": external_desc,
                    "tags": tags,
                    "region": region,
                    "vpc": vpc,
                    "aws_id": instance["InstanceId"],
                    "original_boto":instance
                }

    return servers

    
def _compare_instances(tf_instances, boto_instances, config):
    #FIXME: lightweight scan now!

    out_report = ReportElement()

    tf_ids = tf_instances.keys()
    aws_ids = boto_instances.keys()

    for key, val in tf_instances.items():
        if key not in aws_ids:
            out_report.in_tf_but_not_aws.append(key)
        else:
            out_report.matched.append(key)

    for key, val in boto_instances.items():
        if key not in tf_ids:
            out_report.in_aws_but_not_tf.append(key)

    return out_report



def _get_VPC_name(client, vpc_id, vpcs=None):
    if vpcs is None:
        vpcs = client.describe_vpcs()

    for vpc_data in vpcs["Vpcs"]:
        if(vpc_data["VpcId"] == vpc_id):
            if "Tags" in vpc_data: 
                vpc_tags = vpc_data["Tags"]
                for vpc_tag in vpc_tags:
                    if vpc_tag["Key"] == "Name":
                        return vpc_tag["Value"]
    return ''
