from __future__ import annotations

from typing import TYPE_CHECKING

from app.fhir.datatypes import fhir_enum, fhir_instant

if TYPE_CHECKING:
    from app.models.document_reference import DocumentReferenceModel


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


def _fhir_ref(ref_raw: str | None, ref_type, ref_id: int | None, display: str | None) -> dict | None:
    result: dict = {}
    if ref_raw:
        result["reference"] = ref_raw
    elif ref_type and ref_id:
        result["reference"] = f"{fhir_enum(ref_type)}/{ref_id}"
    if display:
        result["display"] = display
    return result or None


def _fhir_reference_with_identifier_fallback(obj, prefix: str) -> dict | None:
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

    id_use = getattr(obj, f"{prefix}_identifier_use", None)
    id_system = getattr(obj, f"{prefix}_identifier_system", None)
    id_value = getattr(obj, f"{prefix}_identifier_value", None)
    id_type_text = getattr(obj, f"{prefix}_identifier_type_text", None)

    if id_use or id_system or id_value or id_type_text:
        identifier: dict = {}
        if id_use:
            identifier["use"] = fhir_enum(id_use)
        if id_system:
            identifier["system"] = id_system
        if id_value:
            identifier["value"] = id_value
        if id_type_text:
            identifier["type"] = {"text": id_type_text}
        entry["identifier"] = identifier

    return entry or None


