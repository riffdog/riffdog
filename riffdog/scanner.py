import logging 
import json

import os
import sys
import inspect
import pkgutil
from pathlib import Path
from importlib import import_module

import boto3

#from .modules.ec2_instances import _tf_process_instances, _boto_fetch_instances, _compare_instances

from .data_structures import ScanMode, StateStorage, RDConfig, ReportElement 
from .resource import ResourceDirectory

logger = logging.getLogger(__name__)




def scan(config):

    # in this initial version, lets make some assumptions about things and then
    # fix those later - specificlly like state files will be in an s3 bucket.

    # and that the client being used will be 'aws default' and the user will
    # be all setup to just work(tm)

    # Future JT will hate past JT for these assumptions.

    # Build scan map:
    rd = ResourceDirectory()

    for (_, name, _) in pkgutil.iter_modules([os.path.join(os.path.dirname(__file__),"resources")]):
        imported_module = import_module('riffdog.resources.%s' % name)


    if config.state_storage == StateStorage.AWS_S3:
        # Note we don't support mix & match state locations.
        # Message me if you do this. Becuase I'm interested as to why
        for state_folder in config.state_file_locations:
            logger.info("Inspecting %s" % state_folder)
            found = _s3_state_fetch(state_folder)

    else:
        raise NotImplemented("State storage not implemented yet")

    # Extract items of interest from States:


    logger.info("Now Looking at AWS (via Boto)")

    report = {}

    for scan_element in config.elements_to_scan:
        logger.info("Now inspecting %s" % scan_element)

        # DISCUSS: hope they're all registered! - also? is this still relevant 
        
        if not scan_element in found:
            found[scan_element] = rd.lookup(scan_element)() # put a blank one in
        
        for region in config.regions:
            found[scan_element].fetch_real_resources(region)
    
        # now compare
        report[scan_element] =  found[scan_element].compare(config, None) # FIME - set depth

    logger.info("Scan Complete")
    return report


def _s3_state_fetch(bucket_name):
    """
    This function exists to fetch state files from S3
    """

    client = boto3.client('s3')
    s3 = boto3.resource('s3')

    logger.info("Processing bucket: %s" % bucket_name)

    items = client.list_objects(Bucket=bucket_name, Prefix="")
    
    found = {}

    for item in items['Contents']:
        #if item['Key'].endswith("terraform.tfstate"): # FIXME: in future how can we better identify these files?
        logging.info("Inspecting s3 item: %s" % item['Key'])
        found = _search_state(bucket_name, item['Key'], s3, found)

    # instances
    return found


def _search_state(bucket_name, key, s3, found):
    obj = s3.Object(bucket_name, key)
    content = obj.get()['Body'].read()
    rd = ResourceDirectory()
        
    try:
        parsed = json.loads(content)

        for res in parsed['resources']:
            if res['type'] in found:
                # its already loaded!
                logging.debug("Resource Matched Existing %s" % res['type'])
                found[res['type']].process_state_resource(res, key)
            else:
                func = rd.lookup(res['type'])
                if func:
                    logging.debug("Resource Matched %s - creating" % res['type'])
                    found[res['type']] = func()
                    found[res['type']].process_state_resource(res, key)
                else:
                    logging.debug("Unsupported resource %s" % res['type'])


    except Exception as e: # FIXME: tighten this up could be - file not Json issue, permission of s3 etc, as well as the terraform state version has changed
        logger.info(e)
        logger.warning("Bad Terraform file: %s (perhaps a TF/state version issue?) %s" % (key, type(e)))
        pass

    return found 


