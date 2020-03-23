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
                "inTerraForm": o.in_terraform
            }

            if o.in_real_world:
                out['realWorldId'] = o.real_id

            if o.in_terraform:
                out['terraformId'] = o.terraform_id

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
            logging.warning("Exception loading %s - might not be installed, or errors on load" % project)
            # Can not raise here because you want to pass on optional core modules
            


def _add_core_arguments(parser):
    parser.add_argument('-i', '--include', help="External libraries to scan for Resources", action='append', default=[])
    parser.add_argument('-v', '--verbose', help='Run in Verbose mode (try -vv for info output)', action='count')
    parser.add_argument('-b', '--bucket', help='Bucket containing state file location', action='append', nargs=1)
    parser.add_argument('--json', help='Produce Json output rather then Human readble', action='store_const', const=True)  # noqa: E501
    parser.add_argument('--json-indent', help='Pretty print json with indents of this value', type=int)
    parser.add_argument('--show-matched', help='Shows all resources, including those that matched', action='store_const', const=True)  # noqa: E501
    parser.add_argument('--exclude-resource', help="Excludes a particular resource", action='append', default=[])
    parser.add_argument('--include-resource', help="Includes a particular resource", action="append", default=[])
    parser.add_argument('dir', nargs='*', help="Folders containing state files *or* a specific state", default=None)

def main():
    """
    This is the command line entry point
    """

    # Pre-stuff - use argparser to get command line arguments

    pre_parser = ArgumentParser(add_help=False)
    
    _add_core_arguments(pre_parser)
    
    pre_parsed_args = pre_parser.parse_args(sys.argv[1:])

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

    parser = argparse.ArgumentParser(description='Terraform - Reality Infrastructure Scanner')
    _add_core_arguments(parser)

    config = RDConfig()

    config.external_resource_libs += pre_parsed_args.include
    config.excluded_resources = pre_parsed_args.exclude_resource
    config.included_resources = pre_parsed_args.include_resource

    find_arguments(parser, config.external_resource_libs)
    
    # Parse args.
    
    parsed_args = parser.parse_args(sys.argv[1:])

    # 2. Build config object

    for arg in vars(parsed_args):
        setattr(config, arg, getattr(parsed_args, arg))
    
    if parsed_args.dir:
        config.state_storage = StateStorage.FILE
        config.state_file_locations = parsed_args.dir
    elif parsed_args.bucket:
        config.state_storage = StateStorage.AWS_S3
        config.state_file_locations = parsed_args.bucket[0]

    if parsed_args.bucket is not None:
        config.state_file_locations = parsed_args.bucket[0]

    # These need to be added in as defaults:
    
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

        filtered_data = []
        for item in results:
            if not item.matched or parsed_args.show_matched:
                filtered_data.append(item)

        if parsed_args.json_indent:
            print(dumps(filtered_data, cls=ReportEncoder, indent=parsed_args.json_indent))
        else:
            print(dumps(filtered_data, cls=ReportEncoder))
 
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
