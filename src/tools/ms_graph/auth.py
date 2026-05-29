import os
import json
from dotenv import load_dotenv
from azure.identity import (
    InteractiveBrowserCredential,
    TokenCachePersistenceOptions,
    AuthenticationRecord,
)

load_dotenv()

_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
ROOT = os.getenv("LOCAL_STORE_PATH", os.path.join(_REPO_ROOT, ".local"))
AUTH_RECORD_PATH = os.path.join(ROOT, "ms_auth_record.json")
CLIENT_ID = os.getenv("MS_CLIENT_ID")
GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def get_token(scopes: list[str]) -> str:
    if not CLIENT_ID:
        raise RuntimeError("MS_CLIENT_ID not set in environment variables.")

    cache_options = TokenCachePersistenceOptions(allow_unencrypted_storage=True)
    auth_record = None

    if os.path.exists(AUTH_RECORD_PATH):
        try:
            with open(AUTH_RECORD_PATH, "r") as f:
                auth_record = AuthenticationRecord.deserialize(json.load(f))
        except Exception:
            pass

    credential = InteractiveBrowserCredential(
        client_id=CLIENT_ID,
        cache_persistence_options=cache_options,
        authentication_record=auth_record,
    )

    token = credential.get_token(*scopes).token

    record = credential.authenticate(scopes=scopes)
    os.makedirs(os.path.dirname(os.path.abspath(AUTH_RECORD_PATH)), exist_ok=True)
    with open(AUTH_RECORD_PATH, "w") as f:
        json.dump(record.serialize(), f)

    return token


def auth_headers(scopes: list[str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {get_token(scopes)}"}
