import pytest

from riffdog.command_line import get_regions, DEFAULT_REGION


@pytest.fixture
def set_region(monkeypatch):
    return monkeypatch


class TestGetRegions:

    def test_get_regions_env(self, set_region):
        test_region = 'eu-west-2'
        set_region.setenv('AWS_DEFAULT_REGION', test_region)
        assert get_regions(['us-east-1', 'us-east-2']) == [test_region]

    def test_get_regions_cli(self, set_region):
        test_regions = ['us-east1', 'eu-west1']
        assert get_regions(test_regions) == test_regions

    def test_get_regions_default(self, set_region):
        assert get_regions([]) == [DEFAULT_REGION]
