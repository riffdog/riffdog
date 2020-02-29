import logging
import os
import argparse
import sys
import pkgutil
from importlib import import_module

from json import dumps, JSONEncoder

from tabulate import tabulate

from .scanner import scan
from .config import RDConfig, StateStorage
from .data_structures import FoundItem
from .resource import ResourceDirectory
from .exceptions import RiffDogException

logger = logging.getLogger(__name__)
DEFAULT_REGION = 'us-east-1'


class ArgumentParser(argparse.ArgumentParser):

    def error(self, message):
        pass

class ReportEncoder(JSONEncoder):
    def default(self, o):
        if type(o) == FoundItem:
            out = {
                "matched": o.matched,
                "inRealWorld": o.in_real_world,
                "inTerraForm": o.in_real_but_not_tf
            }

            if o.in_real_world:
                out['inRealWorld'] = True
                out['realWorldId'] = o.real_id
            else:
                out['inRealWorld'] = False

            if o.in_terraform:
                out['inTerraform'] = True
                out['terraformId'] = o.terraform_id
            else:
                out['inTerraform'] = False

            return out
        else:
            return o.__dict__


def find_arguments(argparser, imports):
    # this is related to, but not, resource scanners

    # attempt to scan other projects
    # So - printing here is *bad* because logging is not yet vonfigured.

    logging.info("Looking for external modules")
    for project in imports:
        try:
            logging.info("Loading config for %s" % project)
            imported = import_module("%s.config" % project)
            imported.add_args(argparser)
            imported.config()
        except Exception as e:
            #print(e)
            logging.warn("Exception loading %s - might not be installed, or errors on load" % project)
            # Can not raise here because you want to pass on optional core modules
            


def _add_core_arguments(parser):
    parser.add_argument('-i', '--include', help="External libraries to scan for Resources", action='append', default=[])
    parser.add_argument('-v', '--verbose', help='Run in Verbose mode (try -vv for info output)', action='count')
    parser.add_argument('-b', '--bucket', help='Bucket containing state file location', action='append', nargs=1)
    parser.add_argument('--json', help='Produce Json output rather then Human readble', action='store_const', const=True)  # noqa: E501
    parser.add_argument('--show-matched', help='Shows all resources, including those that matched', action='store_const', const=True)  # noqa: E501
    parser.add_argument('--exclude-resource', help="Excludes a particular resource", action='append', default=[])
    

def main(*args):
    """
    This is the command line entry point
    """
    # Pre-stuff - use argparser to get command line arguments

    pre_parser = ArgumentParser(description='Terraform - AWS infrastructure scanner', add_help=False)
    
    _add_core_arguments(pre_parser)
    
    pre_parsed_args = pre_parser.parse_args(*args)

    logging_level = logging.ERROR

    if pre_parsed_args.verbose is not None:
        if pre_parsed_args.verbose > 2:
            logging_level = logging.DEBUG
        elif pre_parsed_args.verbose == 2:
            logging_level = logging.INFO
        elif pre_parsed_args.verbose == 1:
            logging_level = logging.WARNING

    # 1. Initalise logging.

    logging.basicConfig(level=logging_level, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S')
    logger.debug("cmd starting")

    parser = argparse.ArgumentParser(description='Terraform - AWS infrastructure scanner')
    _add_core_arguments(parser)

    config = RDConfig()

    config.external_resource_libs += pre_parsed_args.include

    find_arguments(parser, config.external_resource_libs)
    
    # Parse args.
    
    parsed_args = parser.parse_args()


    # 2. Build config object

    for arg in vars(parsed_args):
        setattr(config, arg, getattr(parsed_args, arg))

    
    if parsed_args.bucket is not None:
        config.state_file_locations = parsed_args.bucket[0]

    # These need to be added in as defaults:
    config.state_storage = StateStorage.AWS_S3

    # If there are no statefiles, quit early.
    if len(config.state_file_locations) == 0:
        print("No state file locations given - stopping scan early - run `riffdog -h`  for help", file=sys.stderr)
        sys.exit(0)

    # 3. Start scans
    try:
        scan()
    except RiffDogException as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(0)
    except Exception as exc:
        print("Unexpected exception: {}".format(str(exc)), file=sys.stderr)
        sys.exit(1)

    rd = ResourceDirectory()

    results = rd._items  # FIXME - accessing internal object

    if parsed_args.json:
        print(dumps(results, cls=ReportEncoder))
    else:

        table_data = []

        for item in results:
            if not item.matched:
                table_data += [[item.item_type, item.terraform_id, item.real_id, "✓" if item.in_real_world else "x", "✓" if item.in_terraform else "x", "N/A"]]
            if parsed_args.show_matched and item.matched:
                table_data += [[item.item_type, item.terraform_id, item.real_id, "✓", "✓", "x" if not item.dirty else "✓"]]

        print(tabulate(
            table_data,
            headers=["Resource Type", "Terraform Id", "Real Id", "Real", "Terraform", "Dirty"]))

        print("-------------------------")
        print("Please note, for elements in 'Real' (aka AWS) but not in Terraform, "
              "make sure you've scanned all your state files.")

    # 4. Report
    logger.debug("Cmd finished")
