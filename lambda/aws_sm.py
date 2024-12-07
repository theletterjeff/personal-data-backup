from enum import Enum

import boto3
import json


class ApiKeyName(Enum):
    LAST_FM = "last_fm_api_key"
    TOGGL = "toggl_api_key"


def get_api_key(key_name: ApiKeyName) -> str:
    secret_name = "personal-backup-keys"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    sm_client = session.client(
        service_name="secretsmanager",
        region_name=region_name,
    )

    secret_resp = sm_client.get_secret_value(SecretId=secret_name)
    secret = json.loads(secret_resp["SecretString"])
    return secret[key_name.value]
