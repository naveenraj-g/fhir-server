from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant, fhir_split, fhir_telecom

if TYPE_CHECKING:
    from app.models.location import (
        LocationEndpoint,
        LocationHoursOfOperation,
        LocationIdentifier,
        LocationModel,
    )


def _fhir_coding_list(codings) -> list[dict]:
    """Render a list of FhirCodingMixin-shaped rows as a FHIR `coding[]`
    array — shared by Location.type, Location.identifier.type, and
    Location.physicalType, all three being real 0..* child tables now (a
    deployment may need its own custom code alongside a standard-terminology
    crosswalk at once) — mirrors
    app.fhir.mappers.organization.fhir._fhir_coding_list."""
    result = []
    for c in codings or []:
        entry = {
            k: v
            for k, v in {
                "system": c.system,
                "version": c.version,
                "code": c.code,
                "display": c.display,
                "userSelected": c.user_selected,
            }.items()
            if v is not None
        }
        if entry:
            result.append(entry)
    return result


def _fhir_reference(obj, prefix: str) -> dict:
    """Build a FHIR Reference dict for a `{prefix}_type`/`{prefix}_id`/`{prefix}_display`
    resolved reference, with a `{prefix}_identifier_*` logical-reference (Identifier)
    fallback for when the target isn't a resource in this system. Shared by every
    flattened Reference field on Location (identifier.assigner, managingOrganization,
    partOf, endpoint) — mirrors app.fhir.mappers.organization.fhir._fhir_reference."""
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    display = getattr(obj, f"{prefix}_display", None)

    entry: dict = {}
    if ref_type and ref_id:
        entry["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        entry["display"] = display

    id_use = getattr(obj, f"{prefix}_identifier_use", None)
    id_type_system = getattr(obj, f"{prefix}_identifier_type_system", None)
    id_type_version = getattr(obj, f"{prefix}_identifier_type_version", None)
    id_type_code = getattr(obj, f"{prefix}_identifier_type_code", None)
    id_type_display = getattr(obj, f"{prefix}_identifier_type_display", None)
    id_type_text = getattr(obj, f"{prefix}_identifier_type_text", None)
    id_type_user_selected = getattr(
        obj, f"{prefix}_identifier_type_user_selected", None
    )
    id_system = getattr(obj, f"{prefix}_identifier_system", None)
    id_value = getattr(obj, f"{prefix}_identifier_value", None)
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)

    if (
        id_use
        or id_type_system
        or id_type_code
        or id_type_text
        or id_system
        or id_value
    ):
        identifier: dict = {}
        if id_use:
            identifier["use"] = fhir_enum(id_use)
        if id_type_system or id_type_code or id_type_text:
            type_cc: dict = {}
            if id_type_system or id_type_code:
                type_cc["coding"] = [
                    {
                        k: v
                        for k, v in {
                            "system": id_type_system,
                            "version": id_type_version,
                            "code": id_type_code,
                            "display": id_type_display,
                            "userSelected": id_type_user_selected,
                        }.items()
                        if v is not None
                    }
                ]
            if id_type_text:
                type_cc["text"] = id_type_text
            identifier["type"] = type_cc
        if id_system:
            identifier["system"] = id_system
        if id_value:
            identifier["value"] = id_value
        if id_period_start or id_period_end:
            identifier["period"] = {
                k: v
                for k, v in {
                    "start": fhir_instant(id_period_start),
                    "end": fhir_instant(id_period_end),
                }.items()
                if v
            }
        entry["identifier"] = identifier
    return entry


