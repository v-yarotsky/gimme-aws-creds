import dataclasses
from datetime import datetime, timezone

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


