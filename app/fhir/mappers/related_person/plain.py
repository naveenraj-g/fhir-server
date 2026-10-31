from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.related_person import (
        RelatedPersonAddress,
        RelatedPersonCommunication,
        RelatedPersonIdentifier,
        RelatedPersonModel,
        RelatedPersonName,
        RelatedPersonPhoto,
        RelatedPersonRelationship,
        RelatedPersonTelecom,
    )


def _plain_coding(c) -> dict:
    return {
        "id": c.id,
        "system": c.system,
        "version": c.version,
        "code": c.code,
        "display": c.display,
        "user_selected": c.user_selected,
        "tenant_id": c.tenant_id,
        "created_by": c.created_by,
        "updated_by": c.updated_by,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
    }


def _plain_identifier(i: RelatedPersonIdentifier) -> dict:
    return {
        "id": i.id,
        "use": fhir_enum(i.use),
        "type_text": i.type_text,
        "type_codings": [_plain_coding(c) for c in (i.type_codings or [])],
        "system": i.system,
        "value": i.value,
        "period_start": fhir_instant(i.period_start),
        "period_end": fhir_instant(i.period_end),
        "assigner_reference": i.assigner_reference,
        "assigner": (
            f"Organization/{i.assigner_id}"
            if (i.assigner_id and fhir_enum(i.assigner_type) == "Organization")
            else i.assigner_reference
        ),
        "assigner_type": fhir_enum(i.assigner_type),
        "assigner_id": i.assigner_id,
        "assigner_display": i.assigner_display,
        "assigner_identifier_use": fhir_enum(i.assigner_identifier_use),
        "assigner_identifier_type_system": i.assigner_identifier_type_system,
        "assigner_identifier_type_version": i.assigner_identifier_type_version,
        "assigner_identifier_type_code": i.assigner_identifier_type_code,
        "assigner_identifier_type_display": i.assigner_identifier_type_display,
        "assigner_identifier_type_text": i.assigner_identifier_type_text,
        "assigner_identifier_type_user_selected": i.assigner_identifier_type_user_selected,
        "assigner_identifier_system": i.assigner_identifier_system,
        "assigner_identifier_value": i.assigner_identifier_value,
        "assigner_identifier_period_start": fhir_instant(
            i.assigner_identifier_period_start
        ),
        "assigner_identifier_period_end": fhir_instant(
            i.assigner_identifier_period_end
        ),
        "tenant_id": i.tenant_id,
        "created_by": i.created_by,
        "updated_by": i.updated_by,
        "created_at": i.created_at,
        "updated_at": i.updated_at,
    }


def _plain_relationship(r: RelatedPersonRelationship) -> dict:
    return {
        "id": r.id,
        "text": r.text,
        "codings": [_plain_coding(c) for c in (r.codings or [])],
        "tenant_id": r.tenant_id,
        "created_by": r.created_by,
        "updated_by": r.updated_by,
        "created_at": r.created_at,
        "updated_at": r.updated_at,
    }


def _plain_name(n: RelatedPersonName) -> dict:
    return {
        "id": n.id,
        "use": fhir_enum(n.use),
        "text": n.text,
        "family": n.family,
        "given": list(n.given) if n.given else None,
        "prefix": list(n.prefix) if n.prefix else None,
        "suffix": list(n.suffix) if n.suffix else None,
        "period_start": fhir_instant(n.period_start),
        "period_end": fhir_instant(n.period_end),
        "tenant_id": n.tenant_id,
        "created_by": n.created_by,
        "updated_by": n.updated_by,
        "created_at": n.created_at,
        "updated_at": n.updated_at,
    }


def _plain_telecom(t: RelatedPersonTelecom) -> dict:
    return {
        "id": t.id,
        "system": fhir_enum(t.system),
        "value": t.value,
        "use": fhir_enum(t.use),
        "rank": t.rank,
        "period_start": fhir_instant(t.period_start),
        "period_end": fhir_instant(t.period_end),
        "tenant_id": t.tenant_id,
        "created_by": t.created_by,
        "updated_by": t.updated_by,
        "created_at": t.created_at,
        "updated_at": t.updated_at,
    }


def _plain_address(a: RelatedPersonAddress) -> dict:
    return {
        "id": a.id,
        "use": fhir_enum(a.use),
        "type": fhir_enum(a.type),
        "text": a.text,
        "line": list(a.line) if a.line else None,
        "city": a.city,
        "district": a.district,
        "state": a.state,
        "postal_code": a.postal_code,
        "country": a.country,
        "period_start": fhir_instant(a.period_start),
        "period_end": fhir_instant(a.period_end),
        "tenant_id": a.tenant_id,
        "created_by": a.created_by,
        "updated_by": a.updated_by,
        "created_at": a.created_at,
        "updated_at": a.updated_at,
    }


def _plain_photo(p: RelatedPersonPhoto) -> dict:
    return {
        "id": p.id,
        "content_type": p.content_type,
        "language": p.language,
        "data": p.data,
        "url": p.url,
        "size": p.size,
        "hash": p.hash,
        "title": p.title,
        "creation": fhir_instant(p.creation),
        "tenant_id": p.tenant_id,
        "created_by": p.created_by,
        "updated_by": p.updated_by,
        "created_at": p.created_at,
        "updated_at": p.updated_at,
    }


def _plain_communication(c: RelatedPersonCommunication) -> dict:
    return {
        "id": c.id,
        "language_text": c.language_text,
        "language_codings": [_plain_coding(cd) for cd in (c.language_codings or [])],
        "preferred": c.preferred,
        "tenant_id": c.tenant_id,
        "created_by": c.created_by,
        "updated_by": c.updated_by,
        "created_at": c.created_at,
        "updated_at": c.updated_at,
    }


def to_plain_related_person(model: RelatedPersonModel) -> dict:
    """Serialize a RelatedPersonModel to plain snake_case dict."""
    return {
        "id": model.related_person_id,
        "active": model.active,
        "patient_reference": model.patient_reference,
        "patient_type": fhir_enum(model.patient_type),
        "patient_id": model.patient_id,
        "patient_display": model.patient_display,
        "gender": fhir_enum(model.gender),
        "birth_date": model.birth_date.isoformat() if model.birth_date else None,
        "period_start": fhir_instant(model.period_start),
        "period_end": fhir_instant(model.period_end),
        "extension": list(model.extension) if model.extension else [],
        "tenant_id": model.tenant_id,
        "created_by": model.created_by,
        "updated_by": model.updated_by,
        "created_at": model.created_at,
        "updated_at": model.updated_at,
        "identifiers": [_plain_identifier(i) for i in (model.identifiers or [])],
        "relationships": [
            _plain_relationship(r) for r in (model.relationships or [])
        ],
        "names": [_plain_name(n) for n in (model.names or [])],
        "telecoms": [_plain_telecom(t) for t in (model.telecoms or [])],
        "addresses": [_plain_address(a) for a in (model.addresses or [])],
        "photos": [_plain_photo(p) for p in (model.photos or [])],
        "communications": [
            _plain_communication(c) for c in (model.communications or [])
        ],
    }
