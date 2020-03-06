"""
This file is for testing golden path features
"""

import pytest
from mock import patch

from riffdog.config import RDConfig
from riffdog.resource import ResourceDirectory

from riffdog.command_line import main


class TestCommandLine:

    def setup_method(self, method):
        RDConfig.instance = None
        ResourceDirectory.instance = None

    def test_help(self, capsys):
        testargs = ["riffdog", "-h"]
        with patch('sys.argv', testargs):
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                
                main()
   
            assert pytest_wrapped_e.type == SystemExit
        
        captured = capsys.readouterr()
        # inspect captured 

        output = captured.out

        assert "Terraform - Reality Infrastructure Scanner" in output  # if this is there, help is there
        assert "Test Resources" not in output  # this shouldn't be there as no -i
        assert len(captured.err) == 0          # no error output

        # check that there are no resources
        rd = ResourceDirectory()

        assert len(rd.found_resources) == 0
        assert len(rd.resource_aliases) == 0

    def test_help_imports(self, capsys):
        testargs = ["riffdog", "-i", "test_resource_pack", "-h"]
        with patch('sys.argv', testargs):
            with pytest.raises(SystemExit) as pytest_wrapped_e:
                
                main()
   
            assert pytest_wrapped_e.type == SystemExit
        
        captured = capsys.readouterr()
        output = captured.out

        assert "Terraform - Reality Infrastructure Scanner" in output  # if this is there, help is there
        assert "Test Resources" in output  # this should be there as we've added the fake module
        assert "--test_value TEST_VALUE" in output
        assert len(captured.err) == 0       # no error output

    def test_include_resources(self, capsys):
        # check the resource_Scanning loading has been ok - this can't be merged with the help imports
        # as that nees the -h
        
        # also needs to have a state file or it fails
        testargs = ["riffdog", "-i", "test_resource_pack", "test_state_files/v4_test_file.tfstate"]
        with patch('sys.argv', testargs):
            main()
   
        captured = capsys.readouterr()

        rd = ResourceDirectory()

        assert len(rd.found_resources) == 1
        assert len(rd.resource_aliases) == 0