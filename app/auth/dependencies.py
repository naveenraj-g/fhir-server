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
from app.core.logging import get_logger
from app.errors.auth import AuthenticationError

logger = get_logger(__name__)

# Module-level singleton — PyJWKClient caches the fetched JWKS response and
# only re-fetches on a cache miss (e.g. a `kid` it hasn't seen, from IAM key
# rotation), so this avoids a network round-trip on every request.
jwks_client = PyJWKClient(settings.IAM_JWKS_URL)

# Signing-key ids already seen. Purely for observability: a `kid` that isn't in
# here means PyJWKClient just made a blocking network call to the IAM on the
# request hot path, which is otherwise invisible.
_seen_kids: set[str] = set()


def decode_token(token: str) -> dict:
    """Validate and decode a raw JWT string.

    Verifies the signature (key selected via the JWT's `kid` header against
    the cached JWKS), `iss`/`aud` (both checked against IAM_ISSUER — the IAM
    sets aud == iss), and `exp` (handled automatically by pyjwt).

    Raises jwt.ExpiredSignatureError / jwt.InvalidTokenError on failure.
    """
    kid = jwt.get_unverified_header(token).get("kid")
    if kid and kid not in _seen_kids:
        _seen_kids.add(kid)
        logger.info(
            "JWKS signing key fetched",
            extra={"event": "auth.jwks_fetch", "kid": kid},
        )

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
        _log_auth_failure("missing_token", request)
        raise AuthenticationError("Missing authentication token")

    token = auth_header.split(" ")[1]

    try:
        payload = decode_token(token)
        request.state.user = payload
        request.state.token = token
        return payload
    except jwt.ExpiredSignatureError:
        _log_auth_failure("token_expired", request)
        raise AuthenticationError("Token expired")
    except jwt.InvalidTokenError:
        _log_auth_failure("invalid_token", request)
        raise AuthenticationError("Invalid token")
    except Exception as exc:
        # Anything else here is infrastructure, not a bad token — JWKS
        # unreachable, TLS failure, malformed IAM response. Logged with the
        # traceback because the 401 the caller sees says nothing useful.
        logger.error(
            "Authentication failed unexpectedly",
            extra={"event": "auth.failed", "reason": "internal", "path": request.url.path},
            exc_info=exc,
        )
        raise AuthenticationError("Invalid or expired token")


def _log_auth_failure(reason: str, request: Request) -> None:
    """The caller never learns why authentication failed (deliberately) — the
    log is the only place the distinction is recorded."""
    logger.warning(
        "Authentication failed",
        extra={
            "event": "auth.failed",
            "reason": reason,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
        },
    )
