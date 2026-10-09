from sqlalchemy import func, select

from app.models.fhir_profile.enums import FhirProfileScopeLevel, FhirProfileStatus
from app.models.fhir_profile.fhir_profile import FhirProfile


class _CoreMixin:
    """Plain reads, plus the draft -> active -> retired write path for the
    country/organization layers (base is seeded once, never admin-editable
    — see app/fhir_profile/seed_base_profiles.py)."""

    async def get_base(self, resource_type: str) -> FhirProfile | None:
        """No status filter, deliberately — base has no draft/active/
        retired lifecycle (see uq_fhir_profile_base_singleton's own
        comment on the model): there's exactly one HL7-published row per
        resource_type, and its `status` mirrors HL7's own real maturity
        declaration for that resource (which can legitimately be "draft"
        even for a normative R4 resource, e.g. Organization), not whether
        this row is "in effect" — for base, it always is."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(FhirProfile)
                .where(FhirProfile.resource_type == resource_type)
                .where(FhirProfile.scope_level == FhirProfileScopeLevel.base)
                .order_by(FhirProfile.id.desc())
            )
            return result.scalars().first()

    async def get_country(
        self, resource_type: str, country_code: str
    ) -> FhirProfile | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(FhirProfile)
                .where(FhirProfile.resource_type == resource_type)
                .where(FhirProfile.scope_level == FhirProfileScopeLevel.country)
                .where(FhirProfile.scope_id == country_code)
                .where(FhirProfile.status == FhirProfileStatus.active)
                .order_by(FhirProfile.id.desc())
            )
            return result.scalars().first()

    async def get_organization(
        self, resource_type: str, org_id: str
    ) -> FhirProfile | None:
        """scope_id here is the owning organization's public org_id (see
        FhirProfile's own docstring), not a country code — same column,
        different meaning depending on scope_level."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(FhirProfile)
                .where(FhirProfile.resource_type == resource_type)
                .where(FhirProfile.scope_level == FhirProfileScopeLevel.organization)
                .where(FhirProfile.scope_id == org_id)
                .where(FhirProfile.status == FhirProfileStatus.active)
                .order_by(FhirProfile.id.desc())
            )
            return result.scalars().first()

    async def get_by_id(self, profile_id: int) -> FhirProfile | None:
        async with self.session_factory() as session:
            return await session.get(FhirProfile, profile_id)

    async def list_profiles(
        self,
        resource_type: str | None,
        scope_level: str | None,
        scope_id: str | None,
        status: str | None,
        limit: int,
        offset: int,
    ) -> tuple[int, list[FhirProfile]]:
        async with self.session_factory() as session:
            stmt = select(FhirProfile)
            if resource_type:
                stmt = stmt.where(FhirProfile.resource_type == resource_type)
            if scope_level:
                stmt = stmt.where(FhirProfile.scope_level == scope_level)
            if scope_id:
                stmt = stmt.where(FhirProfile.scope_id == scope_id)
            if status:
                stmt = stmt.where(FhirProfile.status == status)

            count = await session.scalar(select(func.count()).select_from(stmt.subquery()))
            rows = await session.execute(
                stmt.order_by(FhirProfile.id.desc()).limit(limit).offset(offset)
            )
            return count or 0, list(rows.scalars().all())

    async def create_profile(
        self,
        resource_type: str,
        scope_level: str,
        scope_id: str | None,
        canonical_url: str,
        version: str,
        structure_definition: dict,
        parent_profile_id: int | None,
        created_by: str,
    ) -> FhirProfile:
        """Always inserted as status='draft' — there is no create-as-active
        path; activate_profile() is the only way a row becomes active, so
        the retire-previous-active step can never be skipped."""
        async with self.session_factory() as session:
            profile = FhirProfile(
                resource_type=resource_type,
                scope_level=scope_level,
                scope_id=scope_id,
                canonical_url=canonical_url,
                version=version,
                status=FhirProfileStatus.draft,
                structure_definition=structure_definition,
                parent_profile_id=parent_profile_id,
                created_by=created_by,
                updated_by=created_by,
            )
            session.add(profile)
            await session.commit()
            await session.refresh(profile)
            return profile

    async def update_draft(
        self, profile_id: int, structure_definition: dict, updated_by: str
    ) -> FhirProfile | None:
        """Caller (service layer) must have already confirmed the row is
        still status='draft' — this method doesn't re-check, since the
        sidecar re-validation and the draft-only guard both happen there."""
        async with self.session_factory() as session:
            profile = await session.get(FhirProfile, profile_id)
            if not profile:
                return None
            profile.structure_definition = structure_definition
            profile.updated_by = updated_by
            await session.commit()
            await session.refresh(profile)
            return profile

    async def activate(self, profile_id: int, updated_by: str) -> FhirProfile | None:
        """Atomically retires whichever row is currently active for the
        same (resource_type, scope_level, scope_id) and activates this one
        — both updates happen in the same transaction so the partial unique
        index (uq_fhir_profile_active_base / uq_fhir_profile_active_scoped)
        is never violated mid-flight, and a crash between the two can never
        leave the scope with zero or two active rows."""
        async with self.session_factory() as session:
            profile = await session.get(FhirProfile, profile_id)
            if not profile:
                return None

            previous_active = (
                await session.execute(
                    select(FhirProfile)
                    .where(FhirProfile.resource_type == profile.resource_type)
                    .where(FhirProfile.scope_level == profile.scope_level)
                    .where(FhirProfile.scope_id == profile.scope_id)
                    .where(FhirProfile.status == FhirProfileStatus.active)
                    .where(FhirProfile.id != profile.id)
                    .with_for_update()
                )
            ).scalars().all()
            for other in previous_active:
                other.status = FhirProfileStatus.retired

            profile.status = FhirProfileStatus.active
            profile.updated_by = updated_by
            await session.commit()
            await session.refresh(profile)
            return profile

    async def delete_profile(self, profile_id: int) -> FhirProfile | None:
        """Returns the deleted row's own data (specifically `status`, which
        the service layer checks before calling this at all) rather than a
        bare bool, so callers never need a second read to log what was
        removed."""
        async with self.session_factory() as session:
            profile = await session.get(FhirProfile, profile_id)
            if not profile:
                return None
            await session.delete(profile)
            await session.commit()
            return profile
