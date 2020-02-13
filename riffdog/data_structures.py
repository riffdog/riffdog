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
        'aws_instance',
        'aws_s3_bucket'
    ]


class ReportElement():
    """
    Output report object for reporting things it finds.
    """

    matched = None
    in_tf_but_not_real = None
    in_real_but_not_tf = None

    def __init__(self):
        self.matched = []
        self.in_tf_but_not_real = []
        self.in_real_but_not_tf = []