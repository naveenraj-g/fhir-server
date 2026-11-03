"""Payload -> FHIR JSON conversion for Measure.

Mirror image of fhir.py. Reads the validated Pydantic input schema
(MeasureCreateSchema / MeasurePatchSchema and nested sub-schemas)
rather than the persisted ORM model, before anything is written to the DB.
Used by the service layer for pre-write base FHIR R4 validation.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Any

from app.fhir.datatypes import fhir_enum

if TYPE_CHECKING:
    from app.schemas.measure.input import (
        MeasureCreateSchema,
        MeasurePatchSchema,
    )


def _val(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _format_datetime(val: Any) -> str | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            val = val.replace(tzinfo=timezone.utc)
        return val.isoformat()
    if isinstance(val, date):
        return val.isoformat()
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return str(val)


def _coding_from_payload(c: Any) -> dict:
    if isinstance(c, dict):
        return {
            k: v
            for k, v in {
                "system": c.get("system"),
                "version": c.get("version"),
                "code": c.get("code"),
                "display": c.get("display"),
                "userSelected": c.get("user_selected"),
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


def payload_measure_codeable_concept(cc: Any) -> dict | None:
    if cc is None:
        return None
    codings = _val(cc, "coding", None)
    coding_list = [_coding_from_payload(c) for c in codings] if codings else []
    text = _val(cc, "text", None)
    result: dict[str, Any] = {}
    if coding_list:
        result["coding"] = coding_list
    if text:
        result["text"] = text
    return result or None


def payload_measure_period(start: Any, end: Any) -> dict | None:
    result: dict[str, Any] = {}
    if start:
        result["start"] = _format_datetime(start)
    if end:
        result["end"] = _format_datetime(end)
    return result or None


def payload_measure_ref(reference: Any, display: Any = None) -> dict | None:
    result: dict[str, Any] = {}
    if reference:
        result["reference"] = reference
    if display:
        result["display"] = display
    return result or None


def payload_measure_identifier(ident: Any) -> dict | None:
    if ident is None:
        return None
    result: dict[str, Any] = {}
    use = _val(ident, "use", None)
    if use:
        result["use"] = fhir_enum(use)

    type_codings = _val(ident, "type_coding", None) or _val(ident, "type_codings", None)
    type_text = _val(ident, "type_text", None)
    if type_codings or type_text:
        cc: dict[str, Any] = {}
        if type_codings:
            cc["coding"] = [_coding_from_payload(c) for c in type_codings]
        if type_text:
            cc["text"] = type_text
        result["type"] = cc

    system = _val(ident, "system", None)
    if system:
        result["system"] = system

    val = _val(ident, "value", None)
    if val:
        result["value"] = val

    period = payload_measure_period(
        _val(ident, "period_start", None), _val(ident, "period_end", None)
    )
    if period:
        result["period"] = period

    assigner_ref = _val(ident, "assigner", None) or _val(ident, "assigner_reference", None)
    assigner_type = _val(ident, "assigner_type", None)
    assigner_id = _val(ident, "assigner_id", None)
    if not assigner_ref and assigner_type and assigner_id:
        assigner_ref = f"{fhir_enum(assigner_type)}/{assigner_id}"
    assigner = payload_measure_ref(
        assigner_ref, _val(ident, "assigner_display", None)
    )
    if assigner:
        result["assigner"] = assigner

    return result or None


def payload_measure_telecom(t: Any) -> dict | None:
    if t is None:
        return None
    result: dict[str, Any] = {}
    sys = _val(t, "system", None)
    if sys:
        result["system"] = fhir_enum(sys)
    val = _val(t, "value", None)
    if val:
        result["value"] = val
    use = _val(t, "use", None)
    if use:
        result["use"] = fhir_enum(use)
    rank = _val(t, "rank", None)
    if rank is not None:
        result["rank"] = rank
    period = payload_measure_period(
        _val(t, "period_start", None), _val(t, "period_end", None)
    )
    if period:
        result["period"] = period
    return result or None


def payload_measure_contact(c: Any) -> dict | None:
    if c is None:
        return None
    result: dict[str, Any] = {}
    name = _val(c, "name", None)
    if name:
        result["name"] = name
    telecoms = _val(c, "telecom", None) or _val(c, "telecoms", None)
    if telecoms:
        tl = [payload_measure_telecom(t) for t in telecoms]
        tl = [t for t in tl if t]
        if tl:
            result["telecom"] = tl
    return result or None


def payload_measure_use_context(uc: Any) -> dict | None:
    if uc is None:
        return None
    result: dict[str, Any] = {}
    code_dict: dict[str, Any] = {}
    code_sys = _val(uc, "code_system", None)
    if code_sys:
        code_dict["system"] = code_sys
    code_ver = _val(uc, "code_version", None)
    if code_ver:
        code_dict["version"] = code_ver
    code_c = _val(uc, "code_code", None)
    if code_c:
        code_dict["code"] = code_c
    code_disp = _val(uc, "code_display", None)
    if code_disp:
        code_dict["display"] = code_disp
    code_us = _val(uc, "code_user_selected", None)
    if code_us is not None:
        code_dict["userSelected"] = code_us
    if code_dict:
        result["code"] = code_dict

    # value[x]
    val_codings = _val(uc, "value_codeable_concept_coding", None) or _val(uc, "value_codings", None)
    val_text = _val(uc, "value_codeable_concept_text", None)
    if val_codings or val_text:
        vcc: dict[str, Any] = {}
        if val_codings:
            vcc["coding"] = [_coding_from_payload(c) for c in val_codings]
        if val_text:
            vcc["text"] = val_text
        result["valueCodeableConcept"] = vcc
    elif (
        _val(uc, "value_quantity_value", None) is not None
        or _val(uc, "value_quantity_unit", None)
        or _val(uc, "value_quantity_system", None)
        or _val(uc, "value_quantity_code", None)
    ):
        vq: dict[str, Any] = {}
        if _val(uc, "value_quantity_value", None) is not None:
            vq["value"] = float(_val(uc, "value_quantity_value"))
        comp = _val(uc, "value_quantity_comparator", None)
        if comp:
            vq["comparator"] = fhir_enum(comp)
        if _val(uc, "value_quantity_unit", None):
            vq["unit"] = _val(uc, "value_quantity_unit")
        if _val(uc, "value_quantity_system", None):
            vq["system"] = _val(uc, "value_quantity_system")
        if _val(uc, "value_quantity_code", None):
            vq["code"] = _val(uc, "value_quantity_code")
        result["valueQuantity"] = vq
    elif (
        _val(uc, "value_range_low_value", None) is not None
        or _val(uc, "value_range_high_value", None) is not None
    ):
        vr: dict[str, Any] = {}
        if _val(uc, "value_range_low_value", None) is not None:
            low_q: dict[str, Any] = {
                "value": float(_val(uc, "value_range_low_value"))
            }
            if _val(uc, "value_range_low_unit", None):
                low_q["unit"] = _val(uc, "value_range_low_unit")
            if _val(uc, "value_range_low_system", None):
                low_q["system"] = _val(uc, "value_range_low_system")
            if _val(uc, "value_range_low_code", None):
                low_q["code"] = _val(uc, "value_range_low_code")
            vr["low"] = low_q
        if _val(uc, "value_range_high_value", None) is not None:
            high_q: dict[str, Any] = {
                "value": float(_val(uc, "value_range_high_value"))
            }
            if _val(uc, "value_range_high_unit", None):
                high_q["unit"] = _val(uc, "value_range_high_unit")
            if _val(uc, "value_range_high_system", None):
                high_q["system"] = _val(uc, "value_range_high_system")
            if _val(uc, "value_range_high_code", None):
                high_q["code"] = _val(uc, "value_range_high_code")
            vr["high"] = high_q
        result["valueRange"] = vr
    elif _val(uc, "value_reference", None) or (
        _val(uc, "value_reference_type", None)
        and _val(uc, "value_reference_id", None)
    ):
        vref = _val(uc, "value_reference", None)
        if not vref and _val(uc, "value_reference_type", None) and _val(uc, "value_reference_id", None):
            vref = f"{fhir_enum(_val(uc, 'value_reference_type'))}/{_val(uc, 'value_reference_id')}"
        ref_dict = payload_measure_ref(vref, _val(uc, "value_reference_display", None))
        if ref_dict:
            result["valueReference"] = ref_dict

    return result or None


def payload_measure_related_artifact(ra: Any) -> dict | None:
    if ra is None:
        return None
    result: dict[str, Any] = {"type": fhir_enum(_val(ra, "type"))}
    for field in ("label", "display", "citation", "url", "document", "resource"):
        v = _val(ra, field, None)
        if v is not None:
            result[field] = v
    return result


def payload_measure_expression(expr: Any) -> dict | None:
    if expr is None:
        return None
    result: dict[str, Any] = {}
    desc = _val(expr, "description", None)
    if desc:
        result["description"] = desc
    name = _val(expr, "name", None)
    if name:
        result["name"] = name
    lang = _val(expr, "language", None)
    if lang:
        result["language"] = lang
    ex = _val(expr, "expression", None)
    if ex:
        result["expression"] = ex
    ref = _val(expr, "reference", None)
    if ref:
        result["reference"] = ref
    return result or None


def payload_measure_group(g: Any) -> dict | None:
    if g is None:
        return None
    result: dict[str, Any] = {}
    code = payload_measure_codeable_concept(_val(g, "code", None))
    if code:
        result["code"] = code
    desc = _val(g, "description", None)
    if desc:
        result["description"] = desc

    populations = _val(g, "population", None)
    if populations:
        pops = []
        for p in populations:
            pd: dict[str, Any] = {}
            p_code = payload_measure_codeable_concept(_val(p, "code", None))
            if p_code:
                pd["code"] = p_code
            p_desc = _val(p, "description", None)
            if p_desc:
                pd["description"] = p_desc
            crit = payload_measure_expression(_val(p, "criteria", None))
            if crit:
                pd["criteria"] = crit
            if pd:
                pops.append(pd)
        if pops:
            result["population"] = pops

    stratifiers = _val(g, "stratifier", None)
    if stratifiers:
        strats = []
        for s in stratifiers:
            sd: dict[str, Any] = {}
            s_code = payload_measure_codeable_concept(_val(s, "code", None))
            if s_code:
                sd["code"] = s_code
            s_desc = _val(s, "description", None)
            if s_desc:
                sd["description"] = s_desc
            crit = payload_measure_expression(_val(s, "criteria", None))
            if crit:
                sd["criteria"] = crit

            comps = _val(s, "component", None)
            if comps:
                cd_list = []
                for c in comps:
                    cd: dict[str, Any] = {}
                    c_code = payload_measure_codeable_concept(_val(c, "code", None))
                    if c_code:
                        cd["code"] = c_code
                    c_desc = _val(c, "description", None)
                    if c_desc:
                        cd["description"] = c_desc
                    c_crit = payload_measure_expression(_val(c, "criteria", None))
                    if c_crit:
                        cd["criteria"] = c_crit
                    if cd:
                        cd_list.append(cd)
                if cd_list:
                    sd["component"] = cd_list
            if sd:
                strats.append(sd)
        if strats:
            result["stratifier"] = strats

    return result or None


def payload_measure_supplemental_data(sd: Any) -> dict | None:
    if sd is None:
        return None
    result: dict[str, Any] = {}
    code = payload_measure_codeable_concept(_val(sd, "code", None))
    if code:
        result["code"] = code

    usages = _val(sd, "usage", None)
    if usages:
        ul = [payload_measure_codeable_concept(u) for u in usages]
        ul = [u for u in ul if u]
        if ul:
            result["usage"] = ul

    desc = _val(sd, "description", None)
    if desc:
        result["description"] = desc

    crit = payload_measure_expression(_val(sd, "criteria", None))
    if crit:
        result["criteria"] = crit

    return result or None


def payload_to_fhir_measure(
    payload: MeasureCreateSchema | dict[str, Any],
) -> dict[str, Any]:
    """Convert a CREATE payload to full FHIR R4 dict for pre-write validation."""
    result: dict[str, Any] = {
        "resourceType": "Measure",
        "id": "placeholder",
    }

    ext = _val(payload, "extension", None)
    if ext:
        result["extension"] = list(ext)

    url = _val(payload, "url", None)
    if url:
        result["url"] = url

    idents = _val(payload, "identifier", None)
    if idents:
        id_list = [payload_measure_identifier(i) for i in idents]
        id_list = [i for i in id_list if i]
        if id_list:
            result["identifier"] = id_list

    version = _val(payload, "version", None)
    if version:
        result["version"] = version

    name = _val(payload, "name", None)
    if name:
        result["name"] = name

    title = _val(payload, "title", None)
    if title:
        result["title"] = title

    subtitle = _val(payload, "subtitle", None)
    if subtitle:
        result["subtitle"] = subtitle

    status = _val(payload, "status", None)
    if status:
        result["status"] = fhir_enum(status)

    exp = _val(payload, "experimental", None)
    if exp is not None:
        result["experimental"] = exp

    # subject[x]
    subj_cc = _val(payload, "subject_codeable_concept", None)
    if subj_cc:
        result["subjectCodeableConcept"] = payload_measure_codeable_concept(subj_cc)
    else:
        subj_ref = _val(payload, "subject_reference", None)
        if subj_ref:
            result["subjectReference"] = payload_measure_ref(
                subj_ref, _val(payload, "subject_reference_display", None)
            )

    d = _val(payload, "date", None)
    if d:
        result["date"] = _format_datetime(d)

    pub = _val(payload, "publisher", None)
    if pub:
        result["publisher"] = pub

    contacts = _val(payload, "contact", None)
    if contacts:
        cl = [payload_measure_contact(c) for c in contacts]
        cl = [c for c in cl if c]
        if cl:
            result["contact"] = cl

    desc = _val(payload, "description", None)
    if desc:
        result["description"] = desc

    use_contexts = _val(payload, "use_context", None)
    if use_contexts:
        ucl = [payload_measure_use_context(uc) for uc in use_contexts]
        ucl = [uc for uc in ucl if uc]
        if ucl:
            result["useContext"] = ucl

    jurisdictions = _val(payload, "jurisdiction", None)
    if jurisdictions:
        jl = [payload_measure_codeable_concept(j) for j in jurisdictions]
        jl = [j for j in jl if j]
        if jl:
            result["jurisdiction"] = jl

    purpose = _val(payload, "purpose", None)
    if purpose:
        result["purpose"] = purpose

    usage = _val(payload, "usage", None)
    if usage:
        result["usage"] = usage

    cright = _val(payload, "copyright", None)
    if cright:
        result["copyright"] = cright

    app_date = _val(payload, "approval_date", None)
    if app_date:
        result["approvalDate"] = _format_datetime(app_date)

    lr_date = _val(payload, "last_review_date", None)
    if lr_date:
        result["lastReviewDate"] = _format_datetime(lr_date)

    ep_start = _val(payload, "effective_period_start", None)
    ep_end = _val(payload, "effective_period_end", None)
    if ep_start or ep_end:
        per = payload_measure_period(ep_start, ep_end)
        if per:
            result["effectivePeriod"] = per

    topics = _val(payload, "topic", None)
    if topics:
        tl = [payload_measure_codeable_concept(t) for t in topics]
        tl = [t for t in tl if t]
        if tl:
            result["topic"] = tl

    for role_key in ("author", "editor", "reviewer", "endorser"):
        r_contacts = _val(payload, role_key, None)
        if r_contacts:
            rcl = [payload_measure_contact(c) for c in r_contacts]
            rcl = [c for c in rcl if c]
            if rcl:
                result[role_key] = rcl

    ras = _val(payload, "related_artifact", None)
    if ras:
        ral = [payload_measure_related_artifact(ra) for ra in ras]
        ral = [ra for ra in ral if ra]
        if ral:
            result["relatedArtifact"] = ral

    lib = _val(payload, "library", None)
    if lib:
        result["library"] = list(lib)

    disclaimer = _val(payload, "disclaimer", None)
    if disclaimer:
        result["disclaimer"] = disclaimer

    scoring = _val(payload, "scoring", None)
    if scoring:
        result["scoring"] = payload_measure_codeable_concept(scoring)

    comp_scoring = _val(payload, "composite_scoring", None)
    if comp_scoring:
        result["compositeScoring"] = payload_measure_codeable_concept(comp_scoring)

    types = _val(payload, "type", None)
    if types:
        typel = [payload_measure_codeable_concept(t) for t in types]
        typel = [t for t in typel if t]
        if typel:
            result["type"] = typel

    ra_adj = _val(payload, "risk_adjustment", None)
    if ra_adj:
        result["riskAdjustment"] = ra_adj

    rate_agg = _val(payload, "rate_aggregation", None)
    if rate_agg:
        result["rateAggregation"] = rate_agg

    rationale = _val(payload, "rationale", None)
    if rationale:
        result["rationale"] = rationale

    clin_rec = _val(payload, "clinical_recommendation_statement", None)
    if clin_rec:
        result["clinicalRecommendationStatement"] = clin_rec

    imp_not = _val(payload, "improvement_notation", None)
    if imp_not:
        result["improvementNotation"] = payload_measure_codeable_concept(imp_not)

    defn = _val(payload, "definition", None)
    if defn:
        result["definition"] = list(defn)

    guidance = _val(payload, "guidance", None)
    if guidance:
        result["guidance"] = guidance

    groups = _val(payload, "group", None)
    if groups:
        gl = [payload_measure_group(g) for g in groups]
        gl = [g for g in gl if g]
        if gl:
            result["group"] = gl

    supp_data = _val(payload, "supplemental_data", None)
    if supp_data:
        sdl = [payload_measure_supplemental_data(sd) for sd in supp_data]
        sdl = [sd for sd in sdl if sd]
        if sdl:
            result["supplementalData"] = sdl

    return result


_SUBJECT_FIELDS = {
    "subject_codeable_concept",
    "subject_reference",
    "subject_reference_display",
}

_EFFECTIVE_PERIOD_FIELDS = {
    "effective_period_start",
    "effective_period_end",
}


def patch_fragment_to_fhir_measure(
    payload: MeasurePatchSchema | dict[str, Any],
) -> tuple[dict[str, Any], set[str]]:
    """Convert a PATCH fragment to partial FHIR dict + touched FHIR top-level keys."""
    provided: set[str] = (
        payload.model_fields_set
        if hasattr(payload, "model_fields_set")
        else set(payload.keys())
    )
    fragment: dict[str, Any] = {}
    touched: set[str] = set()

    if "extension" in provided:
        touched.add("extension")
        ext = _val(payload, "extension", None)
        fragment["extension"] = list(ext) if ext is not None else None

    if "url" in provided:
        touched.add("url")
        fragment["url"] = _val(payload, "url", None)

    if "identifier" in provided:
        touched.add("identifier")
        idents = _val(payload, "identifier", None)
        fragment["identifier"] = (
            [payload_measure_identifier(i) for i in idents]
            if idents is not None
            else None
        )

    if "version" in provided:
        touched.add("version")
        fragment["version"] = _val(payload, "version", None)

    if "name" in provided:
        touched.add("name")
        fragment["name"] = _val(payload, "name", None)

    if "title" in provided:
        touched.add("title")
        fragment["title"] = _val(payload, "title", None)

    if "subtitle" in provided:
        touched.add("subtitle")
        fragment["subtitle"] = _val(payload, "subtitle", None)

    if "status" in provided:
        touched.add("status")
        st = _val(payload, "status", None)
        fragment["status"] = fhir_enum(st) if st is not None else None

    if "experimental" in provided:
        touched.add("experimental")
        fragment["experimental"] = _val(payload, "experimental", None)

    if provided & _SUBJECT_FIELDS:
        touched.add("subjectCodeableConcept")
        touched.add("subjectReference")
        scc = _val(payload, "subject_codeable_concept", None)
        sref = _val(payload, "subject_reference", None)
        if scc is not None:
            fragment["subjectCodeableConcept"] = payload_measure_codeable_concept(scc)
            fragment["subjectReference"] = None
        elif sref is not None:
            fragment["subjectReference"] = payload_measure_ref(
                sref, _val(payload, "subject_reference_display", None)
            )
            fragment["subjectCodeableConcept"] = None
        else:
            fragment["subjectCodeableConcept"] = None
            fragment["subjectReference"] = None

    if "date" in provided:
        touched.add("date")
        d = _val(payload, "date", None)
        fragment["date"] = _format_datetime(d) if d is not None else None

    if "publisher" in provided:
        touched.add("publisher")
        fragment["publisher"] = _val(payload, "publisher", None)

    if "contact" in provided:
        touched.add("contact")
        contacts = _val(payload, "contact", None)
        fragment["contact"] = (
            [payload_measure_contact(c) for c in contacts]
            if contacts is not None
            else None
        )

    if "description" in provided:
        touched.add("description")
        fragment["description"] = _val(payload, "description", None)

    if "use_context" in provided:
        touched.add("useContext")
        ucs = _val(payload, "use_context", None)
        fragment["useContext"] = (
            [payload_measure_use_context(uc) for uc in ucs]
            if ucs is not None
            else None
        )

    if "jurisdiction" in provided:
        touched.add("jurisdiction")
        jurs = _val(payload, "jurisdiction", None)
        fragment["jurisdiction"] = (
            [payload_measure_codeable_concept(j) for j in jurs]
            if jurs is not None
            else None
        )

    if "purpose" in provided:
        touched.add("purpose")
        fragment["purpose"] = _val(payload, "purpose", None)

    if "usage" in provided:
        touched.add("usage")
        fragment["usage"] = _val(payload, "usage", None)

    if "copyright" in provided:
        touched.add("copyright")
        fragment["copyright"] = _val(payload, "copyright", None)

    if "approval_date" in provided:
        touched.add("approvalDate")
        ad = _val(payload, "approval_date", None)
        fragment["approvalDate"] = _format_datetime(ad) if ad is not None else None

    if "last_review_date" in provided:
        touched.add("lastReviewDate")
        lrd = _val(payload, "last_review_date", None)
        fragment["lastReviewDate"] = _format_datetime(lrd) if lrd is not None else None

    if provided & _EFFECTIVE_PERIOD_FIELDS:
        touched.add("effectivePeriod")
        ep_start = _val(payload, "effective_period_start", None)
        ep_end = _val(payload, "effective_period_end", None)
        fragment["effectivePeriod"] = (
            payload_measure_period(ep_start, ep_end)
            if (ep_start is not None or ep_end is not None)
            else None
        )

    if "topic" in provided:
        touched.add("topic")
        topics = _val(payload, "topic", None)
        fragment["topic"] = (
            [payload_measure_codeable_concept(t) for t in topics]
            if topics is not None
            else None
        )

    for role_key in ("author", "editor", "reviewer", "endorser"):
        if role_key in provided:
            touched.add(role_key)
            r_contacts = _val(payload, role_key, None)
            fragment[role_key] = (
                [payload_measure_contact(c) for c in r_contacts]
                if r_contacts is not None
                else None
            )

    if "related_artifact" in provided:
        touched.add("relatedArtifact")
        ras = _val(payload, "related_artifact", None)
        fragment["relatedArtifact"] = (
            [payload_measure_related_artifact(ra) for ra in ras]
            if ras is not None
            else None
        )

    if "library" in provided:
        touched.add("library")
        lib = _val(payload, "library", None)
        fragment["library"] = list(lib) if lib is not None else None

    if "disclaimer" in provided:
        touched.add("disclaimer")
        fragment["disclaimer"] = _val(payload, "disclaimer", None)

    if "scoring" in provided:
        touched.add("scoring")
        sc = _val(payload, "scoring", None)
        fragment["scoring"] = (
            payload_measure_codeable_concept(sc) if sc is not None else None
        )

    if "composite_scoring" in provided:
        touched.add("compositeScoring")
        cs = _val(payload, "composite_scoring", None)
        fragment["compositeScoring"] = (
            payload_measure_codeable_concept(cs) if cs is not None else None
        )

    if "type" in provided:
        touched.add("type")
        types = _val(payload, "type", None)
        fragment["type"] = (
            [payload_measure_codeable_concept(t) for t in types]
            if types is not None
            else None
        )

    if "risk_adjustment" in provided:
        touched.add("riskAdjustment")
        fragment["riskAdjustment"] = _val(payload, "risk_adjustment", None)

    if "rate_aggregation" in provided:
        touched.add("rateAggregation")
        fragment["rateAggregation"] = _val(payload, "rate_aggregation", None)

    if "rationale" in provided:
        touched.add("rationale")
        fragment["rationale"] = _val(payload, "rationale", None)

    if "clinical_recommendation_statement" in provided:
        touched.add("clinicalRecommendationStatement")
        fragment["clinicalRecommendationStatement"] = _val(
            payload, "clinical_recommendation_statement", None
        )

    if "improvement_notation" in provided:
        touched.add("improvementNotation")
        imp = _val(payload, "improvement_notation", None)
        fragment["improvementNotation"] = (
            payload_measure_codeable_concept(imp) if imp is not None else None
        )

    if "definition" in provided:
        touched.add("definition")
        defn = _val(payload, "definition", None)
        fragment["definition"] = list(defn) if defn is not None else None

    if "guidance" in provided:
        touched.add("guidance")
        fragment["guidance"] = _val(payload, "guidance", None)

    if "group" in provided:
        touched.add("group")
        groups = _val(payload, "group", None)
        fragment["group"] = (
            [payload_measure_group(g) for g in groups]
            if groups is not None
            else None
        )

    if "supplemental_data" in provided:
        touched.add("supplementalData")
        supp_data = _val(payload, "supplemental_data", None)
        fragment["supplementalData"] = (
            [payload_measure_supplemental_data(sd) for sd in supp_data]
            if supp_data is not None
            else None
        )

    return fragment, touched
