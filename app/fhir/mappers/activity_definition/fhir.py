from typing import Any

from app.fhir.datatypes import (
    fhir_enum,
    fhir_instant,
)


def _fhir_meta(model) -> dict:
    meta: dict[str, Any] = {}
    if getattr(model, "updated_at", None):
        meta["lastUpdated"] = fhir_instant(model.updated_at)
    elif getattr(model, "created_at", None):
        meta["lastUpdated"] = fhir_instant(model.created_at)
    return meta


def _fhir_coding(c) -> dict | None:
    d: dict[str, Any] = {}
    if getattr(c, "system", None):
        d["system"] = c.system
    if getattr(c, "version", None):
        d["version"] = c.version
    if getattr(c, "code", None):
        d["code"] = c.code
    if getattr(c, "display", None):
        d["display"] = c.display
    if getattr(c, "user_selected", None) is not None:
        d["userSelected"] = c.user_selected
    return d or None


def _fhir_coding_from_fields(
    system: str | None,
    version: str | None,
    code: str | None,
    display: str | None,
    user_selected: bool | None,
) -> dict | None:
    d: dict[str, Any] = {}
    if system:
        d["system"] = system
    if version:
        d["version"] = version
    if code:
        d["code"] = code
    if display:
        d["display"] = display
    if user_selected is not None:
        d["userSelected"] = user_selected
    return d or None


def _fhir_codeable_concept(codings, text: str | None) -> dict | None:
    cc: dict[str, Any] = {}
    if codings:
        cds = [_fhir_coding(c) for c in codings]
        cds = [c for c in cds if c]
        if cds:
            cc["coding"] = cds
    if text:
        cc["text"] = text
    return cc or None


