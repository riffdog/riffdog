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

    def test_include_scan(self, capsys):
        """
        This is the primary golden path tests - it tests the including of resources, the loading of the
        files to scan, the scanning both tf and real, and potentially the comparison function too.
        """
        # check the resource_Scanning loading has been ok - this can't be merged with the help imports
        # as that nees the -h
        
        # also needs to have a state file or it fails
        testargs = ["riffdog", "-i", "test_resource_pack", "tests/test_state_files/v4_test_file.tfstate"]
        with patch('sys.argv', testargs):
            main()
   
        captured = capsys.readouterr()

        rd = ResourceDirectory()

        assert len(rd.found_resources) == 2
        assert len(rd.resource_aliases) == 1

        predicted = {
            "Number One (4-1)": {
                "type": "test_item_one",
                "real": True,
                "tf" : True,
                "dirty": False
            },
            "Number Two (4-2)": {
                "type": "test_item_one",
                "real": False,
                "tf" : True,
                "dirty": False
            },
            "Number Three (4-3)": {
                "type": "test_item_one",
                "real": False,
                "tf" : True,
                "dirty": False
            },
            # item 4 should be missing
            "Number Five (4-5)": {
                "type": "test_item_one",
                "real": False,
                "tf" : True,
                "dirty": False
            },
            "Number Six (4-6)": {
                "type": "test_item_three",
                "real": False,
                "tf" : True,
                "dirty": False
            },
            # this is a type-four aliased to type_three
            "Number Seven (4-7)": {
                "type": "test_item_three",
                "real": False,
                "tf" : True,
                "dirty": False
            },
            "Not In TF": {
                "type": "test_item_one",
                "real": True,
                "tf" : False,
                "dirty": False
            }
        }


        for item in rd._items:
            if item.in_terraform:
                matched = predicted[item.terraform_id]
            else:
                matched = predicted[item.real_id]

            assert item.item_type == matched['type']
            assert item.in_real_world == matched['real']
            assert item.in_terraform == matched['tf']
            assert item.dirty == matched['dirty']

