import logging
import json

import os
import pkgutil
from importlib import import_module

import boto3

from .data_structures import RDConfig, StateStorage
from .resource import ResourceDirectory

logger = logging.getLogger(__name__)


def scan():
    # in this initial version, lets make some assumptions about things and then
    # fix those later - specificlly like state files will be in an s3 bucket.

    # and that the client being used will be 'aws default' and the user will
    # be all setup to just work(tm)

    # Future JT will hate past JT for these assumptions.

    # Build scan map:
    config = RDConfig()
    rd = ResourceDirectory()

    _load_resource_modules()

    # Scan current repo

    if config.state_storage == StateStorage.AWS_S3:
        # Note we don't support mix & match state locations.
        # Message me if you do this. Because I'm interested as to why
        for state_folder in config.state_file_locations:
            logger.info("Inspecting %s" % state_folder)
            _s3_state_fetch(state_folder)
    else:
        raise NotImplementedError("State storage not implemented yet")

    # Extract items of interest from States:
    logger.info("Now Looking at AWS (via Boto)")

    report = {}

    scanned_elements = []

    for scan_element in config.elements_to_scan:
        scanning_elements = []
        scanned_elements = _real_scan_element(scan_element, scanned_elements, scanning_elements)
            
    # now compare
    
    compared_elements = []

    for scan_element in config.elements_to_scan:
        comparing_elements = []
        logger.info("Now comparing %s" % scan_element)

        compared_elements, report = _compare_element(scan_element, compared_elements, comparing_elements, report)

    logger.info("Scan Complete")
    return report


def _load_resource_modules():

    config = RDConfig()

    for (_, name, is_package) in pkgutil.walk_packages([os.path.join(os.path.dirname(__file__), "resources")]):
        if is_package:
            package_name = name
            for (_, name, _) in pkgutil.iter_modules(
                    [os.path.join(os.path.dirname(__file__), "resources", package_name)]):
                import_module('riffdog.resources.%s.%s' % (package_name, name))
        else:
            for (_, name, _) in pkgutil.iter_modules([os.path.join(os.path.dirname(__file__), "resources")]):
                import_module('riffdog.resources.%s' % name)

    # attempt to scan other projects
    logger.info("Looking for external modules")
    for project in config.external_resource_libs:
        try:
            imported = import_module("%s.register" % project)
            imported.register_resources()
        except Exception as e:
            #logger.info(e)
            logger.info("Exception loading %s - might not be installed, or errors on load" % project)


def _real_scan_element(scan_element, scanned, scanning):
    # FIXME: this is recursive - change to a loop at some point

    rd = ResourceDirectory()

    if scan_element in scanned:
        # its allready run, return
        return scanned

    if scan_element in scanning:
        raise Exception("Circular dependency found - code error in dependancy tree")

    scanning.append(scan_element)

    element = rd.lookup(scan_element)
    if element:
        for required_element in element.depends_on:
            if required_element not in scanned:
                scanned = _real_scan_element(required_element, scanned, scanning)

        element.fetch_real_resources()

    scanned.append(scan_element)
    return scanned


def _compare_element(scan_element, compared, comparing, report):
    # FIXME: this is recursive - change to a loop at some point

    rd = ResourceDirectory()

    if scan_element in compared:
        # its allready run, return
        return compared, report

    if scan_element in comparing:
        raise Exception("Circular dependency found - code error in dependancy tree")

    comparing.append(scan_element)

    element = rd.lookup(scan_element)
    if element:
        for required_element in element.depends_on:
            if required_element not in compared:
                compared, report = _compare_element(required_element, compared, comparing, report)

        report[scan_element] = element.compare(depth=None) # FIXME - depth calculation

    compared.append(scan_element)
    return compared, report


def _s3_state_fetch(bucket_name):
    """
    This function exists to fetch state files from S3
    """
    client = boto3.client('s3')
    s3 = boto3.resource('s3')

    logger.info("Processing bucket: %s" % bucket_name)

    items = client.list_objects(Bucket=bucket_name, Prefix="")


    for item in items['Contents']:
        # if item['Key'].endswith("terraform.tfstate"): # FIXME: in future how can we better identify these files?
        logging.info("Inspecting s3 item: %s" % item['Key'])
        _search_state(bucket_name, item['Key'], s3)



def _search_state(bucket_name, key, s3):
    obj = s3.Object(bucket_name, key)
    content = obj.get()['Body'].read()
    rd = ResourceDirectory()

    try:
        parsed = json.loads(content)

        for res in parsed['resources']:
            element = rd.lookup(res['type'])
            if element:
                element.process_state_resource(res, key)
            else:
                logging.debug("Unsupported resource %s" % res['type'])
           

    except Exception as e:
        # FIXME: tighten this up could be - file not Json issue, permission of s3 etc, as well as the terraform state
        # version has changed
        logger.info(e)
        logger.warning("Bad Terraform file: %s (perhaps a TF/state version issue?) %s" % (key, type(e)))
        pass
