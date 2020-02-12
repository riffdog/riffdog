"""
This module exists to hold data structures common across modules, the scanner
and the command line interface
"""

from enum import Enum

class ScanMode(Enum):
    """
    Mode of operation of scanner
    """

    LIGHT = 1
    DEEP = 2


class StateStorage(Enum):
    AWS_S3 = 1
    # FILE = 2


class RDConfig():
    """
    RiffDog Config Object for controlling the scan.
    """

    scan_mode = ScanMode.LIGHT

    state_storage = StateStorage.AWS_S3
    state_file_locations = []
    regions = []

    elements_to_scan = [
        'aws_instance'
    ]


class ReportElement():
    """
    Output report object for reporting things it finds.
    """

    matched = []
    in_tf_but_not_aws = []
    in_aws_but_not_tf = []