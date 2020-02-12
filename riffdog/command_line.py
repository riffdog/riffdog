import logging
import argparse

from json import dumps, JSONEncoder

from tabulate import tabulate

from .scanner import scan
from .data_structures import RDConfig, StateStorage, ScanMode, ReportElement

logger = logging.getLogger(__name__)


class ReportEncoder(JSONEncoder):
    def default(self, o):
        if type(o) == ReportElement:
            return {
                "matched": o.matched,
                "notInAWS": o.in_tf_but_not_aws,
                "notInTF": o.in_aws_but_not_tf
            }
        else:
            return o.__dict__


def main(*args):
    """
    This is the command line entry point
    """

    # Pre-stuff - use argparser to get command line arguments

    parser = argparse.ArgumentParser(description='Terraform - AWS infrastructure scanner')

    parser.add_argument('-v', '--verbose', help='Run in Verbose mode (try -vv for info output)', action='count')
    parser.add_argument('-b', '--bucket', help='Bucket containing state file location', action='append', nargs=1)
    parser.add_argument('--json', help='Produce Json output rather then Human Readble', action='store_const', const=True)
    parser.add_argument('--show-matched', help='Shows all resources, including those that matched', action='store_const', const=True)


    # Parse args.

    parsed_args = parser.parse_args()

    logging_level = logging.ERROR

    if parsed_args.verbose != None:
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

    if parsed_args.bucket != None:
        config.state_file_locations = parsed_args.bucket[0]

    # 3. Start scans
    results = scan(config)

    if parsed_args.json:
        print(dumps(results, cls=ReportEncoder))
    else:

        for key, report in results.items():
            table_data = [[key, e, "✓", "x"] for e in report.in_aws_but_not_tf]
            table_data += [[key, e, "x", "✓"] for e in report.in_tf_but_not_aws]

            if parsed_args.show_matched:
                table_data += [[key, e, "✓", "✓"] for e in report.matched]
                table_data.reverse()   # We want matched at the top (a bit more out the way), a but more human friendly.

        print(tabulate(
            table_data,
            headers=["Resource Type", "Identifier", "AWS", "Terraform"]))

        print("-------------------------")
        print ("Please note, for elements in AWS but not in Terraform, make sure you've scanned all your state files.")
    # 4. Report
    logger.debug("Cmd finished")
