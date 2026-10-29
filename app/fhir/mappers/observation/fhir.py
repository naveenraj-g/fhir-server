from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.observation import ObservationModel

_COMPARATOR_SYMBOLS = {"lt": "<", "le": "<=", "ge": ">=", "gt": ">"}


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


def _fhir_reference(obj, prefix: str) -> dict:
    raw_reference = getattr(obj, f"{prefix}_reference", None)
    ref_type = getattr(obj, f"{prefix}_type", None)
    ref_id = getattr(obj, f"{prefix}_id", None)
    display = getattr(obj, f"{prefix}_display", None)

    entry: dict = {}
    if raw_reference:
        entry["reference"] = raw_reference
    elif ref_type and ref_id:
        entry["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        entry["display"] = display
    return entry


def _fhir_reference_with_identifier_fallback(obj, prefix: str) -> dict:
    entry = _fhir_reference(obj, prefix)

    id_use = getattr(obj, f"{prefix}_identifier_use", None)
    id_type_system = getattr(obj, f"{prefix}_identifier_type_system", None)
    id_type_version = getattr(obj, f"{prefix}_identifier_type_version", None)
    id_type_code = getattr(obj, f"{prefix}_identifier_type_code", None)
    id_type_display = getattr(obj, f"{prefix}_identifier_type_display", None)
    id_type_text = getattr(obj, f"{prefix}_identifier_type_text", None)
    id_type_user_selected = getattr(obj, f"{prefix}_identifier_type_user_selected", None)
    id_system = getattr(obj, f"{prefix}_identifier_system", None)
    id_value = getattr(obj, f"{prefix}_identifier_value", None)
    id_period_start = getattr(obj, f"{prefix}_identifier_period_start", None)
    id_period_end = getattr(obj, f"{prefix}_identifier_period_end", None)

    if id_use or id_type_system or id_type_code or id_type_text or id_system or id_value:
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
                for k, v in {"start": fhir_instant(id_period_start), "end": fhir_instant(id_period_end)}.items()
                if v
            }
        entry["identifier"] = identifier
    return entry


def _fhir_quantity(obj, prefix: str) -> dict:
    value = getattr(obj, f"{prefix}_value", None)
    comparator = getattr(obj, f"{prefix}_comparator", None)
    return {
        k: v
        for k, v in {
            "value": float(value) if value is not None else None,
            "comparator": _COMPARATOR_SYMBOLS.get(fhir_enum(comparator)) if comparator else None,
            "unit": getattr(obj, f"{prefix}_unit", None),
            "system": getattr(obj, f"{prefix}_system", None),
            "code": getattr(obj, f"{prefix}_code", None),
        }.items()
        if v is not None
    }


