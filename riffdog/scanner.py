import logging
import json

import os
import pkgutil
from importlib import import_module

from .config import RDConfig, StateStorage
from .resource import ResourceDirectory
from .exceptions import ResourceNotFoundError, StorageNotImplemented

try:
    import boto3
    BOTO_INSTALLED=True
except Exception:
    BOTO_INSTALLED=False


NO_FOUND_RESOURCES_ERROR = "No resource modules found. Please pip install riffdog_aws/riffdog_cloudflare"
STORAGE_NOT_IMPLEMENTED_ERROR = "State storage not implemented yet"
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

    if not rd.found_resources:
        raise ResourceNotFoundError(NO_FOUND_RESOURCES_ERROR)

    # Note we don't support mix & match state locations.
    # Message me if you do this. Because I'm interested as to why

    if config.state_storage == StateStorage.AWS_S3:

        if BOTO_INSTALLED:
            for state_folder in config.state_file_locations:
                _s3_inspector(state_folder)
        else:
            logger.error("Used -b option, but boto not installed - try doing `pip install boto3` to enable")

    elif config.state_storage == StateStorage.FILE:
        for state_folder in config.state_file_locations:
            _disk_inspector(state_folder)
    else:
        raise StorageNotImplemented(STORAGE_NOT_IMPLEMENTED_ERROR)

    # Extract items of interest from States:
    logger.info("Now Looking at AWS (via Boto)")

    scanned_elements = []

    for scan_element in config.elements_to_scan:
        scanning_elements = []
        scanned_elements = _real_scan_element(scan_element, scanned_elements, scanning_elements)
            
    # now compare

    # This is now different now - 0.1 upwards RC
    _compare(rd._items, config.scan_mode) # FIXME - accessing internal object

    logger.info("Scan Complete")


def _compare(items, scan_mode):

    rd = ResourceDirectory()

    for item in items:
        if item.matched:
            element = rd.lookup(item.item_type)
            try:
                element.compare(item, scan_mode)
                # element won't be none at this point, if it is, fatal error because someone bugged
            except Exception as e:
                logger.info(e)
                logger.info("%s comparison failed for item %s " % (item.item_type, item))


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
            logger.info("Loading modules from %s" % project)
            imported = import_module("%s.register" % project)
            imported.register_resources()
        except Exception as e:
            logger.info(e)
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
                logger.info("Lookging for %s resources in real world" % required_element)
                scanned = _real_scan_element(required_element, scanned, scanning)

        element.fetch_real_resources()

    scanned.append(scan_element)
    return scanned

def _disk_inspector(state_location):
    logger.info("File State Inspecting %s" % state_location)

    target = state_location

    if os.path.exists(target):
        if os.path.isdir(target):
            # get directories
            for root, dirs, files in os.walk(target):
                for filename in files:
                    _file_inspector("%s%s" % (state_location,filename))

                for direc in dirs:
                    _disk_inspector("%s/%s/" % (state_location, direc))

        if os.path.isfile(target):
            _file_inspector(target)
    else:
        logger.warning("Location %s does not seem to exist" % state_location)
    pass

def _file_inspector(filename):
    logger.info("Reading %s" % filename )
    try:
        with open(filename, 'r') as content_file:
            content = content_file.read()
        _search_state(filename, content)
    except Exception as e:
        # could be permission, bad file format, anything
        logger.warn("Failed to read file - maybe not a state file for reason: %s" % e)



def _s3_inspector(state_location):
    
    logger.info("S3 State Inspecting %s" % state_location)
    parts = state_location.split("/",1)
    if len(parts) > 1:
        if parts[1].endswith("/"):
            # Fun Fact - Techincally keys can end in a / but lets assume the user isnt trying 
            # to be awkward. - if anyone hits this, we will need to implement some kind of prefix
            # marker so we know its a prefix or not.
            _s3_state_fetch(parts[0], prefix=parts[1])
        else:
            _search_s3_state(parts[0], parts[1])
    else:
        _s3_state_fetch(state_location)


def _s3_state_fetch(bucket_name, prefix=""):
    """
    This function exists to locate state files from S3
    """
    client = boto3.client('s3')

    logger.info("Processing bucket: %s" % bucket_name)

    items = client.list_objects(Bucket=bucket_name, Prefix=prefix)

    # _search_state(bucket_name, "sandbox_main/services/django_lambda_test/terraform.tfstate", s3)

    for item in items.get('Contents', []):
        if item['Key'].endswith("terraform.tfstate"): # FIXME: in future how can we better identify these files?
            _search_s3_state(bucket_name, item['Key'])


def _search_s3_state(bucket_name, key):
    logging.info("processing s3 file: %s" % key)

    s3 = boto3.resource('s3')

    obj = s3.Object(bucket_name, key)
    content = obj.get()['Body'].read()

    _search_state(key, content)


def _search_state(filename, content):

    rd = ResourceDirectory()
    config = RDConfig()
    parsed = ""
    try:
        parsed = json.loads(content)
        logger.info("Inspecting %s as a %s file" % (filename, parsed['version']))

        if parsed['version'] > 3:
            elements = parsed['resources']
        else:
            # elements = parsed['modules'][0]['resources'].values()
            logger.warning("only state version v4 and above files are not supported right now")
            # a bit of a cheeky return - not raising, just abandoning early.
            return

        for res in elements:
            if res['type'] in config.elements_to_scan or (res['type'] in rd.resource_aliases and rd.resource_aliases[res['type']] in config.elements_to_scan):
                element = rd.lookup(res['type'])
                if element:
                    logger.info("Found and processing a resource of type %s" % res['type'])
                    element.process_state_resource(res, filename)
                else:
                    logging.debug(" Unsupported resource %s" % res['type'])
            else:
                logging.debug("Skipped %s as not in elments to scan" % res['type'])

    except Exception as e:
        # FIXME: tighten this up could be - file not Json issue, permission of s3 etc, as well as the terraform state
        # version has changed
        logger.info(e)
        logger.warning("Bad Terraform file: %s (perhaps a TF/state version issue?) %s" % (filename, type(e)))
        pass

