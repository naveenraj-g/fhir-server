"""Shared org-ownership rule, reusable across every resource's service layer.

Two flavors of the same comparison, since create vs. patch/delete need
different failure behavior:
  - Create: target_org_id is the org being assigned to a not-yet-existing
    row — a mismatch is a straight 403 (assert_org_match).
  - Patch/Delete: target_org_id is an *existing* row's stored org_id — a
    mismatch must become a 404, not 403 (don't confirm the row exists to a
    caller outside the org), so those call sites use the plain org_matches()
    boolean and keep their own "return None/False" pattern.
"""

from app.errors.auth import PermissionDeniedError


def org_matches(target_org_id: str | None, actor_org_id: str | None) -> bool:
    """True if actor_org_id is unset (org-less/super-admin token — always
    allowed) or equals target_org_id exactly."""
    return actor_org_id is None or target_org_id == actor_org_id


def assert_org_match(
    target_org_id: str | None, actor_org_id: str | None, message: str
) -> None:
    """Raises PermissionDeniedError(message) if org_matches() fails."""
    if not org_matches(target_org_id, actor_org_id):
        raise PermissionDeniedError(message)
