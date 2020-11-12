from .credentials import Credentials

import json
import keyring
import logging

from keyring.backends.fail import Keyring as FailKeyring
from typing import Optional

KEYRING_ENABLED = not isinstance(keyring.get_keyring(), FailKeyring)

class CredentialsCache:
    def __init__(self, name: str):
        self.name = name

    def fetch(self) -> Optional[Credentials]:
        if not KEYRING_ENABLED:
            return None
        credentials_json = keyring.get_password(self.name, "")
        if credentials_json is None:
            logging.warning("No credentials cached in keyring, was looking for %s", self.name)
            return None
        credentials_dict = json.loads(credentials_json)
        credentials = Credentials.from_v1_credentials(credentials_dict)
        return credentials

    def store(self, creds: Credentials) -> None:
        if not KEYRING_ENABLED:
            return
        logging.info("Caching credentials into keyring as %s", self.name)
        keyring.set_password(self.name, "", json.dumps(creds.as_v1_credentials()))
