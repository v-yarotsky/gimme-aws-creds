from . import main, ui
from .cache import CredentialsCache
from .credentials import Credentials

import json
import logging
import os
import sys

logging.basicConfig(level=logging.INFO,
                    filename='/tmp/aws-okta.log',
                    filemode='w')

class CredentialProcess:
    def __init__(self, env=os.environ):
        env = env.copy()
        self.aws_profile = env['AWS_PROFILE']
        self.cache = CredentialsCache(f'aws-okta_{self.aws_profile}')

        del env['AWS_PROFILE']  # ensure we don't get in a loop resolving AWS creds for the aws sts assume-role call
        self.ui = ui.CLIUserInterface(environ=env)
        self.creds = main.GimmeAWSCreds(ui=self.ui)

    def run(self) -> None:
        logging.info("Fetching cached credentials")
        credentials = self.cache.fetch()
        if credentials is None or credentials.expired():
            logging.warning("Cached credentials not present or expired. Requesting new credentials.")
            credentials = self.fetch_new_credentials()
            self.cache.store(credentials)
        print(json.dumps(credentials.as_v1_credentials()))

    def fetch_new_credentials(self) -> Credentials:
        with self.ui:
            if self.creds.device_token is None:
                self.creds.handle_action_register_device()
            for data in self.creds.iter_selected_aws_credentials():  # TODO: ensure one!
                creds = data["credentials"]
                result = Credentials(
                        aws_access_key_id=creds["aws_access_key_id"],
                        aws_secret_access_key=creds["aws_secret_access_key"],
                        aws_session_token=creds["aws_session_token"],
                        expiration=creds["expiration"],
                        )
                return result