def _fhir_identifier(i) -> dict | None:
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
    assigner = _fhir_reference_with_identifier_fallback(i, "assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def _fhir_master_identifier(model: DocumentReferenceModel) -> dict | None:
    has_any = (
        model.master_identifier_use
        or model.master_identifier_type_text
        or model.master_identifier_system
        or model.master_identifier_value
        or model.master_identifier_period_start
        or model.master_identifier_period_end
        or model.master_identifier_assigner_reference
        or model.master_identifier_assigner_type
        or model.master_identifier_assigner_id
        or getattr(model, "master_identifier_type_codings", None)
    )
    if not has_any:
        return None

    entry: dict = {}
    if model.master_identifier_use:
        entry["use"] = fhir_enum(model.master_identifier_use)
    type_cc = _fhir_codeable_concept(
        getattr(model, "master_identifier_type_codings", None),
        model.master_identifier_type_text,
    )
    if type_cc:
        entry["type"] = type_cc
    if model.master_identifier_system:
        entry["system"] = model.master_identifier_system
    if model.master_identifier_value:
        entry["value"] = model.master_identifier_value
    if model.master_identifier_period_start or model.master_identifier_period_end:
        period: dict = {}
        if model.master_identifier_period_start:
            period["start"] = fhir_instant(model.master_identifier_period_start)
        if model.master_identifier_period_end:
            period["end"] = fhir_instant(model.master_identifier_period_end)
        entry["period"] = period
    assigner = _fhir_reference_with_identifier_fallback(model, "master_identifier_assigner")
    if assigner:
        entry["assigner"] = assigner
    return entry or None


def _fhir_meta(model: DocumentReferenceModel) -> dict:
    meta: dict = {}
    if model.updated_at:
        meta["lastUpdated"] = fhir_instant(model.updated_at)
    extensions = []
    if model.created_at:
        extensions.append({
            "url": "http://hl7.org/fhir/StructureDefinition/resource-created",
            "valueDateTime": fhir_instant(model.created_at),
        })
    if model.created_by:
        extensions.append({
            "url": "http://hl7.org/fhir/StructureDefinition/resource-createdBy",
            "valueString": model.created_by,
        })
    if model.updated_by:
        extensions.append({
            "url": "http://hl7.org/fhir/StructureDefinition/resource-updatedBy",
            "valueString": model.updated_by,
        })
    if extensions:
        meta["extension"] = extensions
    return meta


def _fhir_content(c) -> dict:
    attachment: dict = {}
    if c.content_type:
        attachment["contentType"] = c.content_type
    if c.language:
        attachment["language"] = c.language
    if c.data:
        attachment["data"] = c.data
    if c.url:
        attachment["url"] = c.url
    if c.size is not None:
        attachment["size"] = c.size
    if c.hash:
        attachment["hash"] = c.hash
    if c.title:
        attachment["title"] = c.title
    if c.creation:
        attachment["creation"] = fhir_instant(c.creation)

    entry: dict = {"attachment": attachment}

    has_format = (
        c.format_system
        or c.format_version
        or c.format_code
        or c.format_display
        or c.format_user_selected is not None
    )
    if has_format:
        format_dict: dict = {}
        if c.format_system:
            format_dict["system"] = c.format_system
        if c.format_version:
            format_dict["version"] = c.format_version
        if c.format_code:
            format_dict["code"] = c.format_code
        if c.format_display:
            format_dict["display"] = c.format_display
        if c.format_user_selected is not None:
            format_dict["userSelected"] = c.format_user_selected
        entry["format"] = format_dict

    return entry


def _fhir_context(model: DocumentReferenceModel) -> dict | None:
    has_encounters = bool(getattr(model, "context_encounters", None))
    has_events = bool(getattr(model, "context_events", None))
    has_period = model.context_period_start or model.context_period_end
    has_facility = model.context_facility_type_text or bool(getattr(model, "context_facility_type_codings", None))
    has_practice = model.context_practice_setting_text or bool(getattr(model, "context_practice_setting_codings", None))
    has_patient_info = model.context_source_patient_info_reference or (
        model.context_source_patient_info_type and model.context_source_patient_info_id
    ) or model.context_source_patient_info_display
    has_related = bool(getattr(model, "context_related", None))

    if not (
        has_encounters
        or has_events
        or has_period
        or has_facility
        or has_practice
        or has_patient_info
        or has_related
    ):
        return None

    ctx: dict = {}
    if has_encounters:
        enc_list = []
        for e in model.context_encounters:
            ref = _fhir_ref(e.reference_reference, e.reference_type, e.reference_id, e.reference_display)
            if ref:
                enc_list.append(ref)
        if enc_list:
            ctx["encounter"] = enc_list

    if has_events:
        ev_list = []
        for ev in model.context_events:
            cc = _fhir_codeable_concept(getattr(ev, "codings", None), ev.text)
            if cc:
                ev_list.append(cc)
        if ev_list:
            ctx["event"] = ev_list

    if has_period:
        p: dict = {}
        if model.context_period_start:
            p["start"] = fhir_instant(model.context_period_start)
        if model.context_period_end:
            p["end"] = fhir_instant(model.context_period_end)
        ctx["period"] = p

    if has_facility:
        facility_cc = _fhir_codeable_concept(
            getattr(model, "context_facility_type_codings", None),
            model.context_facility_type_text,
        )
        if facility_cc:
            ctx["facilityType"] = facility_cc

    if has_practice:
        practice_cc = _fhir_codeable_concept(
            getattr(model, "context_practice_setting_codings", None),
            model.context_practice_setting_text,
        )
        if practice_cc:
            ctx["practiceSetting"] = practice_cc

    if has_patient_info:
        pat_ref = _fhir_ref(
            model.context_source_patient_info_reference,
            model.context_source_patient_info_type,
            model.context_source_patient_info_id,
            model.context_source_patient_info_display,
        )
        if pat_ref:
            ctx["sourcePatientInfo"] = pat_ref

    if has_related:
        rel_list = []
        for r in model.context_related:
            ref = _fhir_ref(r.reference_reference, r.reference_type, r.reference_id, r.reference_display)
            if ref:
                rel_list.append(ref)
        if rel_list:
            ctx["related"] = rel_list

    return ctx or None


def to_fhir_document_reference(model: DocumentReferenceModel) -> dict:
    """Map DocumentReferenceModel ORM instance to a FHIR R4 DocumentReference resource dict."""
    res: dict = {
        "resourceType": "DocumentReference",
        "id": str(model.document_reference_id),
    }

    meta = _fhir_meta(model)
    if meta:
        res["meta"] = meta

    if model.extension:
        res["extension"] = model.extension

    master_id = _fhir_master_identifier(model)
    if master_id:
        res["masterIdentifier"] = master_id

    if getattr(model, "identifiers", None):
        id_list = [_fhir_identifier(i) for i in model.identifiers]
        id_list = [i for i in id_list if i]
        if id_list:
            res["identifier"] = id_list

    res["status"] = fhir_enum(model.status)

    if model.doc_status:
        res["docStatus"] = fhir_enum(model.doc_status)

    type_cc = _fhir_codeable_concept(
        getattr(model, "type_codings", None), model.type_text
    )
    if type_cc:
        res["type"] = type_cc

    if getattr(model, "categories", None):
        cat_list = [
            _fhir_codeable_concept(getattr(c, "codings", None), c.text)
            for c in model.categories
        ]
        cat_list = [c for c in cat_list if c]
        if cat_list:
            res["category"] = cat_list

    subj = _fhir_ref(
        model.subject_reference,
        model.subject_type,
        model.subject_id,
        model.subject_display,
    )
    if subj:
        res["subject"] = subj

    if model.date:
        res["date"] = fhir_instant(model.date)

    if getattr(model, "authors", None):
        auth_list = [
            _fhir_ref(a.author_reference, a.author_type, a.author_id, a.author_display)
            for a in model.authors
        ]
        auth_list = [a for a in auth_list if a]
        if auth_list:
            res["author"] = auth_list

    auth = _fhir_ref(
        model.authenticator_reference,
        model.authenticator_type,
        model.authenticator_id,
        model.authenticator_display,
    )
    if auth:
        res["authenticator"] = auth

    cust = _fhir_ref(
        model.custodian_reference,
        model.custodian_type,
        model.custodian_id,
        model.custodian_display,
    )
    if cust:
        res["custodian"] = cust

    if getattr(model, "relates_to", None):
        rel_list = []
        for r in model.relates_to:
            tgt = _fhir_ref(
                r.target_reference,
                r.target_type,
                r.target_id,
                r.target_display,
            )
            if tgt:
                rel_list.append({
                    "code": fhir_enum(r.code),
                    "target": tgt,
                })
        if rel_list:
            res["relatesTo"] = rel_list

    if model.description:
        res["description"] = model.description

    if getattr(model, "security_labels", None):
        sec_list = [
            _fhir_codeable_concept(getattr(s, "codings", None), s.text)
            for s in model.security_labels
        ]
        sec_list = [s for s in sec_list if s]
        if sec_list:
            res["securityLabel"] = sec_list

    if getattr(model, "contents", None):
        res["content"] = [_fhir_content(c) for c in model.contents]

    ctx = _fhir_context(model)
    if ctx:
        res["context"] = ctx

    return {k: v for k, v in res.items() if v is not None}
