from typing import Any

from app.fhir.datatypes import (
    fhir_enum,
    fhir_instant,
)
from app.models.measure import MeasureModel


def _fhir_meta(model: MeasureModel) -> dict:
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


def _fhir_identifiers(identifiers) -> list[dict] | None:
    res = []
    for i in identifiers or []:
        d: dict[str, Any] = {}
        if i.use:
            d["use"] = fhir_enum(i.use)
        if i.type_codings or i.type_text:
            d["type"] = _fhir_codeable_concept(i.type_codings, i.type_text)
        if i.system:
            d["system"] = i.system
        if i.value:
            d["value"] = i.value
        per = _fhir_period(i.period_start, i.period_end)
        if per:
            d["period"] = per
        ass = _fhir_ref(i.assigner_reference, i.assigner_type, i.assigner_id, i.assigner_display)
        if ass:
            d["assigner"] = ass
        if d:
            res.append(d)
    return res or None


def _fhir_telecoms(telecoms) -> list[dict] | None:
    res = []
    for t in telecoms or []:
        d: dict[str, Any] = {}
        if t.system:
            d["system"] = fhir_enum(t.system)
        if t.value:
            d["value"] = t.value
        if t.use:
            d["use"] = fhir_enum(t.use)
        if t.rank is not None:
            d["rank"] = t.rank
        per = _fhir_period(t.period_start, t.period_end)
        if per:
            d["period"] = per
        if d:
            res.append(d)
    return res or None


def _fhir_contacts_by_role(contacts, role_name: str) -> list[dict] | None:
    res = []
    for c in contacts or []:
        r = c.role.value if hasattr(c.role, "value") else str(c.role)
        if r != role_name:
            continue
        d: dict[str, Any] = {}
        if c.name:
            d["name"] = c.name
        t = _fhir_telecoms(c.telecoms)
        if t:
            d["telecom"] = t
        if d:
            res.append(d)
    return res or None


def _fhir_use_contexts(use_contexts) -> list[dict] | None:
    res = []
    for uc in use_contexts or []:
        d: dict[str, Any] = {}
        code_d = _fhir_coding(uc)
        if code_d:
            d["code"] = code_d

        if uc.value_codings or uc.value_codeable_concept_text:
            d["valueCodeableConcept"] = _fhir_codeable_concept(
                uc.value_codings, uc.value_codeable_concept_text
            )
        elif uc.value_quantity_value is not None or uc.value_quantity_unit or uc.value_quantity_system or uc.value_quantity_code:
            vq: dict[str, Any] = {}
            if uc.value_quantity_value is not None:
                vq["value"] = float(uc.value_quantity_value)
            if uc.value_quantity_comparator:
                vq["comparator"] = fhir_enum(uc.value_quantity_comparator)
            if uc.value_quantity_unit:
                vq["unit"] = uc.value_quantity_unit
            if uc.value_quantity_system:
                vq["system"] = uc.value_quantity_system
            if uc.value_quantity_code:
                vq["code"] = uc.value_quantity_code
            d["valueQuantity"] = vq
        elif (
            uc.value_range_low_value is not None
            or uc.value_range_high_value is not None
        ):
            vr: dict[str, Any] = {}
            if uc.value_range_low_value is not None or uc.value_range_low_unit or uc.value_range_low_system or uc.value_range_low_code:
                low_q: dict[str, Any] = {}
                if uc.value_range_low_value is not None:
                    low_q["value"] = float(uc.value_range_low_value)
                if uc.value_range_low_unit:
                    low_q["unit"] = uc.value_range_low_unit
                if uc.value_range_low_system:
                    low_q["system"] = uc.value_range_low_system
                if uc.value_range_low_code:
                    low_q["code"] = uc.value_range_low_code
                vr["low"] = low_q
            if uc.value_range_high_value is not None or uc.value_range_high_unit or uc.value_range_high_system or uc.value_range_high_code:
                high_q: dict[str, Any] = {}
                if uc.value_range_high_value is not None:
                    high_q["value"] = float(uc.value_range_high_value)
                if uc.value_range_high_unit:
                    high_q["unit"] = uc.value_range_high_unit
                if uc.value_range_high_system:
                    high_q["system"] = uc.value_range_high_system
                if uc.value_range_high_code:
                    high_q["code"] = uc.value_range_high_code
                vr["high"] = high_q
            d["valueRange"] = vr
        elif uc.value_reference_reference or (uc.value_reference_type and uc.value_reference_id):
            ref = _fhir_ref(
                uc.value_reference_reference,
                uc.value_reference_type,
                uc.value_reference_id,
                uc.value_reference_display,
            )
            if ref:
                d["valueReference"] = ref

        if d:
            res.append(d)
    return res or None


