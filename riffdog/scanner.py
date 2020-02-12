import logging 
import json

import boto3

from .modules.ec2_instances import _tf_process_instances, _boto_fetch_instances, _compare_instances

from .data_structures import ScanMode, StateStorage, RDConfig, ReportElement 

logger = logging.getLogger(__name__)


# This is the list of things we don't support yet (at a minimum)
_ignore_types = (
                'aws_nat_gateway', 'aws_main_route_table_association', 'aws_internet_gateway', 
                'aws_kms_key', 'aws_elasticsearch_domain', 'aws_iam_role', 'aws_db_subnet_group', 
                'aws_alb_listener', 'aws_alb_target_group', 'aws_alb_target_group_attachment',
                'aws_iam_policy_document', 'aws_elb_service_account', 'cloudflare_ip_ranges', 
                'aws_s3_bucket_policy', 'aws_alb_listener_rule', 'aws_lb_listener_certificate',
                'aws_route', 'aws_route_table_association', 'aws_default_network_acl', 'aws_elb_attachment',
                'aws_ebs_volume', 'aws_iam_instance_profile', 'aws_iam_role_policy_attachment',
                'aws_volume_attachment', 'aws_dynamodb_table', 'aws_iam_policy', 'aws_iam_policy_attachment'
                'aws_default_route_table', 'aws_lb_listener', 'aws_lb_listener_rule', 
                'aws_lb_target_group', 'aws_lb_target_group_attachment', 
                'aws_customer_gateway', 'aws_vpn_connection', 'aws_vpn_gateway', 
                'aws_iam_role_policy', 'aws_iam_service_linked_role', 
                'aws_lb_listener_certificate', 'aws_s3_bucket_notification', 'aws_ecr_repository',
                'aws_iam_policy_attachment', 'aws_default_route_table', 'aws_sqs_queue_policy'
               )

_scan_map = {
    'aws_instance': { 'aws_scan_func': _boto_fetch_instances, 'compare_func': _compare_instances }
}




def scan(config):

    # in this initial version, lets make some assumptions about things and then
    # fix those later - specificlly like state files will be in an s3 bucket.

    # and that the client being used will be 'aws default' and the user will
    # be all setup to just work(tm)

    # Future JT will hate past JT for these assumptions.

    items = _get_blank_state_dict()

    if config.state_storage == StateStorage.AWS_S3:
        # Note we don't support mix & match state locations.
        # Message me if you do this. Becuase I'm interested as to why
        for state_folder in config.state_file_locations:
            logger.info("Inspecting %s" % state_folder)
            new_items = _s3_state_fetch(state_folder)
            
            for key, val in items.items():
                logger.info("Adding %s items of type %s" % (len(new_items[key]), key))
                val.update(new_items[key])

    else:
        raise NotImplemented("State storage not implemented yet")

    # Extract items of interest from States:
    logger.info("Total items found:")
    for key, val in items.items():
        logger.info("%s:\t%s" % (key, len(val)))


    logger.info("Now Looking at AWS (via Boto)")

    report = {}

    for scan_element in config.elements_to_scan:
        logger.info("Now inspecting %s" % scan_element)
        real_items = {}
        for region in config.regions:
            real_items.update(_scan_map[scan_element]['aws_scan_func'](region))
            
        report[scan_element] = _scan_map[scan_element]['compare_func'](items[scan_element], real_items, config)


    logger.info("Scan Complete")
    return report

def _get_blank_state_dict():
    return {
        "aws_instance": {},
        "buckets": {},
        "rds": {}
    }

def _s3_state_fetch(bucket_name):
    """
    This function exists to fetch state files from S3
    """

    client = boto3.client('s3')
    s3 = boto3.resource('s3')

    logger.info("Processing bucket: %s" % bucket_name)

    items = client.list_objects(Bucket=bucket_name, Prefix="")
    
    total = _get_blank_state_dict()

    for item in items['Contents']:
        found = None
        #print(item['Key'])
        if item['Key'].endswith("terraform.tfstate"):
            found = search_state(bucket_name, item['Key'], s3)

            for key, val in total.items():
                val.update(found[key])

    # instances
    return total


def search_state(bucket_name, key, s3):
    obj = s3.Object(bucket_name, key)
    content = obj.get()['Body'].read()
    parsed = json.loads(content)

    outs = _get_blank_state_dict()

    unknowns = []

    try:
        for res in  parsed['resources']:
            #print(res['type'])
            if res['type'] in _ignore_types or not res['type'].startswith('aws_'):
                # ignore known
                pass

            elif res['type'] == "aws_instance":
                found = _tf_process_instances(res, key)
                outs['aws_instance'].update(found)

            elif res['type']=="aws_s3_bucket":
                found = _process_s3(res, key)
                outs['buckets'].update(found)
            elif res['type'] == "aws_sqs_queue":
                # FIXME: write queue scanner
                pass
            elif res['type'] == "aws_alb":
                # FIXME: write Alb scanner
                pass
            elif res['type'] == "aws_elb":
                # FIXME: write elb 
                pass
            elif res['type'] == "aws_lb":
                # FIXME: classic lb
                pass
            elif res['type'] == "aws_security_group":
                # FIXME: write security group scanner
                pass
            elif res['type'] == 'aws_security_group_rule':
                # FIXME: write this?
                pass
            elif res['type'] == 'aws_subnet':
                # FIXME: write subnet scanner
                pass
            elif res['type'] == 'aws_vpc':
                # FIXME: write vpc scanner
                pass
            elif res['type'] == 'aws_route_table':
                # FIXME: write routetable scanner
                # might not be relevant
                pass
            elif res['type'] == 'aws_vpc_peering_connection':
                # FIXME: write vpc peering conenction scanner
                pass
            elif res['type'] == 'aws_eip':
                # FIXME: write eip scanner
                pass
            elif res['type'] == 'aws_network_interface':
                # FIXME: nework interface
                pass
            elif res['type'] == 'aws_rds_cluster':
                # RDS Cluster
                pass
            elif res['type'] == 'aws_rds_cluster_instance':
                # RDS cluster instance
                pass
            else:
                # warn on unknown types
                if res['type'] not in unknowns:
                    unknowns.append(res['type'])
                
        if len(unknowns) > 0:
            unknown_str = ""
            for unknown in unknowns:
                unknown_str += ", %s" % unknown
        
            logger.warning("The following elements were unknown " + unknown_str)

    except Exception as e:
        logger.warning("Bad Terraform file: %s (perhaps a TF/state version issue?) %s" % (key, type(e)))
        pass

    return outs

def _process_s3(s3, state_filename):
    
    outs = {}
    for bucket in s3['instances']:
        #print(bucket)
        outs[bucket['bucket']] = bucket

    return outs

