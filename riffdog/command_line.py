import logging
import os
import argparse

from json import dumps, JSONEncoder

from tabulate import tabulate

from .scanner import scan
from .data_structures import RDConfig, StateStorage, ReportElement

logger = logging.getLogger(__name__)
DEFAULT_REGION = 'us-east-1'


class ReportEncoder(JSONEncoder):
    def default(self, o):
        if type(o) == ReportElement:
            return {
                "matched": o.matched,
                "notInAWS": o.in_tf_but_not_real,
                "notInTF": o.in_real_but_not_tf
            }
        else:
            return o.__dict__


def get_regions(region_args):
    """
    Current order of precedence
    - AWS_DEFAULT_REGION overrides everything else
    - region_args come next
    - fall back to us-east-1 I guess
    """
    env_region = os.environ.get('AWS_DEFAULT_REGION', None)
    regions = []
    if env_region is not None and env_region:
        regions.append(env_region)
    elif region_args:
        regions.extend(region_args)
    else:
        regions.append(DEFAULT_REGION)
    return regions


def main(*args):
    """
    This is the command line entry point
    """
    # Pre-stuff - use argparser to get command line arguments
    parser = argparse.ArgumentParser(description='Terraform - AWS infrastructure scanner')
    parser.add_argument('-v', '--verbose', help='Run in Verbose mode (try -vv for info output)', action='count')
    parser.add_argument('-b', '--bucket', help='Bucket containing state file location', action='append', nargs=1)
    parser.add_argument('--json', help='Produce Json output rather then Human readble', action='store_const', const=True)  # noqa: E501
    parser.add_argument('--region', help="AWS regions to use", action='append')
    parser.add_argument('--show-matched', help='Shows all resources, including those that matched', action='store_const', const=True)  # noqa: E501
    parser.add_argument('--exclude-resource', help="Excludes a particular resource", action='append', default=[])
    parser.add_argument('-i', '--include', help="External libraries to scan for Resources", action='append', default=[])


    # Parse args.
    parsed_args = parser.parse_args()

    logging_level = logging.ERROR

    if parsed_args.verbose is not None:
        if parsed_args.verbose > 2:
            logging_level = logging.DEBUG
        elif parsed_args.verbose == 2:
            logging_level = logging.INFO
        elif parsed_args.verbose == 1:
            logging_level = logging.WARNING

    # 1. Initalise logging.
    # FIXME: format to config & cmd line options

    logging.basicConfig(level=logging_level, format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S')
    logger.debug("cmd starting")

    # 2. Build config object
    config = RDConfig()

    config.state_storage = StateStorage.AWS_S3
    config.regions = get_regions(parsed_args.region)
    config.excluded_resources = parsed_args.exclude_resource
    config.external_resource_libs += parsed_args.include

    if parsed_args.bucket is not None:
        config.state_file_locations = parsed_args.bucket[0]

    # If there are no statefiles, quit early.
    if len(config.state_file_locations) == 0:
        print("No state file locations given - stopping scan early - run `riffdog -h`  for help")
        return

    # 3. Start scans
    results = scan()

    if parsed_args.json:
        print(dumps(results, cls=ReportEncoder))
    else:
        table_data = []

        for key, report in results.items():
            table_data += [[key, e, "✓", "x"] for e in report.in_real_but_not_tf]
            table_data += [[key, e, "x", "✓"] for e in report.in_tf_but_not_real]

            if parsed_args.show_matched:
                table_data += [[key, e, "✓", "✓"] for e in report.matched]
                table_data.reverse()   # We want matched at the top (a bit more out the way), a but more human friendly.

        print(tabulate(
            table_data,
            headers=["Resource Type", "Identifier", "Real", "Terraform"]))

        print("-------------------------")
        print("Please note, for elements in 'Real' (aka AWS) but not in Terraform, "
              "make sure you've scanned all your state files.")

    # 4. Report
    logger.debug("Cmd finished")
