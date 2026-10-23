from sqlalchemy import func, or_
from sqlalchemy.future import select

from app.core.filters import apply_child_exists_filter, apply_token_filter
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.practitioner import (
    PractitionerAddress,
    PractitionerCommunication,
    PractitionerCommunicationCoding,
    PractitionerIdentifier,
    PractitionerModel,
    PractitionerName,
    PractitionerTelecom,
)

from ._shared import _SORTABLE_FIELDS, _with_relationships

logger = get_logger(__name__)


class _CoreMixin:
    """Core CRUD for the Practitioner parent row (no sub-resources)."""

    async def get_by_practitioner_id(
        self, practitioner_id: int
    ) -> PractitionerModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PractitionerModel).where(
                    PractitionerModel.practitioner_id == practitioner_id
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_practitioner_id_in_org(
        self, practitioner_id: int, org_id: str
    ) -> PractitionerModel | None:
        """Full lookup (with sub-resources) scoped to org_id — returns None
        unless the practitioner exists AND belongs to org_id."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PractitionerModel).where(
                    PractitionerModel.practitioner_id == practitioner_id,
                    PractitionerModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def practitioner_belongs_to_org(
        self, practitioner_id: int, org_id: str
    ) -> bool:
        """Lightweight existence check (no eager-loading) for tenant-ownership
        gates on write routes — True iff the practitioner exists AND belongs
        to org_id."""
        async with self.session_factory() as session:
            stmt = select(PractitionerModel.id).where(
                PractitionerModel.practitioner_id == practitioner_id,
                PractitionerModel.tenant_id == org_id,
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    def _apply_list_filters(
        self,
        stmt,
        org_id,
        user_id: str | None = None,
        active: bool | None = None,
        gender=None,
        family: str | None = None,
        given: str | None = None,
        name: str | None = None,
        phonetic: str | None = None,
        identifier: str | None = None,
        telecom: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        communication: str | None = None,
        address: str | None = None,
        address_city: str | None = None,
        address_state: str | None = None,
        address_postal_code: str | None = None,
        address_country: str | None = None,
        address_use=None,
    ):
        if org_id:
            stmt = stmt.where(PractitionerModel.tenant_id == org_id)
        if user_id:
            stmt = stmt.where(PractitionerModel.user_id == user_id)
        stmt = apply_token_filter(stmt, PractitionerModel.active, active)
        stmt = apply_token_filter(stmt, PractitionerModel.gender, gender)
        if family:
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerName.id).where(
                    PractitionerName.practitioner_pk == PractitionerModel.id,
                    PractitionerName.family.ilike(f"%{family}%"),
                ),
            )
        if given:
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerName.id).where(
                    PractitionerName.practitioner_pk == PractitionerModel.id,
                    func.array_to_string(PractitionerName.given, " ").ilike(
                        f"%{given}%"
                    ),
                ),
            )
        if name or phonetic:
            # `phonetic` has no real soundex/metaphone implementation here —
            # approximated as the same substring match as `name`, scoped to
            # family/given, same simplification every other string-match
            # filter in this project makes (see CLAUDE.md's conformance
            # testing notes on what the base R4 validator does and doesn't
            # catch — matching semantics aren't its job either).
            pattern = f"%{name or phonetic}%"
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerName.id).where(
                    PractitionerName.practitioner_pk == PractitionerModel.id,
                    or_(
                        PractitionerName.text.ilike(pattern),
                        PractitionerName.family.ilike(pattern),
                        func.array_to_string(PractitionerName.given, " ").ilike(
                            pattern
                        ),
                        func.array_to_string(PractitionerName.prefix, " ").ilike(
                            pattern
                        ),
                        func.array_to_string(PractitionerName.suffix, " ").ilike(
                            pattern
                        ),
                    ),
                ),
            )
        if identifier:
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerIdentifier.id).where(
                    PractitionerIdentifier.practitioner_pk == PractitionerModel.id,
                    PractitionerIdentifier.value == identifier,
                ),
            )
        if telecom:
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerTelecom.id).where(
                    PractitionerTelecom.practitioner_pk == PractitionerModel.id,
                    PractitionerTelecom.value == telecom,
                ),
            )
        if phone:
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerTelecom.id).where(
                    PractitionerTelecom.practitioner_pk == PractitionerModel.id,
                    PractitionerTelecom.system == "phone",
                    PractitionerTelecom.value == phone,
                ),
            )
        if email:
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerTelecom.id).where(
                    PractitionerTelecom.practitioner_pk == PractitionerModel.id,
                    PractitionerTelecom.system == "email",
                    PractitionerTelecom.value == email,
                ),
            )
        if communication:
            # Practitioner.communication (0..* CodeableConcept) — coding is a
            # real child table now, same EXISTS-join-to-parent pattern as
            # Organization.type — see app/repository/organization/core.py.
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerCommunicationCoding.id)
                .join(
                    PractitionerCommunication,
                    PractitionerCommunicationCoding.practitioner_communication_id
                    == PractitionerCommunication.id,
                )
                .where(
                    PractitionerCommunication.practitioner_pk == PractitionerModel.id,
                    PractitionerCommunicationCoding.code == communication,
                ),
            )
        if address:
            pattern = f"%{address}%"
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerAddress.id).where(
                    PractitionerAddress.practitioner_pk == PractitionerModel.id,
                    or_(
                        func.array_to_string(PractitionerAddress.line, " ").ilike(
                            pattern
                        ),
                        PractitionerAddress.city.ilike(pattern),
                        PractitionerAddress.district.ilike(pattern),
                        PractitionerAddress.state.ilike(pattern),
                        PractitionerAddress.country.ilike(pattern),
                        PractitionerAddress.postal_code.ilike(pattern),
                        PractitionerAddress.text.ilike(pattern),
                    ),
                ),
            )
        if address_city:
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerAddress.id).where(
                    PractitionerAddress.practitioner_pk == PractitionerModel.id,
                    PractitionerAddress.city.ilike(f"%{address_city}%"),
                ),
            )
        if address_state:
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerAddress.id).where(
                    PractitionerAddress.practitioner_pk == PractitionerModel.id,
                    PractitionerAddress.state.ilike(f"%{address_state}%"),
                ),
            )
        if address_postal_code:
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerAddress.id).where(
                    PractitionerAddress.practitioner_pk == PractitionerModel.id,
                    PractitionerAddress.postal_code == address_postal_code,
                ),
            )
        if address_country:
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerAddress.id).where(
                    PractitionerAddress.practitioner_pk == PractitionerModel.id,
                    PractitionerAddress.country.ilike(f"%{address_country}%"),
                ),
            )
        if address_use is not None:
            stmt = apply_child_exists_filter(
                stmt,
                select(PractitionerAddress.id).where(
                    PractitionerAddress.practitioner_pk == PractitionerModel.id,
                    PractitionerAddress.use == address_use,
                ),
            )
        return stmt

    async def list(
        self,
        org_id: str | None = None,
        user_id: str | None = None,
        active: bool | None = None,
        gender=None,
        family: str | None = None,
        given: str | None = None,
        name: str | None = None,
        phonetic: str | None = None,
        identifier: str | None = None,
        telecom: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        communication: str | None = None,
        address: str | None = None,
        address_city: str | None = None,
        address_state: str | None = None,
        address_postal_code: str | None = None,
        address_country: str | None = None,
        address_use=None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[PractitionerModel], int | None]:
        """Paginated, filtered, sorted list of practitioners. Returns
        (rows, total) — total is None when total_mode="none"."""
        async with self.session_factory() as session:
            filter_kwargs = {
                "org_id": org_id,
                "user_id": user_id,
                "active": active,
                "gender": gender,
                "family": family,
                "given": given,
                "name": name,
                "phonetic": phonetic,
                "identifier": identifier,
                "telecom": telecom,
                "phone": phone,
                "email": email,
                "communication": communication,
                "address": address,
                "address_city": address_city,
                "address_state": address_state,
                "address_postal_code": address_postal_code,
                "address_country": address_country,
                "address_use": address_use,
            }
            base = self._apply_list_filters(
                _with_relationships(select(PractitionerModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(PractitionerModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=PractitionerModel.practitioner_id,
                default_desc=True,
            )
            rows, total = await self._execute_paginated(
                session,
                base,
                count_base,
                sort_column=sort_column,
                sort_desc=sort_desc,
                limit=limit,
                offset=offset,
                total_mode=total_mode,
            )
        logger.debug(
            "Practitioners listed",
            extra={
                "event": "practitioner.listed",
                "returned": len(rows),
                "total": total,
                "limit": limit,
                "offset": offset,
                "filters": sorted(k for k, v in filter_kwargs.items() if v is not None),
            },
        )
        return rows, total

    async def get_me(
        self,
        user_id: str,
        org_id: str,
        **filters,
    ) -> tuple[list[PractitionerModel], int | None]:
        """Same filters as list(), always scoped to this user_id AND org_id."""
        return await self.list(org_id=org_id, user_id=user_id, **filters)

    # ── Delete ───────────────────────────────────────────────────────────
    # create()/patch() live in full.py — Practitioner has no separate
    # scalar-only variant, see PractitionerCreateSchema's docstring.

    async def delete(self, practitioner_id: int) -> bool:
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(
                PractitionerModel.practitioner_id == practitioner_id
            )
            p = (await session.execute(stmt)).scalars().first()
            if not p:
                return False
            try:
                await session.delete(p)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise
