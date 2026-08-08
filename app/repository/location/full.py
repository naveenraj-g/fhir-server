from sqlalchemy import delete, select

from app.core.logging import get_logger
from app.errors.domain import BusinessRuleViolationError
from app.models.location import (
    LocationAlias,
    LocationEndpoint,
    LocationHoursOfOperation,
    LocationIdentifier,
    LocationModel,
    LocationTelecom,
    LocationType,
)
from app.schemas.location import LocationCreateSchema, LocationPatchSchema

from ._shared import (
    _location_ref_kwargs,
    _org_ref_kwargs,
    _parse_endpoint_ref,
    _parse_location_ref,
    _parse_org_ref,
    _partof_chain_contains,
    _reference_kwargs,
    _validate_reference,
)

logger = get_logger(__name__)

# Sub-resource list fields on the create/patch payloads. A supplied list (even
# `[]`) replaces the corresponding rows wholesale; an omitted one is untouched.
_SUB = {"identifier", "type", "alias", "telecom", "hours_of_operation", "endpoint"}


def _join_lines(values: list[str] | None) -> str | None:
    """Address.line[] is stored comma-separated (the `line[]` exception in
    /fhir-db-model) — same as every other flattened Address in this project."""
    return ", ".join(values) if values else None


def _join_days(values: list | None) -> str | None:
    """hoursOfOperation.daysOfWeek[] is stored comma-separated — see
    LocationHoursOfOperation's docstring. Values arrive as LocationDayOfWeek
    enum members from the schema layer, so unwrap to `.value` before joining."""
    if not values:
        return None
    return ",".join(getattr(v, "value", v) for v in values)


