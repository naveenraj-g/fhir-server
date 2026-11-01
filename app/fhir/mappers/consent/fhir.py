from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.consent import (
        ConsentIdentifier,
        ConsentModel,
        ConsentPolicy,
        ConsentProvision,
        ConsentProvisionAction,
        ConsentProvisionActor,
        ConsentProvisionData,
        ConsentVerification,
    )


def _fhir_coding_list(codings) -> list[dict]:
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


def _fhir_codeable_concept(codings, text: str | None) -> dict | None:
    coding_list = _fhir_coding_list(codings)
    result: dict = {}
    if coding_list:
        result["coding"] = coding_list
    if text:
        result["text"] = text
    return result or None


def _fhir_reference(obj, prefix: str) -> dict | None:
    if obj is None:
        return None
    ref = getattr(obj, f"{prefix}_reference", None)
    rtype = getattr(obj, f"{prefix}_type", None)
    rid = getattr(obj, f"{prefix}_id", None)
    disp = getattr(obj, f"{prefix}_display", None)

    out: dict[str, Any] = {}
    if ref:
        out["reference"] = ref
    elif rtype and rid:
        type_str = fhir_enum(rtype)
        out["reference"] = f"{type_str}/{rid}"
    if disp:
        out["display"] = disp

    use = getattr(obj, f"{prefix}_identifier_use", None)
    val = getattr(obj, f"{prefix}_identifier_value", None)
    sys = getattr(obj, f"{prefix}_identifier_system", None)
    type_code = getattr(obj, f"{prefix}_identifier_type_code", None)
    p_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    p_end = getattr(obj, f"{prefix}_identifier_period_end", None)

    if (
        use
        or val
        or sys
        or type_code
        or p_start
        or p_end
        or getattr(obj, f"{prefix}_identifier_type_text", None)
    ):
        ident: dict[str, Any] = {}
        if use:
            ident["use"] = fhir_enum(use)
        if sys:
            ident["system"] = sys
        if val:
            ident["value"] = val
        if type_code or getattr(obj, f"{prefix}_identifier_type_text", None):
            coding: dict[str, Any] = {}
            if getattr(obj, f"{prefix}_identifier_type_system", None):
                coding["system"] = getattr(obj, f"{prefix}_identifier_type_system")
            if getattr(obj, f"{prefix}_identifier_type_version", None):
                coding["version"] = getattr(obj, f"{prefix}_identifier_type_version")
            if type_code:
                coding["code"] = type_code
            if getattr(obj, f"{prefix}_identifier_type_display", None):
                coding["display"] = getattr(obj, f"{prefix}_identifier_type_display")
            if getattr(obj, f"{prefix}_identifier_type_user_selected", None) is not None:
                coding["userSelected"] = getattr(obj, f"{prefix}_identifier_type_user_selected")

            type_dict: dict[str, Any] = {}
            if coding:
                type_dict["coding"] = [coding]
            if getattr(obj, f"{prefix}_identifier_type_text", None):
                type_dict["text"] = getattr(obj, f"{prefix}_identifier_type_text")
            if type_dict:
                ident["type"] = type_dict
        if p_start or p_end:
            period: dict[str, Any] = {}
            if p_start:
                period["start"] = fhir_instant(p_start)
            if p_end:
                period["end"] = fhir_instant(p_end)
            ident["period"] = period
        out["identifier"] = ident

    return out or None


