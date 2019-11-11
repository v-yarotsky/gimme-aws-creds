"""Unit tests for gimme_aws_creds.config.Config"""
import argparse
import unittest
import tempfile

from mock import patch
from nose.tools import assert_equals

from gimme_aws_creds import ui
from gimme_aws_creds.config import Config


class TestConfig(unittest.TestCase):
    """Class to test Config Class.
       Mock is used to mock external calls"""

    def setUp(self):
        """Set up for the unit tests"""
        self.config = Config(gac_ui=ui.cli, create_config=False)

    def tearDown(self):
        """Run Clean Up"""
        self.config.clean_up()

    @patch(
        "argparse.ArgumentParser.parse_args",
        return_value=argparse.Namespace(
            username="ann",
            profile=None,
            insecure=False,
            resolve=None,
            mfa_code=None,
            remember_device=False,
            output_format=None,
            roles=None,
            action_register_device=False,
            action_configure=False,
            action_list_profiles=False,
            action_list_roles=False,
            action_store_json_creds=False,
        ),
    )
    def test_get_args_username(self, mock_arg):
        """Test to make sure username gets returned"""
        self.config.get_args()
        assert_equals(self.config.username, "ann")

    def test_read_config(self):
        """Test to make sure getting config works"""
        test_ui = MockUserInterface(argv = [
            "--profile",
            "myprofile",
        ])
        with open(test_ui.HOME + "/.okta_aws_login_config", "w") as config_file:
            config_file.write("""
[myprofile]
client_id = foo
""")
        config = Config(gac_ui=test_ui, create_config=False)
        config.conf_profile = "myprofile"
        profile_config = config.get_config_dict()
        self.assertEqual(profile_config, {"client_id": "foo"})

    def test_read_config_inherited(self):
        """Test to make sure getting config works when inherited"""
        test_ui = MockUserInterface(argv = [
            "--profile",
            "myprofile",
        ])
        with open(test_ui.HOME + "/.okta_aws_login_config", "w") as config_file:
            config_file.write("""
[mybase]
client_id = bar
aws_appname = baz
[myprofile]
inherits = mybase
client_id = foo
aws_rolename = myrole
""")
        config = Config(gac_ui=test_ui, create_config=False)
        config.conf_profile = "myprofile"
        profile_config = config.get_config_dict()
        self.assertEqual(profile_config, {
            "client_id": "foo",
            "aws_appname": "baz",
            "aws_rolename": "myrole",
        })

class MockUserInterface(ui.UserInterface):

    def __init__(self, argv):
        super().__init__(environ={}, argv=argv)
        self.HOME = tempfile.mkdtemp()
