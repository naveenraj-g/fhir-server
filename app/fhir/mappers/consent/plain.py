from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.consent import (
        ConsentIdentifier,
        ConsentModel,
        ConsentPolicy,
        ConsentProvision,
        ConsentProvisionActor,
        ConsentProvisionData,
        ConsentVerification,
    )


def _plain_ref(ref_raw: str | None, ref_type: Any, ref_id: int | None) -> str | None:
    if ref_raw:
        return ref_raw
    if ref_type and ref_id:
        return f"{fhir_enum(ref_type)}/{ref_id}"
    return None


def _plain_reference_fields(obj, prefix: str) -> dict:
    if obj is None:
        return {}
    p_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    p_end = getattr(obj, f"{prefix}_identifier_period_end", None)
    return {
        f"{prefix}_identifier_use": fhir_enum(
            getattr(obj, f"{prefix}_identifier_use", None)
        ),
        f"{prefix}_identifier_type_system": getattr(
            obj, f"{prefix}_identifier_type_system", None
        ),
        f"{prefix}_identifier_type_version": getattr(
            obj, f"{prefix}_identifier_type_version", None
        ),
        f"{prefix}_identifier_type_code": getattr(
            obj, f"{prefix}_identifier_type_code", None
        ),
        f"{prefix}_identifier_type_display": getattr(
            obj, f"{prefix}_identifier_type_display", None
        ),
        f"{prefix}_identifier_type_user_selected": getattr(
            obj, f"{prefix}_identifier_type_user_selected", None
        ),
        f"{prefix}_identifier_type_text": getattr(
            obj, f"{prefix}_identifier_type_text", None
        ),
        f"{prefix}_identifier_system": getattr(
            obj, f"{prefix}_identifier_system", None
        ),
        f"{prefix}_identifier_value": getattr(
            obj, f"{prefix}_identifier_value", None
        ),
        f"{prefix}_identifier_period_start": fhir_instant(p_start)
        if p_start
        else None,
        f"{prefix}_identifier_period_end": fhir_instant(p_end)
        if p_end
        else None,
    }


def _plain_coding_list(codings) -> list[dict]:
    return [
        {
            "id": getattr(c, "id", None),
            "system": c.system,
            "version": c.version,
            "code": c.code,
            "display": c.display,
            "user_selected": c.user_selected,
        }
        for c in codings or []
    ]


def _plain_codeable_concept(codings, text: str | None) -> dict | None:
    c_list = _plain_coding_list(codings)
    if not c_list and not text:
        return None
    res: dict = {}
    if text:
        res["text"] = text
    if c_list:
        res["coding"] = c_list
    return res


def _plain_identifier(i: ConsentIdentifier) -> dict:
    res = {
        "id": i.id,
        "use": fhir_enum(i.use) if i.use else None,
        "type": _plain_codeable_concept(getattr(i, "type_codings", None), i.type_text),
        "system": i.system,
        "value": i.value,
        "period_start": i.period_start,
        "period_end": i.period_end,
        "assigner": _plain_ref(i.assigner_reference, i.assigner_type, i.assigner_id),
        "assigner_display": i.assigner_display,
    }
    res.update(_plain_reference_fields(i, "assigner"))
    return res


def _plain_policy(p: ConsentPolicy) -> dict:
    return {
        "id": p.id,
        "authority": p.authority,
        "uri": p.uri,
    }


def _plain_verification(v: ConsentVerification) -> dict:
    res = {
        "id": v.id,
        "verified": v.verified,
        "verified_with": _plain_ref(
            v.verified_with_reference,
            v.verified_with_type,
            v.verified_with_id,
        ),
        "verified_with_display": v.verified_with_display,
        "verification_date": v.verification_date,
    }
    res.update(_plain_reference_fields(v, "verified_with"))
    return res


def _plain_provision_actor(a: ConsentProvisionActor) -> dict:
    res = {
        "id": a.id,
        "role": _plain_codeable_concept(getattr(a, "role_codings", None), a.role_text),
        "reference": _plain_ref(
            a.reference_reference,
            a.reference_type,
            a.reference_id,
        ),
        "reference_display": a.reference_display,
    }
    res.update(_plain_reference_fields(a, "reference"))
    return res


