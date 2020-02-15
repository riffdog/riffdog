import mock
import pytest

from riffdog.scanner import scan, NO_FOUND_RESOURCES_ERROR
from riffdog.resource import ResourceDirectory
from riffdog.data_structures import RDConfig


class TestScanner:

    def test_no_resource_modules(self):
        with mock.patch('riffdog.scanner._s3_state_fetch') as mock_state_fetch:
            with pytest.raises(SystemExit) as exc:
                scan()

                assert NO_FOUND_RESOURCES_ERROR in str(exc.value)
                assert not mock_state_fetch.called

    def test_existing_resource_modules(self):
        rd = ResourceDirectory()
        rd.found_resources = {'found': 'somestuff'}

        config = RDConfig()
        config.state_file_locations = ['state1']

        with mock.patch('riffdog.scanner._s3_state_fetch') as mock_state_fetch:
            scan()

            assert mock_state_fetch.called