def _fhir_concepts(items) -> list[dict] | None:
    res = []
    for item in items or []:
        cc = _fhir_codeable_concept(item.codings, item.text)
        if cc:
            res.append(cc)
    return res or None


def _fhir_related_artifacts(related_artifacts) -> list[dict] | None:
    res = []
    for ra in related_artifacts or []:
        d: dict[str, Any] = {
            "type": fhir_enum(ra.type),
        }
        if ra.label:
            d["label"] = ra.label
        if ra.display:
            d["display"] = ra.display
        if ra.citation:
            d["citation"] = ra.citation
        if ra.url:
            d["url"] = ra.url
        if ra.document:
            d["document"] = ra.document
        if ra.resource:
            d["resource"] = ra.resource
        res.append(d)
    return res or None


def _fhir_expression(desc, name, lang, expr, ref) -> dict | None:
    d: dict[str, Any] = {}
    if desc:
        d["description"] = desc
    if name:
        d["name"] = name
    if lang:
        d["language"] = lang
    if expr:
        d["expression"] = expr
    if ref:
        d["reference"] = ref
    return d or None


def _fhir_groups(groups) -> list[dict] | None:
    res = []
    for g in groups or []:
        gd: dict[str, Any] = {}
        if g.code_codings or g.code_text:
            gd["code"] = _fhir_codeable_concept(g.code_codings, g.code_text)
        if g.description:
            gd["description"] = g.description

        pops = []
        for p in g.populations or []:
            pd: dict[str, Any] = {}
            if p.code_codings or p.code_text:
                pd["code"] = _fhir_codeable_concept(p.code_codings, p.code_text)
            if p.description:
                pd["description"] = p.description
            crit = _fhir_expression(
                p.criteria_description, p.criteria_name, p.criteria_language,
                p.criteria_expression, p.criteria_reference
            )
            if crit:
                pd["criteria"] = crit
            if pd:
                pops.append(pd)
        if pops:
            gd["population"] = pops

        strats = []
        for s in g.stratifiers or []:
            sd: dict[str, Any] = {}
            if s.code_codings or s.code_text:
                sd["code"] = _fhir_codeable_concept(s.code_codings, s.code_text)
            if s.description:
                sd["description"] = s.description
            crit = _fhir_expression(
                s.criteria_description, s.criteria_name, s.criteria_language,
                s.criteria_expression, s.criteria_reference
            )
            if crit:
                sd["criteria"] = crit

            comps = []
            for c in s.components or []:
                cd: dict[str, Any] = {}
                if c.code_codings or c.code_text:
                    cd["code"] = _fhir_codeable_concept(c.code_codings, c.code_text)
                if c.description:
                    cd["description"] = c.description
                c_crit = _fhir_expression(
                    c.criteria_description, c.criteria_name, c.criteria_language,
                    c.criteria_expression, c.criteria_reference
                )
                if c_crit:
                    cd["criteria"] = c_crit
                if cd:
                    comps.append(cd)
            if comps:
                sd["component"] = comps
            if sd:
                strats.append(sd)
        if strats:
            gd["stratifier"] = strats
        if gd:
            res.append(gd)
    return res or None


def _fhir_supplemental_data(supplemental_data) -> list[dict] | None:
    res = []
    for sd in supplemental_data or []:
        d: dict[str, Any] = {}
        if sd.code_codings or sd.code_text:
            d["code"] = _fhir_codeable_concept(sd.code_codings, sd.code_text)
        if sd.usages:
            usages = [_fhir_codeable_concept(u.codings, u.text) for u in sd.usages]
            usages = [u for u in usages if u]
            if usages:
                d["usage"] = usages
        if sd.description:
            d["description"] = sd.description
        crit = _fhir_expression(
            sd.criteria_description, sd.criteria_name, sd.criteria_language,
            sd.criteria_expression, sd.criteria_reference
        )
        if crit:
            d["criteria"] = crit
        if d:
            res.append(d)
    return res or None