def _fhir_identifier(i: ConsentIdentifier) -> dict | None:
    entry: dict = {}
    if i.use:
        entry["use"] = fhir_enum(i.use)
    type_cc = _fhir_codeable_concept(getattr(i, "type_codings", None), i.type_text)
    if type_cc:
        entry["type"] = type_cc
    if i.system:
        entry["system"] = i.system
    if i.value:
        entry["value"] = i.value
    if i.period_start or i.period_end:
        period: dict = {}
        if i.period_start:
            period["start"] = fhir_instant(i.period_start)
        if i.period_end:
            period["end"] = fhir_instant(i.period_end)
        entry["period"] = period
    assigner = _fhir_reference(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def _fhir_policy(p: ConsentPolicy) -> dict | None:
    res: dict = {}
    if p.authority:
        res["authority"] = p.authority
    if p.uri:
        res["uri"] = p.uri
    return res or None


def _fhir_verification(v: ConsentVerification) -> dict:
    res: dict = {"verified": v.verified}
    verified_with = _fhir_reference(v, "verified_with")
    if verified_with:
        res["verifiedWith"] = verified_with
    if v.verification_date:
        res["verificationDate"] = fhir_instant(v.verification_date)
    return res


def _fhir_provision_actor(a: ConsentProvisionActor) -> dict | None:
    role = _fhir_codeable_concept(getattr(a, "role_codings", None), a.role_text)
    ref = _fhir_reference(a, "reference")
    if not role or not ref:
        return None
    return {"role": role, "reference": ref}


def _fhir_provision_data(d: ConsentProvisionData) -> dict | None:
    ref = _fhir_reference(d, "reference")
    if not ref:
        return None
    return {
        "meaning": fhir_enum(d.meaning),
        "reference": ref,
    }


def _fhir_provision(p: ConsentProvision) -> dict | None:
    res: dict[str, Any] = {}
    if p.type:
        res["type"] = fhir_enum(p.type)
    if p.period_start or p.period_end:
        period: dict = {}
        if p.period_start:
            period["start"] = fhir_instant(p.period_start)
        if p.period_end:
            period["end"] = fhir_instant(p.period_end)
        res["period"] = period

    if getattr(p, "actors", None):
        actors = [_fhir_provision_actor(a) for a in p.actors]
        actors = [a for a in actors if a]
        if actors:
            res["actor"] = actors

    if getattr(p, "actions", None):
        actions = [
            _fhir_codeable_concept(getattr(act, "codings", None), act.text)
            for act in p.actions
        ]
        actions = [act for act in actions if act]
        if actions:
            res["action"] = actions

    if getattr(p, "security_labels", None):
        sec = _fhir_coding_list(p.security_labels)
        if sec:
            res["securityLabel"] = sec

    if getattr(p, "purposes", None):
        purp = _fhir_coding_list(p.purposes)
        if purp:
            res["purpose"] = purp

    if getattr(p, "classes", None):
        cls_list = _fhir_coding_list(p.classes)
        if cls_list:
            res["class"] = cls_list

    if getattr(p, "codes", None):
        cds = [
            _fhir_codeable_concept(getattr(c, "codings", None), c.text)
            for c in p.codes
        ]
        cds = [c for c in cds if c]
        if cds:
            res["code"] = cds

    if p.data_period_start or p.data_period_end:
        data_period: dict = {}
        if p.data_period_start:
            data_period["start"] = fhir_instant(p.data_period_start)
        if p.data_period_end:
            data_period["end"] = fhir_instant(p.data_period_end)
        res["dataPeriod"] = data_period

    if getattr(p, "data_entries", None):
        data = [_fhir_provision_data(d) for d in p.data_entries]
        data = [d for d in data if d]
        if data:
            res["data"] = data

    if getattr(p, "sub_provisions", None):
        subs = [_fhir_provision(sub) for sub in p.sub_provisions]
        subs = [s for s in subs if s]
        if subs:
            res["provision"] = subs

    return res or None


def to_fhir_consent(model: ConsentModel) -> dict:
    """Map ConsentModel to FHIR R4 Consent dict."""
    res: dict[str, Any] = {
        "resourceType": "Consent",
        "id": str(model.consent_id),
        "status": fhir_enum(model.status),
    }

    if model.updated_at:
        res["meta"] = {
            "versionId": "1",
            "lastUpdated": fhir_instant(model.updated_at),
        }

    scope = _fhir_codeable_concept(
        getattr(model, "scope_codings", None),
        model.scope_text,
    )
    if scope:
        res["scope"] = scope

    if getattr(model, "categories", None):
        cats = [
            _fhir_codeable_concept(getattr(cat, "codings", None), cat.text)
            for cat in model.categories
        ]
        cats = [c for c in cats if c]
        if cats:
            res["category"] = cats

    patient = _fhir_reference(model, "patient")
    if patient:
        res["patient"] = patient

    if model.date_time:
        res["dateTime"] = fhir_instant(model.date_time)

    if getattr(model, "performers", None):
        perfs = [
            _fhir_reference(p, "reference")
            for p in model.performers
        ]
        perfs = [p for p in perfs if p]
        if perfs:
            res["performer"] = perfs

    if getattr(model, "organizations", None):
        orgs = [
            _fhir_reference(o, "reference")
            for o in model.organizations
        ]
        orgs = [o for o in orgs if o]
        if orgs:
            res["organization"] = orgs

    # Choice source[x]
    if model.source_attachment is not None:
        res["sourceAttachment"] = model.source_attachment
    else:
        source_ref = _fhir_reference(model, "source_reference")
        if source_ref:
            res["sourceReference"] = source_ref

    if getattr(model, "policies", None):
        policies = [_fhir_policy(p) for p in model.policies]
        policies = [p for p in policies if p]
        if policies:
            res["policy"] = policies

    policy_rule = _fhir_codeable_concept(
        getattr(model, "policy_rule_codings", None),
        model.policy_rule_text,
    )
    if policy_rule:
        res["policyRule"] = policy_rule

    if getattr(model, "verifications", None):
        vers = [_fhir_verification(v) for v in model.verifications]
        vers = [v for v in vers if v]
        if vers:
            res["verification"] = vers

    if getattr(model, "provisions", None):
        # Top-level provision has parent_provision_id is None
        top_provision = next(
            (p for p in model.provisions if p.parent_provision_id is None),
            None,
        )
        if top_provision:
            prov = _fhir_provision(top_provision)
            if prov:
                res["provision"] = prov

    if getattr(model, "identifiers", None):
        idents = [_fhir_identifier(i) for i in model.identifiers]
        idents = [i for i in idents if i]
        if idents:
            res["identifier"] = idents

    if model.extension:
        res["extension"] = model.extension

    return {k: v for k, v in res.items() if v is not None}