def _plain_provision_data(d: ConsentProvisionData) -> dict:
    res = {
        "id": d.id,
        "meaning": fhir_enum(d.meaning),
        "reference": _plain_ref(
            d.reference_reference,
            d.reference_type,
            d.reference_id,
        ),
        "reference_display": d.reference_display,
    }
    res.update(_plain_reference_fields(d, "reference"))
    return res


def _plain_provision(p: ConsentProvision) -> dict:
    res: dict[str, Any] = {
        "id": p.id,
        "type": fhir_enum(p.type) if p.type else None,
        "period_start": p.period_start,
        "period_end": p.period_end,
        "data_period_start": p.data_period_start,
        "data_period_end": p.data_period_end,
    }

    if getattr(p, "actors", None):
        res["actor"] = [_plain_provision_actor(a) for a in p.actors]

    if getattr(p, "actions", None):
        res["action"] = [
            _plain_codeable_concept(getattr(act, "codings", None), act.text)
            for act in p.actions
        ]

    if getattr(p, "security_labels", None):
        res["security_label"] = _plain_coding_list(p.security_labels)

    if getattr(p, "purposes", None):
        res["purpose"] = _plain_coding_list(p.purposes)

    if getattr(p, "classes", None):
        res["class"] = _plain_coding_list(p.classes)

    if getattr(p, "codes", None):
        res["code"] = [
            _plain_codeable_concept(getattr(c, "codings", None), c.text)
            for c in p.codes
        ]

    if getattr(p, "data_entries", None):
        res["data"] = [_plain_provision_data(d) for d in p.data_entries]

    if getattr(p, "sub_provisions", None):
        res["provision"] = [_plain_provision(sub) for sub in p.sub_provisions]

    return res


def to_plain_consent(model: ConsentModel) -> dict:
    """Map ConsentModel to plain snake_case dict."""
    def _plain_child_ref(row):
        item = {
            "id": row.id,
            "reference": _plain_ref(
                row.reference_reference,
                row.reference_type,
                row.reference_id,
            ),
            "display": row.reference_display,
        }
        for k, v in _plain_reference_fields(row, "reference").items():
            item[k.removeprefix("reference_")] = v
        return item

    res: dict[str, Any] = {
        "id": model.consent_id,
        "status": fhir_enum(model.status),
        "scope": _plain_codeable_concept(
            getattr(model, "scope_codings", None),
            model.scope_text,
        ),
        "category": [
            _plain_codeable_concept(getattr(cat, "codings", None), cat.text)
            for cat in (model.categories or [])
        ],
        "patient": _plain_ref(
            model.patient_reference,
            model.patient_type,
            model.patient_id,
        ),
        "patient_display": model.patient_display,
        "date_time": model.date_time,
        "performer": [
            _plain_child_ref(p) for p in (model.performers or [])
        ]
        if getattr(model, "performers", None)
        else None,
        "organization": [
            _plain_child_ref(o) for o in (model.organizations or [])
        ]
        if getattr(model, "organizations", None)
        else None,
        "source_attachment": model.source_attachment,
        "source_reference": _plain_ref(
            model.source_reference_reference,
            model.source_reference_type,
            model.source_reference_id,
        ),
        "source_reference_display": model.source_reference_display,
        "policy": [
            _plain_policy(p) for p in (model.policies or [])
        ]
        if getattr(model, "policies", None)
        else None,
        "policy_rule": _plain_codeable_concept(
            getattr(model, "policy_rule_codings", None),
            model.policy_rule_text,
        ),
        "verification": [
            _plain_verification(v) for v in (model.verifications or [])
        ]
        if getattr(model, "verifications", None)
        else None,
        "identifier": [
            _plain_identifier(i) for i in (model.identifiers or [])
        ]
        if getattr(model, "identifiers", None)
        else None,
        "extension": model.extension if model.extension else None,
    }

    res.update(_plain_reference_fields(model, "patient"))
    res.update(_plain_reference_fields(model, "source_reference"))

    if getattr(model, "provisions", None):
        top_provision = next(
            (p for p in model.provisions if p.parent_provision_id is None),
            None,
        )
        if top_provision:
            res["provision"] = _plain_provision(top_provision)
    else:
        res["provision"] = None

    return res