def to_fhir_measure(model: MeasureModel) -> dict[str, Any]:
    """Convert MeasureModel ORM instance to FHIR R4 Measure dict."""
    res: dict[str, Any] = {
        "resourceType": "Measure",
        "id": str(model.measure_id),
    }

    meta = _fhir_meta(model)
    if meta:
        res["meta"] = meta

    if model.extension:
        res["extension"] = list(model.extension)

    if model.url:
        res["url"] = model.url

    idents = _fhir_identifiers(model.identifiers)
    if idents:
        res["identifier"] = idents

    if model.version:
        res["version"] = model.version
    if model.name:
        res["name"] = model.name
    if model.title:
        res["title"] = model.title
    if model.subtitle:
        res["subtitle"] = model.subtitle

    res["status"] = fhir_enum(model.status)

    if model.experimental is not None:
        res["experimental"] = model.experimental

    # subject[x]
    if model.subject_codings or model.subject_codeable_concept_text:
        res["subjectCodeableConcept"] = _fhir_codeable_concept(
            model.subject_codings, model.subject_codeable_concept_text
        )
    elif model.subject_reference or (model.subject_type and model.subject_id):
        ref = _fhir_ref(
            model.subject_reference,
            model.subject_type,
            model.subject_id,
            model.subject_display,
        )
        if ref:
            res["subjectReference"] = ref

    if model.date:
        res["date"] = fhir_instant(model.date)
    if model.publisher:
        res["publisher"] = model.publisher

    contacts = _fhir_contacts_by_role(model.contacts, "contact")
    if contacts:
        res["contact"] = contacts

    if model.description:
        res["description"] = model.description

    ucs = _fhir_use_contexts(model.use_contexts)
    if ucs:
        res["useContext"] = ucs

    jurisdictions = _fhir_concepts(model.jurisdictions)
    if jurisdictions:
        res["jurisdiction"] = jurisdictions

    if model.purpose:
        res["purpose"] = model.purpose
    if model.usage:
        res["usage"] = model.usage
    if model.copyright:
        res["copyright"] = model.copyright
    if model.approval_date:
        res["approvalDate"] = model.approval_date.isoformat()
    if model.last_review_date:
        res["lastReviewDate"] = model.last_review_date.isoformat()

    period = _fhir_period(model.effective_period_start, model.effective_period_end)
    if period:
        res["effectivePeriod"] = period

    topics = _fhir_concepts(model.topics)
    if topics:
        res["topic"] = topics

    authors = _fhir_contacts_by_role(model.contacts, "author")
    if authors:
        res["author"] = authors
    editors = _fhir_contacts_by_role(model.contacts, "editor")
    if editors:
        res["editor"] = editors
    reviewers = _fhir_contacts_by_role(model.contacts, "reviewer")
    if reviewers:
        res["reviewer"] = reviewers
    endorsers = _fhir_contacts_by_role(model.contacts, "endorser")
    if endorsers:
        res["endorser"] = endorsers

    ras = _fhir_related_artifacts(model.related_artifacts)
    if ras:
        res["relatedArtifact"] = ras

    if model.library:
        res["library"] = list(model.library)
    if model.disclaimer:
        res["disclaimer"] = model.disclaimer

    if model.scoring_codings or model.scoring_text:
        res["scoring"] = _fhir_codeable_concept(
            model.scoring_codings, model.scoring_text
        )

    if model.composite_scoring_codings or model.composite_scoring_text:
        res["compositeScoring"] = _fhir_codeable_concept(
            model.composite_scoring_codings, model.composite_scoring_text
        )

    types = _fhir_concepts(model.types)
    if types:
        res["type"] = types

    if model.risk_adjustment:
        res["riskAdjustment"] = model.risk_adjustment
    if model.rate_aggregation:
        res["rateAggregation"] = model.rate_aggregation
    if model.rationale:
        res["rationale"] = model.rationale
    if model.clinical_recommendation_statement:
        res["clinicalRecommendationStatement"] = model.clinical_recommendation_statement

    if model.improvement_notation_codings or model.improvement_notation_text:
        res["improvementNotation"] = _fhir_codeable_concept(
            model.improvement_notation_codings, model.improvement_notation_text
        )

    if model.definition:
        res["definition"] = list(model.definition)
    if model.guidance:
        res["guidance"] = model.guidance

    groups = _fhir_groups(model.groups)
    if groups:
        res["group"] = groups

    supp_data = _fhir_supplemental_data(model.supplemental_data)
    if supp_data:
        res["supplementalData"] = supp_data

    return res
