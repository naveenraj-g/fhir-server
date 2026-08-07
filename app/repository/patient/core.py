from sqlalchemy import func, or_, select

from app.core.filters import (
    apply_child_exists_filter,
    apply_fhir_date_filter,
    apply_token_filter,
    parse_reference,
)
from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.enums import OrganizationReferenceType
from app.models.patient.enums import (
    AddressUse,
    PatientGender,
    PatientGeneralPractitionerType,
    PatientLinkOtherType,
)
from app.models.patient import (
    PatientAddress,
    PatientCommunication,
    PatientGeneralPractitioner,
    PatientIdentifier,
    PatientLink,
    PatientModel,
    PatientName,
    PatientTelecom,
)
from app.schemas.enums import ContactPointSystem
from app.schemas.patient import PatientCreateSchema, PatientPatchSchema

from ._shared import (
    _SORTABLE_FIELDS,
    _org_ref_kwargs,
    _parse_org_ref,
    _reference_kwargs,
    _validate_reference,
    _with_relationships,
)


logger = get_logger(__name__)


class _CoreMixin:
    """Core Patient CRUD (everything except create_full/patch_full, which
    live in full.py) plus the internal lookup helpers every sub-resource
    mixin shares (_get_internal, list filtering)."""

    # ── Read ──────────────────────────────────────────────────────────────────

    async def _fetch_by_patient_id(
        self,
        patient_id: int,
        *,
        user_id: str | None = None,
        org_id: str | None = None,
        core: bool = False,
    ) -> PatientModel | None:
        """Shared query-builder behind every by-ID lookup variant below.
        core=True skips the 9 selectinload relationships (scalars only);
        user_id/org_id, when supplied, each add their own WHERE filter
        (tenant/ownership scoping) — omitted, no filter on that dimension.
        Both may be combined (AND) when both are supplied."""
        async with self.session_factory() as session:
            stmt = select(PatientModel).where(PatientModel.patient_id == patient_id)
            if user_id is not None:
                stmt = stmt.where(PatientModel.user_id == user_id)
            if org_id is not None:
                stmt = stmt.where(PatientModel.org_id == org_id)
            if not core:
                stmt = _with_relationships(stmt)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_by_patient_id(self, patient_id: int) -> PatientModel | None:
        """Full lookup by public patient_id, eager-loading every sub-resource
        relationship. Backs GET /{patient_id}."""
        return await self._fetch_by_patient_id(patient_id)

    async def get_core_by_patient_id(self, patient_id: int) -> PatientModel | None:
        """
        Same lookup as get_by_patient_id() but WITHOUT the 9 selectinload
        options — one query against the patients table only, no fan-out to
        the sub-resource child tables. Backs GET /{patient_id}/core.

        Callers must go through to_plain_patient_core()/to_fhir_patient_core()
        (never to_plain_patient()/to_fhir_patient()) to format the result —
        those touch the relationship attributes this query leaves unloaded.
        """
        return await self._fetch_by_patient_id(patient_id, core=True)

    async def get_by_patient_id_in_org(
        self, patient_id: int, user_id: str | None, org_id: str | None
    ) -> PatientModel | None:
        """Full lookup scoped to whichever of user_id/org_id are supplied
        (AND together when both are) — returns None unless every supplied
        filter matches."""
        return await self._fetch_by_patient_id(
            patient_id, user_id=user_id, org_id=org_id
        )

    async def get_core_by_patient_id_in_org(
        self, patient_id: int, org_id: str | None = None, user_id: str | None = None
    ) -> PatientModel | None:
        """Same as get_by_patient_id_in_org() but scalars only (no
        selectinload) — the org-scoped counterpart to get_core_by_patient_id().
        Backs GET /{patient_id}/core when org-scoped."""
        return await self._fetch_by_patient_id(
            patient_id, user_id=user_id, org_id=org_id, core=True
        )

    async def patient_belongs_to_org(self, patient_id: int, org_id: str) -> bool:
        """Lightweight existence check (no eager-loading) for tenant-ownership
        gates on write routes — True iff the patient exists AND belongs to
        org_id."""
        async with self.session_factory() as session:
            stmt = select(PatientModel.id).where(
                PatientModel.patient_id == patient_id,
                PatientModel.org_id == org_id,
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none() is not None

    async def get_by_user_id(self, user_id: str) -> PatientModel | None:
        """Lookup by the gateway-forwarded user_id — used to find "my own" patient profile."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PatientModel).where(PatientModel.user_id == user_id)
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_me(self, user_id: str, org_id: str) -> PatientModel | None:
        """Lookup scoped to both user_id and org_id — backs the GET /me route."""
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(PatientModel).where(
                    PatientModel.user_id == user_id,
                    PatientModel.org_id == org_id,
                )
            )
            result = await session.execute(stmt)
            return result.scalars().first()

    def _apply_list_filters(
        self,
        stmt,
        user_id,
        org_id,
        family: str | None = None,
        given: str | None = None,
        name: str | None = None,
        gender: PatientGender | None = None,
        active=None,
        identifier: str | None = None,
        birthdate: list[str] | None = None,
        death_date: list[str] | None = None,
        deceased: bool | None = None,
        address: str | None = None,
        address_city: str | None = None,
        address_state: str | None = None,
        address_postal_code: str | None = None,
        address_country: str | None = None,
        address_use: AddressUse | None = None,
        telecom: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        language: str | None = None,
        general_practitioner: str | None = None,
        organization: str | None = None,
        link: str | None = None,
    ):
        if user_id:
            stmt = stmt.where(PatientModel.user_id == user_id)
        if org_id:
            stmt = stmt.where(PatientModel.org_id == org_id)
        if family:
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientName.id).where(
                    PatientName.patient_id == PatientModel.id,
                    PatientName.family.ilike(f"%{family}%"),
                ),
            )
        if given:
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientName.id).where(
                    PatientName.patient_id == PatientModel.id,
                    PatientName.given.ilike(f"%{given}%"),
                ),
            )
        if name:
            # FHIR "name" — a single term matched against any HumanName
            # sub-field (family, given, prefix, suffix, text), unlike
            # family/given above which each target one specific sub-field.
            pattern = f"%{name}%"
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientName.id).where(
                    PatientName.patient_id == PatientModel.id,
                    or_(
                        PatientName.family.ilike(pattern),
                        PatientName.given.ilike(pattern),
                        PatientName.prefix.ilike(pattern),
                        PatientName.suffix.ilike(pattern),
                        PatientName.text.ilike(pattern),
                    ),
                ),
            )
        stmt = apply_token_filter(stmt, PatientModel.gender, gender)
        stmt = apply_token_filter(stmt, PatientModel.active, active)

        # ── New filters — see dev-docs/12-search-and-filter-standards.md (fhir-gql repo) ──
        if identifier:
            # Identifier.value is an exact business-identifier match (MRN/SSN/etc.),
            # not a substring search — a partial identifier match isn't a meaningful
            # clinical query the way a partial name search is.
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientIdentifier.id).where(
                    PatientIdentifier.patient_id == PatientModel.id,
                    PatientIdentifier.value == identifier,
                ),
            )
        stmt = apply_fhir_date_filter(stmt, PatientModel.birth_date, birthdate)
        stmt = apply_fhir_date_filter(stmt, PatientModel.deceased_datetime, death_date)
        if deceased is not None:
            # FHIR semantics: "deceased" means deceased[x] is populated at all
            # (boolean true OR a death date present) — not a literal equality
            # check on deceased_boolean alone.
            if deceased:
                stmt = stmt.where(
                    or_(
                        PatientModel.deceased_boolean.is_(True),
                        PatientModel.deceased_datetime.isnot(None),
                    )
                )
            else:
                stmt = stmt.where(
                    PatientModel.deceased_boolean.isnot(True),
                    PatientModel.deceased_datetime.is_(None),
                )
        if address:
            # Composite string search across every Address sub-field, per the
            # FHIR "address" search parameter (as opposed to address-city
            # etc. below, which each target one specific sub-field).
            pattern = f"%{address}%"
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientAddress.id).where(
                    PatientAddress.patient_id == PatientModel.id,
                    or_(
                        PatientAddress.line.ilike(pattern),
                        PatientAddress.city.ilike(pattern),
                        PatientAddress.district.ilike(pattern),
                        PatientAddress.state.ilike(pattern),
                        PatientAddress.country.ilike(pattern),
                        PatientAddress.postal_code.ilike(pattern),
                        PatientAddress.text.ilike(pattern),
                    ),
                ),
            )
        if address_city:
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientAddress.id).where(
                    PatientAddress.patient_id == PatientModel.id,
                    PatientAddress.city.ilike(f"%{address_city}%"),
                ),
            )
        if address_state:
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientAddress.id).where(
                    PatientAddress.patient_id == PatientModel.id,
                    PatientAddress.state.ilike(f"%{address_state}%"),
                ),
            )
        if address_postal_code:
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientAddress.id).where(
                    PatientAddress.patient_id == PatientModel.id,
                    PatientAddress.postal_code == address_postal_code,
                ),
            )
        if address_country:
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientAddress.id).where(
                    PatientAddress.patient_id == PatientModel.id,
                    PatientAddress.country.ilike(f"%{address_country}%"),
                ),
            )
        if address_use is not None:
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientAddress.id).where(
                    PatientAddress.patient_id == PatientModel.id,
                    PatientAddress.use == address_use,
                ),
            )
        if telecom:
            # Any telecom system — unlike email/phone below, which are each
            # scoped to one specific system.
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientTelecom.id).where(
                    PatientTelecom.patient_id == PatientModel.id,
                    PatientTelecom.value.ilike(f"%{telecom}%"),
                ),
            )
        if email:
            # system-scoped EXISTS — matches only telecom rows whose system is
            # specifically "email", so an email filter can never accidentally
            # match a phone number that happens to contain the same substring.
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientTelecom.id).where(
                    PatientTelecom.patient_id == PatientModel.id,
                    PatientTelecom.system == ContactPointSystem.email,
                    PatientTelecom.value.ilike(f"%{email}%"),
                ),
            )
        if phone:
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientTelecom.id).where(
                    PatientTelecom.patient_id == PatientModel.id,
                    PatientTelecom.system == ContactPointSystem.phone,
                    PatientTelecom.value.ilike(f"%{phone}%"),
                ),
            )
        if language:
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientCommunication.id).where(
                    PatientCommunication.patient_id == PatientModel.id,
                    PatientCommunication.language_code == language,
                ),
            )
        if general_practitioner:
            gp_type, gp_id = parse_reference(
                general_practitioner, PatientGeneralPractitionerType
            )
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientGeneralPractitioner.id).where(
                    PatientGeneralPractitioner.patient_id == PatientModel.id,
                    PatientGeneralPractitioner.reference_type == gp_type,
                    PatientGeneralPractitioner.reference_id == gp_id,
                ),
            )
        if organization:
            # managingOrganization is a direct column (0..1 reference), not a
            # child table, so it's a plain equality filter rather than an
            # EXISTS — the parsed id is the referenced Organization's PUBLIC
            # id, exactly as stored by parse_reference at write time.
            _, org_ref_id = parse_reference(organization, OrganizationReferenceType)
            stmt = apply_token_filter(
                stmt, PatientModel.managing_organization_id, org_ref_id
            )
        if link:
            other_type, other_id = parse_reference(link, PatientLinkOtherType)
            stmt = apply_child_exists_filter(
                stmt,
                select(PatientLink.id).where(
                    PatientLink.patient_id == PatientModel.id,
                    PatientLink.other_type == other_type,
                    PatientLink.other_id == other_id,
                ),
            )

        return stmt

    async def list(
        self,
        user_id: str | None = None,
        org_id: str | None = None,
        family: str | None = None,
        given: str | None = None,
        name: str | None = None,
        gender: PatientGender | None = None,
        active: bool | None = None,
        identifier: str | None = None,
        birthdate: list[str] | None = None,
        death_date: list[str] | None = None,
        deceased: bool | None = None,
        address: str | None = None,
        address_city: str | None = None,
        address_state: str | None = None,
        address_postal_code: str | None = None,
        address_country: str | None = None,
        address_use: AddressUse | None = None,
        telecom: str | None = None,
        email: str | None = None,
        phone: str | None = None,
        language: str | None = None,
        general_practitioner: str | None = None,
        organization: str | None = None,
        link: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[PatientModel], int | None]:
        """Paginated, filtered, sorted list of patients. Backs GET / and, with
        user_id/org_id pinned, GET /me. Returns (rows, total) — total is None
        when total_mode="none"."""
        async with self.session_factory() as session:
            # Every filter argument is applied identically to both the row
            # query and the count query so the two can never drift apart —
            # see BaseRepository._execute_paginated's docstring.
            filter_kwargs = {
                "user_id": user_id,
                "org_id": org_id,
                "family": family,
                "given": given,
                "name": name,
                "gender": gender,
                "active": active,
                "identifier": identifier,
                "birthdate": birthdate,
                "death_date": death_date,
                "deceased": deceased,
                "address": address,
                "address_city": address_city,
                "address_state": address_state,
                "address_postal_code": address_postal_code,
                "address_country": address_country,
                "address_use": address_use,
                "telecom": telecom,
                "email": email,
                "phone": phone,
                "language": language,
                "general_practitioner": general_practitioner,
                "organization": organization,
                "link": link,
            }
            base = self._apply_list_filters(
                _with_relationships(select(PatientModel)), **filter_kwargs
            )
            count_base = self._apply_list_filters(
                select(func.count()).select_from(PatientModel), **filter_kwargs
            )
            sort_column, sort_desc = resolve_sort(
                sort,
                _SORTABLE_FIELDS,
                default_column=PatientModel.patient_id,
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
            "Patients listed",
            extra={
                "event": "patient.listed",
                "returned": len(rows),
                "total": total,
                "limit": limit,
                "offset": offset,
                "filters": sorted(
                    k for k, v in filter_kwargs.items() if v is not None
                ),
            },
        )
        return rows, total

    # ── Write ─────────────────────────────────────────────────────────────────

    async def create(
        self,
        payload: PatientCreateSchema,
        user_id: str | None,
        org_id: str,
        created_by: str | None = None,
    ) -> PatientModel:
        """Create a Patient from its core scalar fields only — no sub-resources.
        Use create_full() to create sub-resources in the same request."""
        mo_type, mo_id = (
            _parse_org_ref(payload.managing_organization)
            if payload.managing_organization
            else (None, None)
        )
        async with self.session_factory() as session:
            await _validate_reference(session, org_id, mo_type, mo_id, "managingOrganization")
            patient = PatientModel(
                user_id=user_id,
                org_id=org_id,
                active=payload.active,
                gender=payload.gender,
                birth_date=payload.birth_date,
                deceased_boolean=payload.deceased_boolean,
                deceased_datetime=payload.deceased_datetime,
                marital_status_system=payload.marital_status_system,
                marital_status_version=payload.marital_status_version,
                marital_status_code=payload.marital_status_code,
                marital_status_display=payload.marital_status_display,
                marital_status_text=payload.marital_status_text,
                marital_status_user_selected=payload.marital_status_user_selected,
                multiple_birth_boolean=payload.multiple_birth_boolean,
                multiple_birth_integer=payload.multiple_birth_integer,
                **_org_ref_kwargs(
                    "managing_organization",
                    payload.managing_organization,
                    payload.managing_organization_display,
                ),
                **_reference_kwargs("managing_organization", payload),
                created_by=created_by,
            )
            try:
                session.add(patient)
                await session.commit()
                await session.refresh(patient)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_patient_id(patient.patient_id)

    async def patch(
        self,
        patient_id: int,
        payload: PatientPatchSchema,
        updated_by: str | None = None,
    ) -> PatientModel | None:
        """Partial update of core scalar fields only (model_dump(exclude_unset=True)
        drives which columns get written). Sub-resources are untouched — use
        patch_full() to also replace sub-resource lists in the same call."""
        async with self.session_factory() as session:
            stmt = select(PatientModel).where(PatientModel.patient_id == patient_id)
            result = await session.execute(stmt)
            patient = result.scalars().first()

            if not patient:
                return None

            for field, value in payload.model_dump(exclude_unset=True).items():
                if field == "managing_organization":
                    if value is not None:
                        ref_type, ref_id = _parse_org_ref(value)
                        await _validate_reference(
                            session, patient.org_id, ref_type, ref_id, "managingOrganization"
                        )
                        patient.managing_organization_type = ref_type
                        patient.managing_organization_id = ref_id
                    else:
                        patient.managing_organization_type = None
                        patient.managing_organization_id = None
                else:
                    setattr(patient, field, value)
            if updated_by is not None:
                patient.updated_by = updated_by

            try:
                await session.commit()
                await session.refresh(patient)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_patient_id(patient_id)

    async def delete(self, patient_id: int) -> bool:
        """Permanently deletes the Patient row — sub-resource rows cascade
        via the FK relationships' cascade="all, delete-orphan"."""
        async with self.session_factory() as session:
            stmt = select(PatientModel).where(PatientModel.patient_id == patient_id)
            result = await session.execute(stmt)
            patient = result.scalars().first()

            if not patient:
                return False

            try:
                await session.delete(patient)
                await session.commit()
                return True
            except Exception:
                await session.rollback()
                raise

    # ── Sub-resource mutations ─────────────────────────────────────────────────

    async def _get_internal(self, session, patient_id: int) -> PatientModel | None:
        """Fetch by public patient_id — internal PK only, no relationships loaded."""
        result = await session.execute(
            select(PatientModel).where(PatientModel.patient_id == patient_id)
        )
        return result.scalars().first()
