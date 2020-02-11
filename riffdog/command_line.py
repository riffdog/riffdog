import logging 
import argparse 

from .scanner import scan, RDConfig, StateStorage, ScanMode

logger = logging.getLogger(__name__)

def main(*args):
    """
    This is the command line entry point
    """

    # Pre-stuff - use argparser to get command line arguments

    parser = argparse.ArgumentParser(description='Terraform - AWS infrastructure scanner')

    parser.add_argument('-v', '--verbose', help='Run in Verbose mode (try -vv for info output)', action='count')
    parser.add_argument('-b', '--bucket', help='Bucket containing state file location', action='append', nargs=1)

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
    
    # 4. Report
    logger.debug("Cmd finished")


