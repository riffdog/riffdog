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


class RDConfig:
    """
    RiffDog Config Object for controlling the scan.
    """

    class __RDConfig:
        scan_mode = ScanMode.LIGHT

        state_storage = StateStorage.AWS_S3
        state_file_locations = []
        regions = []
        excluded_resources = []

        base_elements_to_scan = []

        # This is a list of the core repositories. It can be added to with command options
        external_resource_libs = [
            'riffdog_aws',
            'riffdog_cloudflare'
        ]

        @property
        def elements_to_scan(self):
            return (x for x in self.base_elements_to_scan if x not in self.excluded_resources)

            
    instance = None

    def __new__(cls): # __new__ always a classmethod
        if not RDConfig.instance:
            RDConfig.instance = RDConfig.__RDConfig()
        return RDConfig.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name):
        return setattr(self.instance, name)

