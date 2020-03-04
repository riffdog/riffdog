from riffdog.config import RDConfig


class TestRDConfig:

    def test_exclude_no_elements(self):
        config = RDConfig()

        assert list(config.elements_to_scan) == config.base_elements_to_scan

    def test_exclude_one_element(self):
        config = RDConfig()
        config.excluded_resources = config.base_elements_to_scan[:1]

        assert list(config.elements_to_scan) == config.base_elements_to_scan[1:]

    def test_include_no_exclude(self):
        config = RDConfig()
        config.included_resources = ['aws_bucket']

        assert list(config.elements_to_scan) == config.included_resources

    def test_include_with_excluded(self):
        config = RDConfig()
        config.exclude_resources = ['aws_s3_bucket']
        config.included_resources = ['aws_vpc', 'aws_subnet']

        assert list(config.elements_to_scan) == config.included_resources

    def test_singleton(self):
        config = RDConfig()
        config.regions = ['us-east-1', 'eu-west-1']
        config2 = RDConfig()

        assert id(config) == id(config2)
        assert config.regions == config2.regions