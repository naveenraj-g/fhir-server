"""Payload -> FHIR JSON conversion for Consent.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(ConsentCreateSchema / ConsentPatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum, fhir_instant, merge_patch_fragment

if TYPE_CHECKING:
    from app.schemas.consent.input import (
        ConsentCodeableConceptInput,
        ConsentCreateSchema,
        ConsentIdentifierInput,
        ConsentPatchSchema,
        ConsentPolicyInput,
        ConsentProvisionActorInput,
        ConsentProvisionDataInput,
        ConsentProvisionInput,
        ConsentReferenceInput,
        ConsentVerificationInput,
    )

_PATIENT_FIELDS = {"patient", "patient_display"}
_SOURCE_REF_FIELDS = {"source_reference", "source_reference_display"}


def _coding_from_payload(c: Any) -> dict:
    if isinstance(c, dict):
        return {
            k: v
            for k, v in {
                "system": c.get("system"),
                "version": c.get("version"),
                "code": c.get("code"),
                "display": c.get("display"),
                "userSelected": c.get("user_selected") or c.get("userSelected"),
            }.items()
            if v is not None
        }
    return {
        k: v
        for k, v in {
            "system": getattr(c, "system", None),
            "version": getattr(c, "version", None),
            "code": getattr(c, "code", None),
            "display": getattr(c, "display", None),
            "userSelected": getattr(c, "user_selected", None),
        }.items()
        if v is not None
    }


def _codeable_concept_from_payload(
    concept: ConsentCodeableConceptInput | dict | None,
) -> dict | None:
    if not concept:
        return None
    if isinstance(concept, dict):
        codings = [_coding_from_payload(c) for c in (concept.get("coding") or [])]
        codings = [c for c in codings if c]
        text = concept.get("text")
    else:
        codings = [_coding_from_payload(c) for c in (concept.coding or [])]
        codings = [c for c in codings if c]
        text = concept.text

    result: dict = {}
    if codings:
        result["coding"] = codings
    if text:
        result["text"] = text
    return result or None


def _identifier_from_payload(
    ident: ConsentIdentifierInput | dict | None,
) -> dict | None:
    if not ident:
        return None
    entry: dict = {}
    if isinstance(ident, dict):
        use = ident.get("use")
        type_in = ident.get("type")
        system = ident.get("system")
        value = ident.get("value")
        p_start = ident.get("period_start")
        p_end = ident.get("period_end")
        assigner = ident.get("assigner")
        assigner_disp = ident.get("assigner_display")
    else:
        use = ident.use
        type_in = ident.type
        system = ident.system
        value = ident.value
        p_start = ident.period_start
        p_end = ident.period_end
        assigner = ident.assigner
        assigner_disp = ident.assigner_display

    if use:
        entry["use"] = fhir_enum(use)
    type_cc = _codeable_concept_from_payload(type_in)
    if type_cc:
        entry["type"] = type_cc
    if system:
        entry["system"] = system
    if value:
        entry["value"] = value
    if p_start or p_end:
        period: dict = {}
        if p_start:
            period["start"] = fhir_instant(p_start)
        if p_end:
            period["end"] = fhir_instant(p_end)
        entry["period"] = period
    if assigner or assigner_disp:
        asg: dict = {}
        if assigner:
            asg["reference"] = assigner
        if assigner_disp:
            asg["display"] = assigner_disp
        if asg:
            entry["assigner"] = asg
    return entry or None


def _policy_from_payload(
    policy: ConsentPolicyInput | dict | None,
) -> dict | None:
    if not policy:
        return None
    entry: dict = {}
    if isinstance(policy, dict):
        authority = policy.get("authority")
        uri = policy.get("uri")
    else:
        authority = policy.authority
        uri = policy.uri
    if authority:
        entry["authority"] = authority
    if uri:
        entry["uri"] = uri
    return entry or None


def _verification_from_payload(
    v: ConsentVerificationInput | dict | None,
) -> dict | None:
    if not v:
        return None
    entry: dict = {}
    if isinstance(v, dict):
        verified = v.get("verified")
        verified_with = v.get("verified_with")
        verified_with_disp = v.get("verified_with_display")
        v_date = v.get("verification_date")
    else:
        verified = v.verified
        verified_with = v.verified_with
        verified_with_disp = v.verified_with_display
        v_date = v.verification_date

    entry["verified"] = bool(verified)
    if verified_with or verified_with_disp:
        ref: dict = {}
        if verified_with:
            ref["reference"] = verified_with
        if verified_with_disp:
            ref["display"] = verified_with_disp
        if ref:
            entry["verifiedWith"] = ref
    if v_date:
        entry["verificationDate"] = fhir_instant(v_date)
    return entry


def _provision_actor_from_payload(
    a: ConsentProvisionActorInput | dict | None,
) -> dict | None:
    if not a:
        return None
    if isinstance(a, dict):
        role_in = a.get("role")
        ref_in = a.get("reference")
        disp_in = a.get("reference_display")
    else:
        role_in = a.role
        ref_in = a.reference
        disp_in = a.reference_display

    role = _codeable_concept_from_payload(role_in)
    ref: dict = {}
    if ref_in:
        ref["reference"] = ref_in
    if disp_in:
        ref["display"] = disp_in
    if not role or not ref:
        return None
    return {"role": role, "reference": ref}


def _provision_data_from_payload(
    d: ConsentProvisionDataInput | dict | None,
) -> dict | None:
    if not d:
        return None
    if isinstance(d, dict):
        meaning = d.get("meaning")
        ref_in = d.get("reference")
        disp_in = d.get("reference_display")
    else:
        meaning = d.meaning
        ref_in = d.reference
        disp_in = d.reference_display

    ref: dict = {}
    if ref_in:
        ref["reference"] = ref_in
    if disp_in:
        ref["display"] = disp_in
    if not meaning or not ref:
        return None
    return {
        "meaning": fhir_enum(meaning),
        "reference": ref,
    }


def _provision_from_payload(
    p: ConsentProvisionInput | dict | None,
) -> dict | None:
    if not p:
        return None
    res: dict[str, Any] = {}
    if isinstance(p, dict):
        p_type = p.get("type")
        p_start = p.get("period_start")
        p_end = p.get("period_end")
        actors = p.get("actor")
        actions = p.get("action")
        sec_labels = p.get("security_label")
        purposes = p.get("purpose")
        classes = p.get("class") or p.get("class_")
        codes = p.get("code")
        dp_start = p.get("data_period_start")
        dp_end = p.get("data_period_end")
        data_list = p.get("data")
        subs = p.get("provision")
    else:
        p_type = p.type
        p_start = p.period_start
        p_end = p.period_end
        actors = p.actor
        actions = p.action
        sec_labels = p.security_label
        purposes = p.purpose
        classes = getattr(p, "class_", None)
        codes = p.code
        dp_start = p.data_period_start
        dp_end = p.data_period_end
        data_list = p.data
        subs = p.provision

    if p_type:
        res["type"] = fhir_enum(p_type)
    if p_start or p_end:
        period: dict = {}
        if p_start:
            period["start"] = fhir_instant(p_start)
        if p_end:
            period["end"] = fhir_instant(p_end)
        res["period"] = period

    if actors:
        act_res = [_provision_actor_from_payload(a) for a in actors]
        act_res = [a for a in act_res if a]
        if act_res:
            res["actor"] = act_res

    if actions:
        act_res = [_codeable_concept_from_payload(act) for act in actions]
        act_res = [act for act in act_res if act]
        if act_res:
            res["action"] = act_res

    if sec_labels:
        sec_res = [_coding_from_payload(s) for s in sec_labels]
        sec_res = [s for s in sec_res if s]
        if sec_res:
            res["securityLabel"] = sec_res

    if purposes:
        purp_res = [_coding_from_payload(pr) for pr in purposes]
        purp_res = [pr for pr in purp_res if pr]
        if purp_res:
            res["purpose"] = purp_res

    if classes:
        cls_res = [_coding_from_payload(cl) for cl in classes]
        cls_res = [cl for cl in cls_res if cl]
        if cls_res:
            res["class"] = cls_res

    if codes:
        cd_res = [_codeable_concept_from_payload(cd) for cd in codes]
        cd_res = [cd for cd in cd_res if cd]
        if cd_res:
            res["code"] = cd_res

    if dp_start or dp_end:
        dp: dict = {}
        if dp_start:
            dp["start"] = fhir_instant(dp_start)
        if dp_end:
            dp["end"] = fhir_instant(dp_end)
        res["dataPeriod"] = dp

    if data_list:
        dt_res = [_provision_data_from_payload(dt) for dt in data_list]
        dt_res = [dt for dt in dt_res if dt]
        if dt_res:
            res["data"] = dt_res

    if subs:
        sub_res = [_provision_from_payload(sub) for sub in subs]
        sub_res = [sub for sub in sub_res if sub]
        if sub_res:
            res["provision"] = sub_res

    return res or None


def _ref_from_payload(ref: ConsentReferenceInput | dict | None) -> dict | None:
    if not ref:
        return None
    if isinstance(ref, dict):
        r = ref.get("reference")
        d = ref.get("display")
    else:
        r = ref.reference
        d = ref.display
    entry: dict = {}
    if r:
        entry["reference"] = r
    if d:
        entry["display"] = d
    return entry or None


def payload_to_fhir_consent(payload: ConsentCreateSchema) -> dict:
    """Build a minimal FHIR R4 Consent resource dict from create schema."""
    res: dict[str, Any] = {
        "resourceType": "Consent",
        "status": fhir_enum(payload.status),
    }

    scope = _codeable_concept_from_payload(payload.scope)
    if scope:
        res["scope"] = scope

    if payload.category:
        cats = [_codeable_concept_from_payload(c) for c in payload.category]
        cats = [c for c in cats if c]
        if cats:
            res["category"] = cats

    if payload.patient or payload.patient_display:
        pat: dict = {}
        if payload.patient:
            pat["reference"] = payload.patient
        if payload.patient_display:
            pat["display"] = payload.patient_display
        if pat:
            res["patient"] = pat

    if payload.date_time:
        res["dateTime"] = fhir_instant(payload.date_time)

    if payload.performer:
        perfs = [_ref_from_payload(p) for p in payload.performer]
        perfs = [p for p in perfs if p]
        if perfs:
            res["performer"] = perfs

    if payload.organization:
        orgs = [_ref_from_payload(o) for o in payload.organization]
        orgs = [o for o in orgs if o]
        if orgs:
            res["organization"] = orgs

    if payload.source_attachment is not None:
        res["sourceAttachment"] = payload.source_attachment
    elif payload.source_reference or payload.source_reference_display:
        s_ref: dict = {}
        if payload.source_reference:
            s_ref["reference"] = payload.source_reference
        if payload.source_reference_display:
            s_ref["display"] = payload.source_reference_display
        if s_ref:
            res["sourceReference"] = s_ref

    if payload.policy:
        policies = [_policy_from_payload(p) for p in payload.policy]
        policies = [p for p in policies if p]
        if policies:
            res["policy"] = policies

    if payload.policy_rule:
        pol_rule = _codeable_concept_from_payload(payload.policy_rule)
        if pol_rule:
            res["policyRule"] = pol_rule

    if payload.verification:
        vers = [_verification_from_payload(v) for v in payload.verification]
        vers = [v for v in vers if v]
        if vers:
            res["verification"] = vers

    if payload.provision:
        prov = _provision_from_payload(payload.provision)
        if prov:
            res["provision"] = prov

    if payload.identifier:
        idents = [_identifier_from_payload(i) for i in payload.identifier]
        idents = [i for i in idents if i]
        if idents:
            res["identifier"] = idents

    if payload.extension:
        res["extension"] = payload.extension

    return {k: v for k, v in res.items() if v is not None}


def patch_fragment_to_fhir_consent(
    payload: ConsentPatchSchema,
) -> tuple[dict[str, Any], set[str]]:
    """Convert a partial patch payload to a FHIR fragment and set of touched fields."""
    fragment: dict[str, Any] = {}
    touched: set[str] = set()
    fields_set = payload.model_fields_set

    if "status" in fields_set:
        touched.add("status")
        if payload.status is not None:
            fragment["status"] = fhir_enum(payload.status)

    if "scope" in fields_set:
        touched.add("scope")
        if payload.scope is not None:
            fragment["scope"] = _codeable_concept_from_payload(payload.scope)

    if "category" in fields_set:
        touched.add("category")
        if payload.category is not None:
            fragment["category"] = [
                c
                for c in [
                    _codeable_concept_from_payload(x) for x in payload.category
                ]
                if c
            ]

    if _PATIENT_FIELDS & fields_set:
        touched.add("patient")
        if payload.patient is not None or payload.patient_display is not None:
            ref: dict = {}
            if payload.patient:
                ref["reference"] = payload.patient
            if payload.patient_display:
                ref["display"] = payload.patient_display
            if ref:
                fragment["patient"] = ref

    if "date_time" in fields_set:
        touched.add("dateTime")
        if payload.date_time is not None:
            fragment["dateTime"] = fhir_instant(payload.date_time)

    if "performer" in fields_set:
        touched.add("performer")
        if payload.performer is not None:
            fragment["performer"] = [
                p
                for p in [_ref_from_payload(x) for x in payload.performer]
                if p
            ]

    if "organization" in fields_set:
        touched.add("organization")
        if payload.organization is not None:
            fragment["organization"] = [
                o
                for o in [_ref_from_payload(x) for x in payload.organization]
                if o
            ]

    if "source_attachment" in fields_set:
        touched.add("sourceAttachment")
        if payload.source_attachment is not None:
            fragment["sourceAttachment"] = payload.source_attachment

    if _SOURCE_REF_FIELDS & fields_set:
        touched.add("sourceReference")
        if (
            payload.source_reference is not None
            or payload.source_reference_display is not None
        ):
            ref = {}
            if payload.source_reference:
                ref["reference"] = payload.source_reference
            if payload.source_reference_display:
                ref["display"] = payload.source_reference_display
            if ref:
                fragment["sourceReference"] = ref

    if "policy" in fields_set:
        touched.add("policy")
        if payload.policy is not None:
            fragment["policy"] = [
                p
                for p in [_policy_from_payload(x) for x in payload.policy]
                if p
            ]

    if "policy_rule" in fields_set:
        touched.add("policyRule")
        if payload.policy_rule is not None:
            fragment["policyRule"] = _codeable_concept_from_payload(
                payload.policy_rule
            )

    if "verification" in fields_set:
        touched.add("verification")
        if payload.verification is not None:
            fragment["verification"] = [
                v
                for v in [
                    _verification_from_payload(x) for x in payload.verification
                ]
                if v
            ]

    if "provision" in fields_set:
        touched.add("provision")
        if payload.provision is not None:
            fragment["provision"] = _provision_from_payload(payload.provision)

    if "identifier" in fields_set:
        touched.add("identifier")
        if payload.identifier is not None:
            fragment["identifier"] = [
                i
                for i in [_identifier_from_payload(x) for x in payload.identifier]
                if i
            ]

    if "extension" in fields_set:
        touched.add("extension")
        if payload.extension is not None:
            fragment["extension"] = payload.extension

    return fragment, touched
