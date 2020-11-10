import sys
from . import main, ui
import keyring
from keyring.backends.fail import Keyring as FailKeyring
import json
import logging
import os
from typing import Optional
import dataclasses
from datetime import datetime, timezone

KEYRING_ENABLED = not isinstance(keyring.get_keyring(), FailKeyring)

logging.basicConfig(level=logging.INFO,
                    filename='/tmp/aws-okta.log',
                    filemode='w')

@dataclasses.dataclass()
class Credentials:
    aws_access_key_id: str
    aws_secret_access_key: str
    aws_session_token: str
    expiration: datetime

    def __post_init__(self) -> None:
        if isinstance(self.expiration, str):
            self.expiration = datetime.fromisoformat(self.expiration)

    @classmethod
    def from_v1_credentials(self, d) -> "Credentials":
        result = Credentials(
                aws_access_key_id=d["AccessKeyId"],
                aws_secret_access_key=d["SecretAccessKey"],
                aws_session_token=d["SessionToken"],
                expiration=d["Expiration"],
                )
        return result

    def as_v1_credentials(self):
        return {
                "Version": 1,
                "AccessKeyId": self.aws_access_key_id,
                "SecretAccessKey": self.aws_secret_access_key,
                "SessionToken": self.aws_session_token,
                "Expiration": self.expiration.isoformat(),
                }

    def expired(self):
        return self.expiration < datetime.now(timezone.utc)


class CredentialProcess:
    def __init__(self, env=os.environ):
        env = env.copy()
        self.aws_profile = env['AWS_PROFILE']
        del env['AWS_PROFILE']  # ensure we don't get in a loop resolving AWS creds for the aws sts assume-role call
        self.ui = ui.CLIUserInterface(environ=env)
        self.creds = main.GimmeAWSCreds(ui=self.ui)

    def run(self) -> None:
        logging.info("Fetching cached credentials")
        credentials = self.fetch_cached_credentials()
        if credentials is None or credentials.expired():
            logging.warning("Cached credentials not present or expired. Requesting new credentials.")
            credentials = self.fetch_new_credentials()
            self.cache_credentials(credentials)
        print(json.dumps(credentials.as_v1_credentials()))

    def fetch_new_credentials(self) -> Credentials:
        with self.ui:
            for data in self.creds.iter_selected_aws_credentials():  # TODO: ensure one!
                creds = data["credentials"]
                result = Credentials(
                        aws_access_key_id=creds["aws_access_key_id"],
                        aws_secret_access_key=creds["aws_secret_access_key"],
                        aws_session_token=creds["aws_session_token"],
                        expiration=creds["expiration"],
                        )
                return result

    def keyring_cache_name(self) -> str:
        return f'aws-okta_{self.aws_profile}'

    def fetch_cached_credentials(self) -> Optional[Credentials]:
        if not KEYRING_ENABLED:
            return None
        credentials_json = keyring.get_password(self.keyring_cache_name(), "")
        if credentials_json is None:
            logging.warning("No credentials cached in keyring, was looking for %s", self.keyring_cache_name())
            return None
        credentials_dict = json.loads(credentials_json)
        credentials = Credentials.from_v1_credentials(credentials_dict)
        return credentials

    def cache_credentials(self, credentials: Credentials) -> None:
        if not KEYRING_ENABLED:
            return
        logging.info("Caching credentials into keyring as %s", self.keyring_cache_name())
        keyring.set_password(
                self.keyring_cache_name(),
                "",
                json.dumps(credentials.as_v1_credentials()))
