"""FastAPI dependency functions for JWT-based authentication.

Flow: client sends `Authorization: Bearer <jwt>` -> get_current_user extracts
the token -> decode_token verifies it against the IAM's JWKS (signature, exp,
iss, aud) -> the decoded payload is stashed on request.state.user so route
handlers and require_permission() (app.auth.rbac) can read it without
re-decoding.
"""

import jwt
from fastapi import Request
from jwt import PyJWKClient

from app.core.config import settings
from app.errors.auth import AuthenticationError

# Module-level singleton — PyJWKClient caches the fetched JWKS response and
# only re-fetches on a cache miss (e.g. a `kid` it hasn't seen, from IAM key
# rotation), so this avoids a network round-trip on every request.
jwks_client = PyJWKClient(settings.IAM_JWKS_URL)


def decode_token(token: str) -> dict:
    """Validate and decode a raw JWT string.

    Verifies the signature (key selected via the JWT's `kid` header against
    the cached JWKS), `iss`/`aud` (both checked against IAM_ISSUER — the IAM
    sets aud == iss), and `exp` (handled automatically by pyjwt).

    Raises jwt.ExpiredSignatureError / jwt.InvalidTokenError on failure.
    """
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        audience=settings.IAM_ISSUER,
        issuer=settings.IAM_ISSUER,
        algorithms=["EdDSA", "RS256"],
        options={"verify_aud": True},
    )


async def get_current_user(request: Request) -> dict:
    """FastAPI dependency that authenticates the incoming request.

    Applied as a router-level dependency (see app.main) so it runs once for
    every route in the group — individual routes don't declare it again.
    Always raises AuthenticationError (401) on any failure, without
    distinguishing the failure mode to the caller.
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthenticationError("Missing authentication token")

    token = auth_header.split(" ")[1]

    try:
        payload = decode_token(token)
        request.state.user = payload
        request.state.token = token
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")
    except Exception:
        raise AuthenticationError("Invalid or expired token")