def _fhir_ref(reference, ref_type, ref_id, display) -> dict | None:
    entry: dict[str, Any] = {}
    if reference:
        entry["reference"] = reference
    elif ref_type and ref_id:
        entry["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        entry["display"] = display
    return entry or None


def _fhir_period(start, end) -> dict | None:
    p: dict[str, Any] = {}
    if start:
        p["start"] = fhir_instant(start)
    if end:
        p["end"] = fhir_instant(end)
    return p or None


def _fhir_quantity(obj, prefix: str) -> dict | None:
    val = getattr(obj, f"{prefix}_value", None)
    unit = getattr(obj, f"{prefix}_unit", None)
    system = getattr(obj, f"{prefix}_system", None)
    code = getattr(obj, f"{prefix}_code", None)
    q: dict[str, Any] = {}
    if val is not None:
        q["value"] = float(val)
    if unit:
        q["unit"] = unit
    if system:
        q["system"] = system
    if code:
        q["code"] = code
    return q or None


def _fhir_quantity_with_comparator(obj, prefix: str) -> dict | None:
    q = _fhir_quantity(obj, prefix)
    comparator = getattr(obj, f"{prefix}_comparator", None)
    if q and comparator:
        q["comparator"] = fhir_enum(comparator)
    return q


def _fhir_range(obj, prefix: str) -> dict | None:
    low = _fhir_quantity(obj, f"{prefix}_low")
    high = _fhir_quantity(obj, f"{prefix}_high")
    r: dict[str, Any] = {}
    if low:
        r["low"] = low
    if high:
        r["high"] = high
    return r or None


def _fhir_identifiers(identifiers) -> list[dict]:
    result = []
    for i in identifiers:
        ident: dict[str, Any] = {}
        if i.use:
            ident["use"] = fhir_enum(i.use)
        if i.type_text or i.type_codings:
            t = _fhir_codeable_concept(i.type_codings, i.type_text)
            if t:
                ident["type"] = t
        if i.system:
            ident["system"] = i.system
        if i.value:
            ident["value"] = i.value
        p = _fhir_period(i.period_start, i.period_end)
        if p:
            ident["period"] = p
        assigner = _fhir_ref(
            i.assigner_reference, i.assigner_type, i.assigner_id, i.assigner_display
        )
        if assigner:
            ident["assigner"] = assigner
        if ident:
            result.append(ident)
    return result


def _fhir_contacts(contacts, role: str) -> list[dict]:
    result = []
    for c in contacts:
        if c.role and fhir_enum(c.role) == role:
            entry: dict[str, Any] = {}
            if c.name:
                entry["name"] = c.name
            if c.telecoms:
                telecoms = []
                for t in c.telecoms:
                    tel: dict[str, Any] = {}
                    if t.system:
                        tel["system"] = fhir_enum(t.system)
                    if t.value:
                        tel["value"] = t.value
                    if t.use:
                        tel["use"] = fhir_enum(t.use)
                    if t.rank is not None:
                        tel["rank"] = t.rank
                    p = _fhir_period(t.period_start, t.period_end)
                    if p:
                        tel["period"] = p
                    if tel:
                        telecoms.append(tel)
                if telecoms:
                    entry["telecom"] = telecoms
            if entry:
                result.append(entry)
    return result


def _fhir_use_contexts(use_contexts) -> list[dict]:
    result = []
    for uc in use_contexts:
        entry: dict[str, Any] = {}
        code = _fhir_coding_from_fields(
            uc.system,
            uc.version,
            uc.code,
            uc.display,
            uc.user_selected,
        )
        if code:
            entry["code"] = code
        vcc = _fhir_codeable_concept(uc.value_codings, uc.value_codeable_concept_text)
        if vcc:
            entry["valueCodeableConcept"] = vcc
        vq = _fhir_quantity_with_comparator(uc, "value_quantity")
        if vq:
            entry["valueQuantity"] = vq
        vr = _fhir_range(uc, "value_range")
        if vr:
            entry["valueRange"] = vr
        vref = _fhir_ref(
            uc.value_reference_reference,
            uc.value_reference_type,
            uc.value_reference_id,
            uc.value_reference_display,
        )
        if vref:
            entry["valueReference"] = vref
        if entry:
            result.append(entry)
    return result


def _fhir_related_artifacts(artifacts) -> list[dict]:
    result = []
    for ra in artifacts:
        entry: dict[str, Any] = {}
        if ra.type:
            entry["type"] = fhir_enum(ra.type)
        if ra.label:
            entry["label"] = ra.label
        if ra.display:
            entry["display"] = ra.display
        if ra.citation:
            entry["citation"] = ra.citation
        if ra.url:
            entry["url"] = ra.url
        if ra.document:
            entry["document"] = ra.document
        if ra.resource:
            entry["resource"] = ra.resource
        if entry:
            result.append(entry)
    return result


def _fhir_participants(participants) -> list[dict]:
    result = []
    for p in participants:
        entry: dict[str, Any] = {}
        if p.type:
            entry["type"] = fhir_enum(p.type)
        role = _fhir_codeable_concept(p.role_codings, p.role_text)
        if role:
            entry["role"] = role
        if entry:
            result.append(entry)
    return result


def _fhir_dosages(dosages) -> list[dict]:
    result = []
    for d in dosages:
        entry: dict[str, Any] = {}
        if d.sequence is not None:
            entry["sequence"] = d.sequence
        if d.text:
            entry["text"] = d.text
        if d.patient_instruction:
            entry["patientInstruction"] = d.patient_instruction
        if d.timing:
            entry["timing"] = d.timing
        if d.as_needed_boolean is not None:
            entry["asNeededBoolean"] = d.as_needed_boolean
        an_cc = _fhir_codeable_concept(
            d.as_needed_codings, d.as_needed_codeable_concept_text
        )
        if an_cc:
            entry["asNeededCodeableConcept"] = an_cc
        site = _fhir_codeable_concept(d.site_codings, d.site_text)
        if site:
            entry["site"] = site
        route = _fhir_codeable_concept(d.route_codings, d.route_text)
        if route:
            entry["route"] = route
        method = _fhir_codeable_concept(d.method_codings, d.method_text)
        if method:
            entry["method"] = method
        if d.dose_and_rate:
            entry["doseAndRate"] = d.dose_and_rate
        if d.max_dose_per_period:
            entry["maxDosePerPeriod"] = d.max_dose_per_period
        max_admin = _fhir_quantity(d, "max_dose_per_administration")
        if max_admin:
            entry["maxDosePerAdministration"] = max_admin
        max_life = _fhir_quantity(d, "max_dose_per_lifetime")
        if max_life:
            entry["maxDosePerLifetime"] = max_life
        if entry:
            result.append(entry)
    return result


def _fhir_dynamic_values(dynamic_values) -> list[dict]:
    result = []
    for dv in dynamic_values:
        entry: dict[str, Any] = {}
        if dv.path:
            entry["path"] = dv.path
        expr: dict[str, Any] = {}
        if dv.expression_description:
            expr["description"] = dv.expression_description
        if dv.expression_name:
            expr["name"] = dv.expression_name
        if dv.expression_language:
            expr["language"] = dv.expression_language
        if dv.expression_expression:
            expr["expression"] = dv.expression_expression
        if dv.expression_reference:
            expr["reference"] = dv.expression_reference
        if expr:
            entry["expression"] = expr
        if entry:
            result.append(entry)
    return result


def to_fhir_activity_definition(model) -> dict:
    """Transform an ActivityDefinitionModel into a FHIR R4 camelCase dict."""
    fhir: dict[str, Any] = {
        "resourceType": "ActivityDefinition",
        "id": str(model.activity_definition_id),
    }

    meta = _fhir_meta(model)
    if meta:
        fhir["meta"] = meta

    if model.url:
        fhir["url"] = model.url

    if model.identifiers:
        idents = _fhir_identifiers(model.identifiers)
        if idents:
            fhir["identifier"] = idents

    if model.version:
        fhir["version"] = model.version

    if model.name:
        fhir["name"] = model.name

    if model.title:
        fhir["title"] = model.title

    if model.subtitle:
        fhir["subtitle"] = model.subtitle

    # status is required (1..1)
    if model.status:
        fhir["status"] = fhir_enum(model.status)

    if model.experimental is not None:
        fhir["experimental"] = model.experimental

    if model.date:
        fhir["date"] = fhir_instant(model.date)

    if model.publisher:
        fhir["publisher"] = model.publisher

    if model.contacts:
        contacts = _fhir_contacts(model.contacts, "contact")
        if contacts:
            fhir["contact"] = contacts
        authors = _fhir_contacts(model.contacts, "author")
        if authors:
            fhir["author"] = authors
        editors = _fhir_contacts(model.contacts, "editor")
        if editors:
            fhir["editor"] = editors
        reviewers = _fhir_contacts(model.contacts, "reviewer")
        if reviewers:
            fhir["reviewer"] = reviewers
        endorsers = _fhir_contacts(model.contacts, "endorser")
        if endorsers:
            fhir["endorser"] = endorsers

    if model.description:
        fhir["description"] = model.description

    if model.use_contexts:
        ucs = _fhir_use_contexts(model.use_contexts)
        if ucs:
            fhir["useContext"] = ucs

    if model.jurisdictions:
        juris = [_fhir_codeable_concept(j.codings, j.text) for j in model.jurisdictions]
        juris = [j for j in juris if j]
        if juris:
            fhir["jurisdiction"] = juris

    if model.purpose:
        fhir["purpose"] = model.purpose

    if model.usage:
        fhir["usage"] = model.usage

    if model.copyright:
        fhir["copyright"] = model.copyright

    if model.approval_date:
        fhir["approvalDate"] = model.approval_date.isoformat()

    if model.last_review_date:
        fhir["lastReviewDate"] = model.last_review_date.isoformat()

    effective_period = _fhir_period(model.effective_period_start, model.effective_period_end)
    if effective_period:
        fhir["effectivePeriod"] = effective_period

    if model.topics:
        topics = [_fhir_codeable_concept(t.codings, t.text) for t in model.topics]
        topics = [t for t in topics if t]
        if topics:
            fhir["topic"] = topics

    if model.related_artifacts:
        ras = _fhir_related_artifacts(model.related_artifacts)
        if ras:
            fhir["relatedArtifact"] = ras

    if model.library:
        fhir["library"] = model.library

    if model.kind:
        fhir["kind"] = fhir_enum(model.kind)

    if model.profile:
        fhir["profile"] = model.profile

    code = _fhir_codeable_concept(model.code_codings, model.code_text)
    if code:
        fhir["code"] = code

    if model.intent:
        fhir["intent"] = fhir_enum(model.intent)

    if model.priority:
        fhir["priority"] = fhir_enum(model.priority)

    if model.do_not_perform is not None:
        fhir["doNotPerform"] = model.do_not_perform

    # timing[x]
    if model.timing_timing:
        fhir["timingTiming"] = model.timing_timing
    elif model.timing_date_time:
        fhir["timingDateTime"] = fhir_instant(model.timing_date_time)
    else:
        timing_age = _fhir_quantity(model, "timing_age")
        if timing_age:
            fhir["timingAge"] = timing_age
        else:
            timing_period = _fhir_period(model.timing_period_start, model.timing_period_end)
            if timing_period:
                fhir["timingPeriod"] = timing_period
            else:
                timing_range = _fhir_range(model, "timing_range")
                if timing_range:
                    fhir["timingRange"] = timing_range
                else:
                    timing_duration = _fhir_quantity(model, "timing_duration")
                    if timing_duration:
                        fhir["timingDuration"] = timing_duration

    location = _fhir_ref(
        model.location_reference,
        model.location_type,
        model.location_id,
        model.location_display,
    )
    if location:
        fhir["location"] = location

    if model.participants:
        participants = _fhir_participants(model.participants)
        if participants:
            fhir["participant"] = participants

    # product[x]
    product_cc = _fhir_codeable_concept(
        model.product_codings, model.product_codeable_concept_text
    )
    if product_cc:
        fhir["productCodeableConcept"] = product_cc
    else:
        product_ref = _fhir_ref(
            model.product_reference,
            model.product_type,
            model.product_id,
            model.product_display,
        )
        if product_ref:
            fhir["productReference"] = product_ref

    quantity = _fhir_quantity_with_comparator(model, "quantity")
    if quantity:
        fhir["quantity"] = quantity

    if model.dosages:
        dosages = _fhir_dosages(model.dosages)
        if dosages:
            fhir["dosage"] = dosages

    if model.body_sites:
        body_sites = [_fhir_codeable_concept(b.codings, b.text) for b in model.body_sites]
        body_sites = [b for b in body_sites if b]
        if body_sites:
            fhir["bodySite"] = body_sites

    if model.specimen_requirements:
        srs = [
            _fhir_ref(
                sr.reference_reference,
                sr.reference_type,
                sr.reference_id,
                sr.reference_display,
            )
            for sr in model.specimen_requirements
        ]
        srs = [s for s in srs if s]
        if srs:
            fhir["specimenRequirement"] = srs

    if model.observation_requirements:
        orqs = [
            _fhir_ref(
                orq.reference_reference,
                orq.reference_type,
                orq.reference_id,
                orq.reference_display,
            )
            for orq in model.observation_requirements
        ]
        orqs = [o for o in orqs if o]
        if orqs:
            fhir["observationRequirement"] = orqs

    if model.observation_result_requirements:
        orrs = [
            _fhir_ref(
                orr.reference_reference,
                orr.reference_type,
                orr.reference_id,
                orr.reference_display,
            )
            for orr in model.observation_result_requirements
        ]
        orrs = [o for o in orrs if o]
        if orrs:
            fhir["observationResultRequirement"] = orrs

    if model.transform:
        fhir["transform"] = model.transform

    if model.dynamic_values:
        dvs = _fhir_dynamic_values(model.dynamic_values)
        if dvs:
            fhir["dynamicValue"] = dvs

    # subject[x]
    subject_cc = _fhir_codeable_concept(
        model.subject_codings, model.subject_codeable_concept_text
    )
    if subject_cc:
        fhir["subjectCodeableConcept"] = subject_cc
    else:
        subject_ref = _fhir_ref(
            model.subject_reference,
            model.subject_type,
            model.subject_id,
            model.subject_display,
        )
        if subject_ref:
            fhir["subjectReference"] = subject_ref

    if model.extension:
        fhir["extension"] = model.extension

    return {k: v for k, v in fhir.items() if v is not None}