def fhir_observation_identifier(obj, prefix: str = "") -> dict:
    """Renders a full ObservationIdentifier child row into a FHIR
    Identifier dict."""
    p = prefix
    entry: dict = {}
    use = getattr(obj, f"{p}use", None)
    if use:
        entry["use"] = fhir_enum(use)
    codings_attr = f"{p}type_codings" if p else "type_codings"
    coding = _fhir_coding_list(getattr(obj, codings_attr, None))
    type_text = getattr(obj, f"{p}type_text", None)
    if coding or type_text:
        type_cc: dict = {}
        if coding:
            type_cc["coding"] = coding
        if type_text:
            type_cc["text"] = type_text
        entry["type"] = type_cc
    system = getattr(obj, f"{p}system", None)
    if system:
        entry["system"] = system
    value = getattr(obj, f"{p}value", None)
    if value:
        entry["value"] = value
    period_start = getattr(obj, f"{p}period_start", None)
    period_end = getattr(obj, f"{p}period_end", None)
    if period_start or period_end:
        entry["period"] = {
            k: v for k, v in {"start": fhir_instant(period_start), "end": fhir_instant(period_end)}.items() if v
        }
    assigner = _fhir_reference_with_identifier_fallback(obj, f"{p}assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry


def fhir_observation_codeable_concept(codings, text: str | None) -> dict:
    """Generic CodeableConcept renderer — reused for every plain {coding[],
    text} field on this resource."""
    entry: dict = {}
    coding = _fhir_coding_list(codings)
    if coding:
        entry["coding"] = coding
    if text:
        entry["text"] = text
    return entry


def fhir_observation_note(n) -> dict:
    entry: dict = {}
    if n.author_string:
        entry["authorString"] = n.author_string
    else:
        ref = _fhir_reference(n, "author")
        if ref:
            entry["authorReference"] = ref
    if n.time:
        entry["time"] = fhir_instant(n.time)
    if n.text:
        entry["text"] = n.text
    return entry


def _fhir_reference_range(rr) -> dict:
    entry: dict = {}
    low = _fhir_quantity(rr, "low")
    if low:
        entry["low"] = low
    high = _fhir_quantity(rr, "high")
    if high:
        entry["high"] = high
    type_cc = fhir_observation_codeable_concept(rr.type_codings, rr.type_text)
    if type_cc:
        entry["type"] = type_cc
    applies_tos = [fhir_observation_codeable_concept(a.codings, a.text) for a in (rr.applies_tos or [])]
    applies_tos = [a for a in applies_tos if a]
    if applies_tos:
        entry["appliesTo"] = applies_tos
    age_low = _fhir_quantity(rr, "age_low")
    age_high = _fhir_quantity(rr, "age_high")
    if age_low or age_high:
        age: dict = {}
        if age_low:
            age["low"] = age_low
        if age_high:
            age["high"] = age_high
        entry["age"] = age
    if rr.text:
        entry["text"] = rr.text
    return entry


def _fhir_value_x(obj, out: dict) -> None:
    """Renders the 11-variant value[x] choice (shared shape between the
    root resource and its own component) directly into `out`."""
    value_quantity = _fhir_quantity(obj, "value_quantity")
    if value_quantity:
        out["valueQuantity"] = value_quantity
        return
    value_cc = fhir_observation_codeable_concept(
        getattr(obj, "value_codeable_concept_codings", None), obj.value_codeable_concept_text
    )
    if value_cc:
        out["valueCodeableConcept"] = value_cc
        return
    if obj.value_string:
        out["valueString"] = obj.value_string
        return
    if obj.value_boolean is not None:
        out["valueBoolean"] = obj.value_boolean
        return
    if obj.value_integer is not None:
        out["valueInteger"] = obj.value_integer
        return
    value_range_low = _fhir_quantity(obj, "value_range_low")
    value_range_high = _fhir_quantity(obj, "value_range_high")
    if value_range_low or value_range_high:
        range_entry: dict = {}
        if value_range_low:
            range_entry["low"] = value_range_low
        if value_range_high:
            range_entry["high"] = value_range_high
        out["valueRange"] = range_entry
        return
    value_ratio_num = _fhir_quantity(obj, "value_ratio_numerator")
    value_ratio_den = _fhir_quantity(obj, "value_ratio_denominator")
    if value_ratio_num or value_ratio_den:
        ratio_entry: dict = {}
        if value_ratio_num:
            ratio_entry["numerator"] = value_ratio_num
        if value_ratio_den:
            ratio_entry["denominator"] = value_ratio_den
        out["valueRatio"] = ratio_entry
        return
    sampled_data_origin = _fhir_quantity(obj, "value_sampled_data_origin")
    if (
        sampled_data_origin
        or obj.value_sampled_data_period is not None
        or obj.value_sampled_data_dimensions is not None
    ):
        sampled: dict = {}
        if sampled_data_origin:
            sampled["origin"] = sampled_data_origin
        if obj.value_sampled_data_period is not None:
            sampled["period"] = float(obj.value_sampled_data_period)
        if obj.value_sampled_data_factor is not None:
            sampled["factor"] = float(obj.value_sampled_data_factor)
        if obj.value_sampled_data_lower_limit is not None:
            sampled["lowerLimit"] = float(obj.value_sampled_data_lower_limit)
        if obj.value_sampled_data_upper_limit is not None:
            sampled["upperLimit"] = float(obj.value_sampled_data_upper_limit)
        if obj.value_sampled_data_dimensions is not None:
            sampled["dimensions"] = obj.value_sampled_data_dimensions
        if obj.value_sampled_data_data:
            sampled["data"] = obj.value_sampled_data_data
        out["valueSampledData"] = sampled
        return
    if obj.value_time:
        out["valueTime"] = obj.value_time.isoformat()
        return
    if obj.value_date_time:
        out["valueDateTime"] = fhir_instant(obj.value_date_time)
        return
    if obj.value_period_start or obj.value_period_end:
        out["valuePeriod"] = {
            k: v
            for k, v in {
                "start": fhir_instant(obj.value_period_start),
                "end": fhir_instant(obj.value_period_end),
            }.items()
            if v
        }


def fhir_observation_component(c) -> dict:
    entry: dict = {"code": fhir_observation_codeable_concept(c.code_codings, c.code_text)}
    _fhir_value_x(c, entry)
    data_absent_reason = fhir_observation_codeable_concept(c.data_absent_reason_codings, c.data_absent_reason_text)
    if data_absent_reason:
        entry["dataAbsentReason"] = data_absent_reason
    interpretations = [fhir_observation_codeable_concept(i.codings, i.text) for i in (c.interpretations or [])]
    interpretations = [i for i in interpretations if i]
    if interpretations:
        entry["interpretation"] = interpretations
    reference_ranges = [_fhir_reference_range(rr) for rr in (c.reference_ranges or [])]
    reference_ranges = [rr for rr in reference_ranges if rr]
    if reference_ranges:
        entry["referenceRange"] = reference_ranges
    return entry


_EXT_BASE = "https://fhir-server.dev/fhir/StructureDefinition"


def _fhir_meta(obs: ObservationModel) -> dict:
    meta: dict = {}
    if obs.updated_at:
        meta["lastUpdated"] = fhir_instant(obs.updated_at)
    extensions = []
    if obs.tenant_id:
        extensions.append({"url": f"{_EXT_BASE}/org-id", "valueString": obs.tenant_id})
    if obs.created_by:
        extensions.append({"url": f"{_EXT_BASE}/created-by", "valueString": obs.created_by})
    if obs.updated_by:
        extensions.append({"url": f"{_EXT_BASE}/updated-by", "valueString": obs.updated_by})
    if obs.created_at:
        extensions.append({"url": f"{_EXT_BASE}/created-at", "valueDateTime": fhir_instant(obs.created_at)})
    if extensions:
        meta["extension"] = extensions
    return meta


def to_fhir_observation(obs: ObservationModel) -> dict:
    result: dict = {"resourceType": "Observation", "id": str(obs.observation_id)}

    meta = _fhir_meta(obs)
    if meta:
        result["meta"] = meta
    if obs.extension:
        result["extension"] = list(obs.extension)

    identifiers = [fhir_observation_identifier(i) for i in (obs.identifiers or [])]
    if identifiers:
        result["identifier"] = identifiers

    based_ons = [_fhir_reference_with_identifier_fallback(b, "reference") for b in (obs.based_ons or [])]
    based_ons = [b for b in based_ons if b]
    if based_ons:
        result["basedOn"] = based_ons

    part_ofs = [_fhir_reference_with_identifier_fallback(p, "reference") for p in (obs.part_ofs or [])]
    part_ofs = [p for p in part_ofs if p]
    if part_ofs:
        result["partOf"] = part_ofs

    if obs.status:
        result["status"] = fhir_enum(obs.status).replace("_", "-")

    categories = [fhir_observation_codeable_concept(c.codings, c.text) for c in (obs.categories or [])]
    categories = [c for c in categories if c]
    if categories:
        result["category"] = categories

    result["code"] = fhir_observation_codeable_concept(obs.code_codings, obs.code_text)

    subject = _fhir_reference_with_identifier_fallback(obs, "subject")
    if subject:
        result["subject"] = subject

    focuses = [_fhir_reference_with_identifier_fallback(f, "reference") for f in (obs.focuses or [])]
    focuses = [f for f in focuses if f]
    if focuses:
        result["focus"] = focuses

    encounter = _fhir_reference_with_identifier_fallback(obs, "encounter")
    if encounter:
        result["encounter"] = encounter

    if obs.effective_date_time:
        result["effectiveDateTime"] = fhir_instant(obs.effective_date_time)
    elif obs.effective_period_start or obs.effective_period_end:
        result["effectivePeriod"] = {
            k: v
            for k, v in {
                "start": fhir_instant(obs.effective_period_start),
                "end": fhir_instant(obs.effective_period_end),
            }.items()
            if v
        }
    elif obs.effective_timing:
        result["effectiveTiming"] = dict(obs.effective_timing)
    elif obs.effective_instant:
        result["effectiveInstant"] = fhir_instant(obs.effective_instant)

    if obs.issued:
        result["issued"] = fhir_instant(obs.issued)

    performers = [_fhir_reference_with_identifier_fallback(p, "reference") for p in (obs.performers or [])]
    performers = [p for p in performers if p]
    if performers:
        result["performer"] = performers

    _fhir_value_x(obs, result)

    data_absent_reason = fhir_observation_codeable_concept(obs.data_absent_reason_codings, obs.data_absent_reason_text)
    if data_absent_reason:
        result["dataAbsentReason"] = data_absent_reason

    interpretations = [fhir_observation_codeable_concept(i.codings, i.text) for i in (obs.interpretations or [])]
    interpretations = [i for i in interpretations if i]
    if interpretations:
        result["interpretation"] = interpretations

    notes = [fhir_observation_note(n) for n in (obs.notes or [])]
    notes = [n for n in notes if n]
    if notes:
        result["note"] = notes

    body_site = fhir_observation_codeable_concept(obs.body_site_codings, obs.body_site_text)
    if body_site:
        result["bodySite"] = body_site

    method = fhir_observation_codeable_concept(obs.method_codings, obs.method_text)
    if method:
        result["method"] = method

    specimen = _fhir_reference_with_identifier_fallback(obs, "specimen")
    if specimen:
        result["specimen"] = specimen

    device = _fhir_reference_with_identifier_fallback(obs, "device")
    if device:
        result["device"] = device

    reference_ranges = [_fhir_reference_range(rr) for rr in (obs.reference_ranges or [])]
    reference_ranges = [rr for rr in reference_ranges if rr]
    if reference_ranges:
        result["referenceRange"] = reference_ranges

    has_members = [_fhir_reference_with_identifier_fallback(h, "reference") for h in (obs.has_members or [])]
    has_members = [h for h in has_members if h]
    if has_members:
        result["hasMember"] = has_members

    derived_froms = [_fhir_reference_with_identifier_fallback(d, "reference") for d in (obs.derived_froms or [])]
    derived_froms = [d for d in derived_froms if d]
    if derived_froms:
        result["derivedFrom"] = derived_froms

    components = [fhir_observation_component(c) for c in (obs.components or [])]
    components = [c for c in components if c]
    if components:
        result["component"] = components

    return {k: v for k, v in result.items() if v is not None}
