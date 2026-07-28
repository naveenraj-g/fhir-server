from dataclasses import dataclass
from typing import Optional


@dataclass
class AuthUser:
    """Immutable snapshot of the authenticated caller's identity for a single
    request, built from the verified JWT after get_current_user succeeds.

    sub:    JWT `sub` claim — stable user id, used as created_by/updated_by
            on writes so audit fields can't be spoofed via the request body.
    org_id: JWT `activeOrganizationId` claim — the org the caller is acting
            on behalf of. None for org-less/super-admin tokens, which are
            exempted from tenant-ownership checks.
    """

    sub: str
    org_id: str | None
