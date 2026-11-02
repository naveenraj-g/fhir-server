from app.repository.base import BaseRepository
from app.repository.family_member_history.core import _CoreMixin
from app.repository.family_member_history.full import _FullMixin


class FamilyMemberHistoryRepository(_CoreMixin, _FullMixin, BaseRepository):
    """Repository for FamilyMemberHistory FHIR resource."""

    pass


__all__ = ["FamilyMemberHistoryRepository"]
