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
        _configurations = {}

        @property
        def elements_to_scan(self):
            return (x for x in self.base_elements_to_scan if x not in self.excluded_resources)


        def __init__(self):
            # Set defaults and must-have settings
            self.external_resource_libs = [
                'riffdog_aws',
                #'riffdog_cloudflare'
            ]

            self.state_file_locations = []

            self.excluded_resources = []

            self.base_elements_to_scan = []

            self.scan_mode = ScanMode.LIGHT

        def __getattr__(self, name):
            return self._configurations[name]

        def __setattr__(self, name, value):
            self._configurations[name] = value

            
    instance = None

    def __new__(cls): # __new__ always a classmethod
        if not RDConfig.instance:
            RDConfig.instance = RDConfig.__RDConfig()
        return RDConfig.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name):
        return setattr(self.instance, name)

