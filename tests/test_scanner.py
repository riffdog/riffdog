import mock
import pytest
import boto3
from botocore.stub import Stubber

from riffdog.scanner import scan, NO_FOUND_RESOURCES_ERROR, STORAGE_NOT_IMPLEMENTED_ERROR, _s3_state_fetch
from riffdog.resource import ResourceDirectory
from riffdog.config import RDConfig
from riffdog.exceptions import ResourceNotFoundError, StorageNotImplemented


class TestScanner:

    def test_no_resource_modules(self):
        with mock.patch('riffdog.scanner._s3_state_fetch') as mock_state_fetch:
            with pytest.raises(ResourceNotFoundError) as exc:
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

    def test_unsupported_state_storage(self):
        config = RDConfig()
        config.state_storage = 'not s3'
        with mock.patch('riffdog.scanner._load_resource_modules') as mock_state_load_modules:
            with pytest.raises(StorageNotImplemented) as exc:
                scan()

                assert STORAGE_NOT_IMPLEMENTED_ERROR in str(exc.value)
