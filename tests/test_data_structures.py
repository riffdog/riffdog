from riffdog.config import RDConfig


class TestRDConfig:

    def setup_method(self, method):
        RDConfig.instance = None
        #ResourceDirectory.instance = None

    def test_exclude_no_elements(self):
        config = RDConfig()

        assert list(config.elements_to_scan) == config.base_elements_to_scan

    def test_exclude_one_element(self):
        config = RDConfig()
        config.excluded_resources = config.base_elements_to_scan[:1]

        assert list(config.elements_to_scan) == config.base_elements_to_scan[1:]

    def test_singleton(self):
        config = RDConfig()
        config.regions = ['us-east-1', 'eu-west-1']
        config2 = RDConfig()

        assert id(config) == id(config2)
        assert config.regions == config2.regions