class _FullMixin:
    """create_full/patch_full — the two atomic nested-write orchestrators that
    touch all 6 sub-resource types (plus core scalar fields) in one
    transaction."""

    def _build_identifier(self, i, location_pk: int, org_id: str, actor: str | None):
        return LocationIdentifier(
            location_id=location_pk,
            org_id=org_id,
            use=i.use,
            type_system=i.type_system,
            type_version=i.type_version,
            type_code=i.type_code,
            type_display=i.type_display,
            type_text=i.type_text,
            type_user_selected=i.type_user_selected,
            system=i.system,
            value=i.value,
            period_start=i.period_start,
            period_end=i.period_end,
            **_org_ref_kwargs("assigner", i.assigner, i.assigner_display),
            **_reference_kwargs("assigner", i),
            created_by=actor,
        )

    @staticmethod
    def _build_type(t, location_pk: int, org_id: str, actor: str | None):
        return LocationType(
            location_id=location_pk,
            org_id=org_id,
            coding_system=t.coding_system,
            coding_version=t.coding_version,
            coding_code=t.coding_code,
            coding_display=t.coding_display,
            text=t.text,
            coding_user_selected=t.coding_user_selected,
            created_by=actor,
        )

    @staticmethod
    def _build_alias(a, location_pk: int, org_id: str, actor: str | None):
        return LocationAlias(
            location_id=location_pk,
            org_id=org_id,
            value=a.value,
            created_by=actor,
        )

    @staticmethod
    def _build_telecom(t, location_pk: int, org_id: str, actor: str | None):
        return LocationTelecom(
            location_id=location_pk,
            org_id=org_id,
            system=t.system,
            value=t.value,
            use=t.use,
            rank=t.rank,
            period_start=t.period_start,
            period_end=t.period_end,
            created_by=actor,
        )

    @staticmethod
    def _build_hours(h, location_pk: int, org_id: str, actor: str | None):
        return LocationHoursOfOperation(
            location_id=location_pk,
            org_id=org_id,
            days_of_week=_join_days(h.days_of_week),
            all_day=h.all_day,
            opening_time=h.opening_time,
            closing_time=h.closing_time,
            created_by=actor,
        )

    @staticmethod
    def _build_endpoint(e, location_pk: int, org_id: str, actor: str | None):
        ep_type, ep_id = (
            _parse_endpoint_ref(e.reference) if e.reference else (None, None)
        )
        return LocationEndpoint(
            location_id=location_pk,
            org_id=org_id,
            reference_type=ep_type,
            reference_id=ep_id,
            reference_display=e.reference_display,
            **_reference_kwargs("reference", e),
            created_by=actor,
        )

    async def create_full(
        self,
        payload: LocationCreateSchema,
        org_id: str,
        created_by: str | None = None,
    ) -> LocationModel:
        """Create a Location plus any combination of its 6 sub-resource lists,
        atomically in one DB transaction. Every list on the payload is
        optional; only the ones supplied get inserted.

        No partOf cycle check is needed here (unlike patch_full): the row
        doesn't exist yet, so it cannot already be an ancestor of the location
        it is being attached to.
        """
        mo_type, mo_id = (
            _parse_org_ref(payload.managing_organization)
            if payload.managing_organization
            else (None, None)
        )
        po_type, po_id = (
            _parse_location_ref(payload.part_of) if payload.part_of else (None, None)
        )

        async with self.session_factory() as session:
            await _validate_reference(
                session, org_id, mo_type, mo_id, "managingOrganization"
            )
            await _validate_reference(session, org_id, po_type, po_id, "partOf")

            loc = LocationModel(
                org_id=org_id,
                created_by=created_by,
                status=payload.status,
                mode=payload.mode,
                operational_status_system=payload.operational_status_system,
                operational_status_version=payload.operational_status_version,
                operational_status_code=payload.operational_status_code,
                operational_status_display=payload.operational_status_display,
                operational_status_user_selected=payload.operational_status_user_selected,
                name=payload.name,
                description=payload.description,
                address_use=payload.address_use,
                address_type=payload.address_type,
                address_text=payload.address_text,
                address_line=_join_lines(payload.address_line),
                address_city=payload.address_city,
                address_district=payload.address_district,
                address_state=payload.address_state,
                address_postal_code=payload.address_postal_code,
                address_country=payload.address_country,
                address_period_start=payload.address_period_start,
                address_period_end=payload.address_period_end,
                physical_type_system=payload.physical_type_system,
                physical_type_version=payload.physical_type_version,
                physical_type_code=payload.physical_type_code,
                physical_type_display=payload.physical_type_display,
                physical_type_text=payload.physical_type_text,
                physical_type_user_selected=payload.physical_type_user_selected,
                position_longitude=payload.position_longitude,
                position_latitude=payload.position_latitude,
                position_altitude=payload.position_altitude,
                availability_exceptions=payload.availability_exceptions,
                **_org_ref_kwargs(
                    "managing_organization",
                    payload.managing_organization,
                    payload.managing_organization_display,
                ),
                **_reference_kwargs("managing_organization", payload),
                **_location_ref_kwargs(
                    "part_of", payload.part_of, payload.part_of_display
                ),
                **_reference_kwargs("part_of", payload),
            )
            session.add(loc)
            await session.flush()

            if payload.identifier:
                for i in payload.identifier:
                    a_type, a_id = (
                        _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    )
                    await _validate_reference(
                        session, org_id, a_type, a_id, "identifier.assigner"
                    )
                    session.add(
                        self._build_identifier(i, loc.id, org_id, created_by)
                    )

            for t in payload.type or []:
                session.add(self._build_type(t, loc.id, org_id, created_by))
            for a in payload.alias or []:
                session.add(self._build_alias(a, loc.id, org_id, created_by))
            for t in payload.telecom or []:
                session.add(self._build_telecom(t, loc.id, org_id, created_by))
            for h in payload.hours_of_operation or []:
                session.add(self._build_hours(h, loc.id, org_id, created_by))
            for e in payload.endpoint or []:
                session.add(self._build_endpoint(e, loc.id, org_id, created_by))

            try:
                await session.commit()
                await session.refresh(loc)
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_location_id(loc.location_id)

    async def patch_full(
        self,
        location_id: int,
        payload: LocationPatchSchema,
        updated_by: str | None = None,
    ) -> LocationModel | None:
        """Patches core scalar fields and, for each sub-resource list that is
        supplied — even `[]` — atomically deletes all existing rows and inserts
        the new ones. Lists omitted from the payload are left untouched."""
        async with self.session_factory() as session:
            stmt = select(LocationModel).where(
                LocationModel.location_id == location_id
            )
            loc = (await session.execute(stmt)).scalars().first()
            if not loc:
                return None

            data = payload.model_dump(exclude_unset=True)
            for field, value in data.items():
                if field in _SUB:
                    continue

                if field == "managing_organization":
                    if value is not None:
                        mo_type, mo_id = _parse_org_ref(value)
                        await _validate_reference(
                            session,
                            loc.org_id,
                            mo_type,
                            mo_id,
                            "managingOrganization",
                        )
                        loc.managing_organization_type = mo_type
                        loc.managing_organization_id = mo_id
                    else:
                        loc.managing_organization_type = None
                        loc.managing_organization_id = None

                elif field == "part_of":
                    if value is not None:
                        po_type, po_id = _parse_location_ref(value)
                        await _validate_reference(
                            session, loc.org_id, po_type, po_id, "partOf"
                        )
                        # Walking UP from the proposed parent: if this location
                        # already appears among its ancestors (or is the parent
                        # itself), attaching would close a loop.
                        if await _partof_chain_contains(
                            session, loc.org_id, po_id, loc.location_id
                        ):
                            raise BusinessRuleViolationError(
                                f"Setting partOf to Location/{po_id} would create a "
                                "circular location hierarchy."
                            )
                        loc.part_of_type = po_type
                        loc.part_of_id = po_id
                    else:
                        loc.part_of_type = None
                        loc.part_of_id = None

                elif field == "address_line":
                    loc.address_line = _join_lines(value)

                else:
                    setattr(loc, field, value)

            if updated_by is not None:
                loc.updated_by = updated_by

            if payload.identifier is not None:
                await session.execute(
                    delete(LocationIdentifier).where(
                        LocationIdentifier.location_id == loc.id
                    )
                )
                for i in payload.identifier:
                    a_type, a_id = (
                        _parse_org_ref(i.assigner) if i.assigner else (None, None)
                    )
                    await _validate_reference(
                        session, loc.org_id, a_type, a_id, "identifier.assigner"
                    )
                    session.add(
                        self._build_identifier(i, loc.id, loc.org_id, updated_by)
                    )

            if payload.type is not None:
                await session.execute(
                    delete(LocationType).where(LocationType.location_id == loc.id)
                )
                for t in payload.type:
                    session.add(self._build_type(t, loc.id, loc.org_id, updated_by))

            if payload.alias is not None:
                await session.execute(
                    delete(LocationAlias).where(LocationAlias.location_id == loc.id)
                )
                for a in payload.alias:
                    session.add(self._build_alias(a, loc.id, loc.org_id, updated_by))

            if payload.telecom is not None:
                await session.execute(
                    delete(LocationTelecom).where(
                        LocationTelecom.location_id == loc.id
                    )
                )
                for t in payload.telecom:
                    session.add(
                        self._build_telecom(t, loc.id, loc.org_id, updated_by)
                    )

            if payload.hours_of_operation is not None:
                await session.execute(
                    delete(LocationHoursOfOperation).where(
                        LocationHoursOfOperation.location_id == loc.id
                    )
                )
                for h in payload.hours_of_operation:
                    session.add(self._build_hours(h, loc.id, loc.org_id, updated_by))

            if payload.endpoint is not None:
                await session.execute(
                    delete(LocationEndpoint).where(
                        LocationEndpoint.location_id == loc.id
                    )
                )
                for e in payload.endpoint:
                    session.add(
                        self._build_endpoint(e, loc.id, loc.org_id, updated_by)
                    )

            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise

            # Which sub-resource lists were wholesale replaced. Only the
            # repository knows this — the service sees "a patch happened", and
            # "replaced telecom with 0 rows" vs. "left telecom untouched" is
            # exactly the distinction that turns into a support ticket.
            replaced = sorted(_SUB & set(data.keys()))
            if replaced:
                logger.debug(
                    "Location sub-resource lists replaced",
                    extra={
                        "event": "location.sublists_replaced",
                        "location_id": location_id,
                        "replaced": replaced,
                    },
                )

        return await self.get_by_location_id(location_id)