def fhir_location_identifier(i: LocationIdentifier) -> dict:
    """Location.identifier (Identifier) → FHIR camelCase dict. Resource-specific
    (not the shared app.fhir.datatypes.fhir_identifier) because assigner is a
    resolved Reference(Organization) with an identifier fallback, and
    `type.coding[]` is a real 0..* child table (type_codings) rather than a
    single flattened coding — mirrors OrganizationIdentifier's own
    type.coding[] promotion."""
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    type_codings = _fhir_coding_list(i.type_codings)
    if type_codings or i.type_text:
        type_cc: dict = {}
        if type_codings:
            type_cc["coding"] = type_codings
        if i.type_text:
            type_cc["text"] = i.type_text
        entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    if i.period_start or i.period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": fhir_instant(i.period_start),
                "end": fhir_instant(i.period_end),
            }.items()
            if v
        }
    assigner = _fhir_reference(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry


def fhir_location_type(t) -> dict:
    """Location.type (CodeableConcept) → FHIR camelCase dict. `coding[]` is
    a real 0..* child table (codings) rather than a single flattened coding
    — mirrors OrganizationType's own coding[] promotion."""
    coding = _fhir_coding_list(t.codings)
    entry: dict = {}
    if coding:
        entry["coding"] = coding
    if t.text:
        entry["text"] = t.text
    return entry


def fhir_location_alias(a) -> str:
    """Location.alias (string) — the child row collapses to a bare string in
    FHIR output, same as Organization.alias."""
    return a.value


def fhir_location_telecom(t) -> dict:
    """Location.telecom (ContactPoint) → FHIR camelCase dict."""
    return fhir_telecom(t)


def fhir_location_hours_of_operation(h: LocationHoursOfOperation) -> dict:
    """Location.hoursOfOperation (BackboneElement) → FHIR camelCase dict.
    `days_of_week` is stored comma-separated (see the model's docstring) and is
    split back into a real `daysOfWeek[]` array here."""
    entry: dict = {}
    days = fhir_split(h.days_of_week)
    if days:
        entry["daysOfWeek"] = days
    if h.all_day is not None:
        entry["allDay"] = h.all_day
    if h.opening_time:
        entry["openingTime"] = h.opening_time.isoformat()
    if h.closing_time:
        entry["closingTime"] = h.closing_time.isoformat()
    return entry


def fhir_location_endpoint(e: LocationEndpoint) -> dict:
    """Location.endpoint (Reference(Endpoint)) → FHIR camelCase dict. Uses the
    shared resolved-reference-plus-fallback renderer since Endpoint isn't a
    modeled resource — the identifier fallback is often the only populated
    half."""
    return _fhir_reference(e, "reference")


def fhir_location_address(loc: LocationModel) -> dict:
    """Location.address (0..1 Address) → FHIR camelCase dict.

    Singular, unlike Organization.address — Location.address is 0..1 in R4, so
    the columns live flat on the parent row under an `address_` prefix rather
    than in a child table.
    """
    entry: dict = {}
    if loc.address_use:
        entry["use"] = fhir_enum(loc.address_use)
    if loc.address_type:
        entry["type"] = fhir_enum(loc.address_type)
    if loc.address_text:
        entry["text"] = loc.address_text
    lines = fhir_split(loc.address_line)
    if lines:
        entry["line"] = lines
    if loc.address_city:
        entry["city"] = loc.address_city
    if loc.address_district:
        entry["district"] = loc.address_district
    if loc.address_state:
        entry["state"] = loc.address_state
    if loc.address_postal_code:
        entry["postalCode"] = loc.address_postal_code
    if loc.address_country:
        entry["country"] = loc.address_country
    if loc.address_period_start or loc.address_period_end:
        entry["period"] = {
            k: v
            for k, v in {
                "start": fhir_instant(loc.address_period_start),
                "end": fhir_instant(loc.address_period_end),
            }.items()
            if v
        }
    return entry


def fhir_location_position(loc: LocationModel) -> dict:
    """Location.position (0..1 BackboneElement) → FHIR camelCase dict.

    longitude and latitude are both 1..1 *within* position, so an incomplete
    pair emits nothing rather than a half-built element — the schema layer
    rejects that combination on write, and this keeps any row predating the
    rule from producing invalid FHIR.
    """
    if loc.position_longitude is None or loc.position_latitude is None:
        return {}
    entry: dict = {
        "longitude": loc.position_longitude,
        "latitude": loc.position_latitude,
    }
    if loc.position_altitude is not None:
        entry["altitude"] = loc.position_altitude
    return entry


def fhir_location_operational_status(loc: LocationModel) -> dict:
    """Location.operationalStatus (0..1 Coding) → FHIR camelCase dict.

    A Coding, not a CodeableConcept — so there is no `text` sibling and no
    `coding[]` wrapper, unlike physicalType below.
    """
    return {
        k: v
        for k, v in {
            "system": loc.operational_status_system,
            "version": loc.operational_status_version,
            "code": loc.operational_status_code,
            "display": loc.operational_status_display,
            "userSelected": loc.operational_status_user_selected,
        }.items()
        if v is not None
    }


def fhir_location_physical_type(loc: LocationModel) -> dict:
    """Location.physicalType (0..1 CodeableConcept) → FHIR camelCase dict.
    `coding[]` is a real 0..* child table (physical_type_codings) rather
    than a single flattened coding — physicalType itself is 0..1 at the
    Location level, but its own coding[] is still 0..* per spec, same
    reasoning as Location.type/identifier.type."""
    coding = _fhir_coding_list(loc.physical_type_codings)
    entry: dict = {}
    if coding:
        entry["coding"] = coding
    if loc.physical_type_text:
        entry["text"] = loc.physical_type_text
    return entry


# Base URL for this server's own, not-yet-formally-registered extensions —
# same convention as app.fhir.mappers.organization.fhir._EXT_BASE.
_EXT_BASE = "https://fhir-server.dev/fhir/StructureDefinition"


def _fhir_meta(loc: LocationModel) -> dict:
    """Audit columns (tenant_id/created_by/updated_by/created_at/updated_at)
    rendered into Resource.meta — same convention as
    app.fhir.mappers.organization.fhir._fhir_meta. `lastUpdated` is Meta's
    own native field; the other four have no native Meta field in R4, so
    they ride as extensions. Location has no user_id (see the model's
    docstring), so there's no equivalent of a user-scoped extension here."""
    meta: dict = {}
    if loc.updated_at:
        meta["lastUpdated"] = fhir_instant(loc.updated_at)

    extensions = []
    if loc.tenant_id:
        extensions.append(
            {"url": f"{_EXT_BASE}/org-id", "valueString": loc.tenant_id}
        )
    if loc.created_by:
        extensions.append(
            {"url": f"{_EXT_BASE}/created-by", "valueString": loc.created_by}
        )
    if loc.updated_by:
        extensions.append(
            {"url": f"{_EXT_BASE}/updated-by", "valueString": loc.updated_by}
        )
    if loc.created_at:
        extensions.append(
            {
                "url": f"{_EXT_BASE}/created-at",
                "valueDateTime": fhir_instant(loc.created_at),
            }
        )
    if extensions:
        meta["extension"] = extensions

    return meta


def to_fhir_location(loc: LocationModel) -> dict:
    result: dict = {
        "resourceType": "Location",
        "id": str(loc.location_id),
    }

    meta = _fhir_meta(loc)
    if meta:
        result["meta"] = meta

    identifiers = [fhir_location_identifier(i) for i in (loc.identifiers or [])]
    if identifiers:
        result["identifier"] = identifiers

    if loc.status:
        result["status"] = fhir_enum(loc.status)

    operational_status = fhir_location_operational_status(loc)
    if operational_status:
        result["operationalStatus"] = operational_status

    if loc.name:
        result["name"] = loc.name

    aliases = [fhir_location_alias(a) for a in (loc.aliases or []) if a.value]
    if aliases:
        result["alias"] = aliases

    if loc.description:
        result["description"] = loc.description
    if loc.mode:
        result["mode"] = fhir_enum(loc.mode)

    types = [fhir_location_type(t) for t in (loc.types or [])]
    types = [t for t in types if t]
    if types:
        result["type"] = types

    telecoms = [fhir_location_telecom(t) for t in (loc.telecoms or [])]
    if telecoms:
        result["telecom"] = telecoms

    address = fhir_location_address(loc)
    if address:
        result["address"] = address

    physical_type = fhir_location_physical_type(loc)
    if physical_type:
        result["physicalType"] = physical_type

    position = fhir_location_position(loc)
    if position:
        result["position"] = position

    managing_organization = _fhir_reference(loc, "managing_organization")
    if managing_organization:
        result["managingOrganization"] = managing_organization

    part_of = _fhir_reference(loc, "part_of")
    if part_of:
        result["partOf"] = part_of

    hours = [
        fhir_location_hours_of_operation(h) for h in (loc.hours_of_operation or [])
    ]
    hours = [h for h in hours if h]
    if hours:
        result["hoursOfOperation"] = hours

    if loc.availability_exceptions:
        result["availabilityExceptions"] = loc.availability_exceptions

    endpoints = [fhir_location_endpoint(e) for e in (loc.endpoints or [])]
    endpoints = [e for e in endpoints if e]
    if endpoints:
        result["endpoint"] = endpoints

    return {k: v for k, v in result.items() if v is not None}
