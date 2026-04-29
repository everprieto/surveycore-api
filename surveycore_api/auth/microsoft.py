"""Microsoft Entra ID token validation."""
import os
import requests
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()

TENANT_ID = os.getenv("AZURE_TENANT_ID")
CLIENT_ID = os.getenv("AZURE_CLIENT_ID")

_jwks_cache: dict | None = None


def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        url = f"https://login.microsoftonline.com/{TENANT_ID}/discovery/v2.0/keys"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        _jwks_cache = response.json()
    return _jwks_cache


def validate_microsoft_id_token(id_token: str) -> dict:
    """Validate a Microsoft Entra ID token and return its claims.

    Raises ValueError if the token is invalid.
    """
    if not TENANT_ID or not CLIENT_ID:
        raise ValueError("AZURE_TENANT_ID and AZURE_CLIENT_ID must be configured")

    jwks = _get_jwks()

    try:
        header = jwt.get_unverified_header(id_token)
    except JWTError as e:
        raise ValueError(f"Invalid token header: {e}")

    rsa_key = next(
        (key for key in jwks.get("keys", []) if key.get("kid") == header.get("kid")),
        None,
    )
    if rsa_key is None:
        # Cache may be stale — invalidate and retry once
        global _jwks_cache
        _jwks_cache = None
        jwks = _get_jwks()
        rsa_key = next(
            (key for key in jwks.get("keys", []) if key.get("kid") == header.get("kid")),
            None,
        )

    if rsa_key is None:
        raise ValueError("No matching signing key found in Microsoft JWKS")

    issuer = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"

    try:
        payload = jwt.decode(
            id_token,
            rsa_key,
            algorithms=["RS256"],
            audience=CLIENT_ID,
            issuer=issuer,
            options={"verify_at_hash": False},
        )
    except JWTError as e:
        raise ValueError(f"Token validation failed: {e}")

    return payload
