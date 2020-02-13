from riffdog.data_structures import RDConfig


class TestRDConfig:

    def test_exclude_no_elements(self):
        config = RDConfig()

        assert list(config.elements_to_scan) == config.base_elements_to_scan

    def test_exclude_one_element(self):
        config = RDConfig()
        config.excluded_resources = config.base_elements_to_scan[:1]

        assert list(config.elements_to_scan) == config.base_elements_to_scan[1:]