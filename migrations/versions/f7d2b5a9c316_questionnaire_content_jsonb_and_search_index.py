"""questionnaire: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: f7d2b5a9c316
Revises: e6c1a4f8b215
Create Date: 2026-12-19 10:00:00.000000

Stores Questionnaire whole in `content` (see QuestionnaireModel's docstring), like the other
resources already moved (QuestionnaireResponse e6c1a4f8b215, DocumentReference d5b9e2f7a103,
...). The whole FHIR resource - including the nested `item` tree with its enableWhen /
answerOption / initial entries, `contact`, `useContext`, `jurisdiction` and `code` - moves into
`questionnaire.content`; every column/table that survives is a search index for one of the FHIR
R4 Questionnaire search parameters (or `_id` / `_lastUpdated`), derived from `content`:

  questionnaire: status (the enum already held the true FHIR codes, so it stays), subject_type
      (new: an array of the enum `questionnaire_subject_type`, the required-binding resource
      types), url, version,
      name / title / description / publisher (each plus a `*_norm` twin), date_start/_end (new:
      the range the dateTime covers; the old `date` instant is dropped) and
      effective_start/_end (new: the half-open range of effectivePeriod); the public id gets its
      sequence as a server default; new: content.
  questionnaire_identifier: rebuilt as an index table (one row per identifier x type coding)
  questionnaire_token: new - jurisdiction, code (item.code at every depth),
      context-type and context (the latter two carry the useContext's slot)
  questionnaire_definition: new - one row per item.definition at every depth
  questionnaire_context_quantity: new - one row per useContext whose value is a Quantity / Range
  dropped: the item tree tables and the contact, useContext, jurisdiction, code and identifier
      type-coding tables (all of it now lives in `content`), every main-table column with no
      search parameter (derivedFrom, experimental, subjectType, purpose, copyright, approvalDate,
      lastReviewDate, extension, date, effectivePeriod) and the per-field `questionnaire_*`
      enums (item type, enable behaviour, operator, quantity comparator, useContext reference
      type).

upgrade: (1) builds `content` for every existing row from the old columns and tables - a frozen
copy of the old to_fhir_questionnaire() logic, including rebuilding the nested item tree from
the flat tables (but keeping a reference's raw string, so an absolute URL is not lost), so this
migration never depends on application code that has since changed; (2) drops the old child
tables/columns and creates the index tables; (3) rebuilds the index from `content`.

downgrade: not supported. Everything the old schema held is preserved in `content`, but
rebuilding the old normalized tables from it is not implemented - restore from a backup taken
before upgrading.
"""

import json
import re
import unicodedata
from datetime import UTC, date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "f7d2b5a9c316"
down_revision: Union[str, None] = "e6c1a4f8b215"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

P = "questionnaire"

_STATUS = ("draft", "active", "retired", "unknown")
_COMPARATOR = {"lt": "<", "le": "<=", "ge": ">=", "gt": ">"}
_OPERATOR = {
    "exists": "exists",
    "eq": "=",
    "ne": "!=",
    "gt": ">",
    "lt": "<",
    "ge": ">=",
    "le": "<=",
}
# The 148 R4 resource types (HL7's `resource-types` code system): Questionnaire.subjectType's
# required binding, held as the enum `questionnaire_subject_type`.
_SUBJECT_TYPES = (
    "Account",
    "ActivityDefinition",
    "AdverseEvent",
    "AllergyIntolerance",
    "Appointment",
    "AppointmentResponse",
    "AuditEvent",
    "Basic",
    "Binary",
    "BiologicallyDerivedProduct",
    "BodyStructure",
    "Bundle",
    "CapabilityStatement",
    "CarePlan",
    "CareTeam",
    "CatalogEntry",
    "ChargeItem",
    "ChargeItemDefinition",
    "Claim",
    "ClaimResponse",
    "ClinicalImpression",
    "CodeSystem",
    "Communication",
    "CommunicationRequest",
    "CompartmentDefinition",
    "Composition",
    "ConceptMap",
    "Condition",
    "Consent",
    "Contract",
    "Coverage",
    "CoverageEligibilityRequest",
    "CoverageEligibilityResponse",
    "DetectedIssue",
    "Device",
    "DeviceDefinition",
    "DeviceMetric",
    "DeviceRequest",
    "DeviceUseStatement",
    "DiagnosticReport",
    "DocumentManifest",
    "DocumentReference",
    "DomainResource",
    "EffectEvidenceSynthesis",
    "Encounter",
    "Endpoint",
    "EnrollmentRequest",
    "EnrollmentResponse",
    "EpisodeOfCare",
    "EventDefinition",
    "Evidence",
    "EvidenceVariable",
    "ExampleScenario",
    "ExplanationOfBenefit",
    "FamilyMemberHistory",
    "Flag",
    "Goal",
    "GraphDefinition",
    "Group",
    "GuidanceResponse",
    "HealthcareService",
    "ImagingStudy",
    "Immunization",
    "ImmunizationEvaluation",
    "ImmunizationRecommendation",
    "ImplementationGuide",
    "InsurancePlan",
    "Invoice",
    "Library",
    "Linkage",
    "List",
    "Location",
    "Measure",
    "MeasureReport",
    "Media",
    "Medication",
    "MedicationAdministration",
    "MedicationDispense",
    "MedicationKnowledge",
    "MedicationRequest",
    "MedicationStatement",
    "MedicinalProduct",
    "MedicinalProductAuthorization",
    "MedicinalProductContraindication",
    "MedicinalProductIndication",
    "MedicinalProductIngredient",
    "MedicinalProductInteraction",
    "MedicinalProductManufactured",
    "MedicinalProductPackaged",
    "MedicinalProductPharmaceutical",
    "MedicinalProductUndesirableEffect",
    "MessageDefinition",
    "MessageHeader",
    "MolecularSequence",
    "NamingSystem",
    "NutritionOrder",
    "Observation",
    "ObservationDefinition",
    "OperationDefinition",
    "OperationOutcome",
    "Organization",
    "OrganizationAffiliation",
    "Parameters",
    "Patient",
    "PaymentNotice",
    "PaymentReconciliation",
    "Person",
    "PlanDefinition",
    "Practitioner",
    "PractitionerRole",
    "Procedure",
    "Provenance",
    "Questionnaire",
    "QuestionnaireResponse",
    "RelatedPerson",
    "RequestGroup",
    "ResearchDefinition",
    "ResearchElementDefinition",
    "ResearchStudy",
    "ResearchSubject",
    "Resource",
    "RiskAssessment",
    "RiskEvidenceSynthesis",
    "Schedule",
    "SearchParameter",
    "ServiceRequest",
    "Slot",
    "Specimen",
    "SpecimenDefinition",
    "StructureDefinition",
    "StructureMap",
    "Subscription",
    "Substance",
    "SubstanceNucleicAcid",
    "SubstancePolymer",
    "SubstanceProtein",
    "SubstanceReferenceInformation",
    "SubstanceSourceMaterial",
    "SubstanceSpecification",
    "SupplyDelivery",
    "SupplyRequest",
    "Task",
    "TerminologyCapabilities",
    "TestReport",
    "TestScript",
    "ValueSet",
    "VerificationResult",
    "VisionPrescription",
)


# -- shared helpers (frozen - never import application code here) ---------------------------


def _prune(value):
    if isinstance(value, dict):
        out = {k: _prune(v) for k, v in value.items()}
        return {k: v for k, v in out.items() if v is not None and v != [] and v != {}}
    if isinstance(value, list):
        out = [_prune(v) for v in value]
        return [v for v in out if v is not None and v != [] and v != {}]
    return value


def _iso(value):
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    return value


def _period(start, end):
    return {"start": _iso(start), "end": _iso(end)}


def _json(value):
    """A raw text() query can hand JSONB back as a string."""
    return json.loads(value) if isinstance(value, str) else value


def _rows(bind, sql, **params):
    return bind.execute(sa.text(sql), params).mappings().all()


def _norm(text):
    """Frozen copy of app.fhir.search.values.normalize."""
    if text is None:
        return None
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def _num(value):
    return float(value) if isinstance(value, Decimal) else value


_DATE_RE = re.compile(
    r"^(?P<y>\d{4})(?:-(?P<m>\d{2})(?:-(?P<d>\d{2})(?:T(?P<H>\d{2}):(?P<M>\d{2})"
    r"(?::(?P<S>\d{2})(?P<f>\.\d+)?)?(?P<tz>Z|[+-]\d{2}:\d{2})?)?)?)?$"
)


def _bounds(value):
    """(start, end) instants of a FHIR date/dateTime at its written precision - the half-open
    range it covers (frozen copy of app.fhir.search.values.parse_date). (None, None) if absent
    or unparseable."""
    if not value:
        return None, None
    g = _DATE_RE.match(str(value))
    if not g:
        return None, None
    g = g.groupdict()
    tz = UTC
    if g["tz"] and g["tz"] != "Z":
        sign = 1 if g["tz"][0] == "+" else -1
        tz = timezone(
            sign * timedelta(hours=int(g["tz"][1:3]), minutes=int(g["tz"][4:6]))
        )
    try:
        low = datetime(
            int(g["y"]),
            int(g["m"] or 1),
            int(g["d"] or 1),
            int(g["H"] or 0),
            int(g["M"] or 0),
            int(g["S"] or 0),
            int(((g["f"] or ".0")[1:] + "000000")[:6]),
            tzinfo=tz,
        )
    except ValueError:
        return None, None
    if g["f"]:
        high = low + timedelta(microseconds=1)
    elif g["S"]:
        high = low + timedelta(seconds=1)
    elif g["M"]:
        high = low + timedelta(minutes=1)
    elif g["d"]:
        high = low + timedelta(days=1)
    elif g["m"]:
        high = low.replace(year=low.year + (low.month // 12), month=low.month % 12 + 1)
    else:
        high = low.replace(year=low.year + 1)
    return low.astimezone(UTC), high.astimezone(UTC)


# -- upgrade: old columns/tables -> content (frozen copy of the old mapper) -----------------

_TYPE_NAMES = {
    t.upper(): t
    for t in (
        "Organization",
        "PlanDefinition",
        "ResearchStudy",
        "InsurancePlan",
        "HealthcareService",
        "Group",
        "Location",
    )
}


def _coding(row, prefix=""):
    """A Coding from the (optionally prefixed) FhirCodingMixin columns."""
    return {
        "system": row[f"{prefix}system"],
        "version": row[f"{prefix}version"],
        "code": row[f"{prefix}code"],
        "display": row[f"{prefix}display"],
        "userSelected": row[f"{prefix}user_selected"],
    }


def _fallback_identifier(row, prefix):
    """The logical identifier of a Reference. Every column is read tolerantly."""
    g = row.get
    return {
        "use": g(f"{prefix}_use"),
        "type": {
            "coding": [
                {
                    "system": g(f"{prefix}_type_system"),
                    "version": g(f"{prefix}_type_version"),
                    "code": g(f"{prefix}_type_code"),
                    "display": g(f"{prefix}_type_display"),
                    "userSelected": g(f"{prefix}_type_user_selected"),
                }
            ],
            "text": g(f"{prefix}_type_text"),
        },
        "system": g(f"{prefix}_system"),
        "value": g(f"{prefix}_value"),
        "period": _period(g(f"{prefix}_period_start"), g(f"{prefix}_period_end")),
    }


def _ref(row, prefix):
    """A Reference from the old `{prefix}_reference/_type/_id/_display/_identifier_*` columns."""
    raw = row.get(f"{prefix}_reference")
    if not raw and row.get(f"{prefix}_type") and row.get(f"{prefix}_id"):
        ref_type = str(row[f"{prefix}_type"])
        raw = f"{_TYPE_NAMES.get(ref_type.upper(), ref_type)}/{row[f'{prefix}_id']}"
    return {
        "reference": raw,
        "display": row.get(f"{prefix}_display"),
        "identifier": _fallback_identifier(row, f"{prefix}_identifier"),
    }


def _has_ref(row, prefix):
    return bool(
        row.get(f"{prefix}_reference")
        or (row.get(f"{prefix}_type") and row.get(f"{prefix}_id"))
    )


def _rows_of(bind, table, fk, value):
    return _rows(bind, f"SELECT * FROM {table} WHERE {fk} = :v ORDER BY id", v=value)


def _quantity(row, prefix, comparator_key=None):
    return {
        "value": _num(row[f"{prefix}_value"]),
        "comparator": _COMPARATOR.get(row[comparator_key], row[comparator_key])
        if comparator_key and row[comparator_key]
        else None,
        "unit": row[f"{prefix}_unit"],
        "system": row[f"{prefix}_system"],
        "code": row[f"{prefix}_code"],
    }


def _has_quantity(row, prefix):
    return (
        row[f"{prefix}_value"] is not None
        or row[f"{prefix}_unit"]
        or row[f"{prefix}_system"]
        or row[f"{prefix}_code"]
    )


def _identifiers(bind, pk):
    out = []
    for i in _rows(
        bind,
        f'SELECT *, "use"::text AS use_text FROM {P}_identifier WHERE {P}_pk = :v ORDER BY id',
        v=pk,
    ):
        out.append(
            {
                "use": i["use_text"],
                "type": {
                    "coding": [
                        _coding(c)
                        for c in _rows_of(
                            bind,
                            f"{P}_identifier_type_coding",
                            f"{P}_identifier_id",
                            i["id"],
                        )
                    ],
                    "text": i["type_text"],
                },
                "system": i["system"],
                "value": i["value"],
                "period": _period(i["period_start"], i["period_end"]),
                "assigner": _ref(i, "assigner"),
            }
        )
    return out


def _contacts(bind, pk):
    out = []
    for c in _rows_of(bind, f"{P}_contact", f"{P}_pk", pk):
        telecom = []
        for t in _rows(
            bind,
            f'SELECT *, system::text AS system_text, "use"::text AS use_text '
            f"FROM {P}_contact_telecom WHERE {P}_contact_id = :v ORDER BY id",
            v=c["id"],
        ):
            telecom.append(
                {
                    "system": t["system_text"],
                    "value": t["value"],
                    "use": t["use_text"],
                    "rank": t["rank"],
                    "period": _period(t["period_start"], t["period_end"]),
                }
            )
        out.append({"name": c["name"], "telecom": telecom})
    return out


def _use_contexts(bind, pk):
    out = []
    for uc in _rows(
        bind,
        f"SELECT *, value_quantity_comparator::text AS comparator_text "
        f"FROM {P}_use_context WHERE {P}_pk = :v ORDER BY id",
        v=pk,
    ):
        entry = {"code": _coding(uc)}
        codings = _rows_of(
            bind, f"{P}_use_context_value_coding", f"{P}_use_context_id", uc["id"]
        )
        if uc["value_codeable_concept_text"] or codings:
            entry["valueCodeableConcept"] = {
                "coding": [_coding(c) for c in codings],
                "text": uc["value_codeable_concept_text"],
            }
        elif _has_quantity(uc, "value_quantity"):
            entry["valueQuantity"] = _quantity(uc, "value_quantity", "comparator_text")
        elif (
            uc["value_range_low_value"] is not None
            or uc["value_range_high_value"] is not None
        ):
            entry["valueRange"] = {
                "low": _quantity(uc, "value_range_low"),
                "high": _quantity(uc, "value_range_high"),
            }
        elif _has_ref(uc, "value_reference"):
            entry["valueReference"] = _ref(uc, "value_reference")
        out.append(entry)
    return out


def _jurisdictions(bind, pk):
    out = []
    for j in _rows_of(bind, f"{P}_jurisdiction", f"{P}_pk", pk):
        out.append(
            {
                "coding": [
                    _coding(c)
                    for c in _rows_of(
                        bind,
                        f"{P}_jurisdiction_coding",
                        f"{P}_jurisdiction_id",
                        j["id"],
                    )
                ],
                "text": j["text"],
            }
        )
    return out


def _enable_when(ew):
    entry = {
        "question": ew["question"],
        "operator": _OPERATOR.get(ew["operator_text"], ew["operator_text"]),
    }
    if ew["answer_boolean"] is not None:
        entry["answerBoolean"] = ew["answer_boolean"]
    elif ew["answer_decimal"] is not None:
        entry["answerDecimal"] = _num(ew["answer_decimal"])
    elif ew["answer_integer"] is not None:
        entry["answerInteger"] = ew["answer_integer"]
    elif ew["answer_date"] is not None:
        entry["answerDate"] = _iso(ew["answer_date"])
    elif ew["answer_date_time"] is not None:
        entry["answerDateTime"] = _iso(ew["answer_date_time"])
    elif ew["answer_time"] is not None:
        entry["answerTime"] = _iso(ew["answer_time"])
    elif ew["answer_string"] is not None:
        entry["answerString"] = ew["answer_string"]
    elif ew["answer_coding_system"] or ew["answer_coding_code"]:
        entry["answerCoding"] = _coding(ew, "answer_coding_")
    elif _has_quantity(ew, "answer_quantity"):
        entry["answerQuantity"] = _quantity(ew, "answer_quantity", "qc_text")
    elif _has_ref(ew, "answer_reference"):
        entry["answerReference"] = _ref(ew, "answer_reference")
    return entry


def _answer_option(ao):
    entry = {}
    if ao["value_integer"] is not None:
        entry["valueInteger"] = ao["value_integer"]
    elif ao["value_date"] is not None:
        entry["valueDate"] = _iso(ao["value_date"])
    elif ao["value_time"] is not None:
        entry["valueTime"] = _iso(ao["value_time"])
    elif ao["value_string"] is not None:
        entry["valueString"] = ao["value_string"]
    elif ao["value_coding_system"] or ao["value_coding_code"]:
        entry["valueCoding"] = _coding(ao, "value_coding_")
    elif _has_ref(ao, "value_reference"):
        entry["valueReference"] = _ref(ao, "value_reference")
    if ao["initial_selected"] is not None:
        entry["initialSelected"] = ao["initial_selected"]
    return entry


def _initial(ini):
    entry = {}
    if ini["value_boolean"] is not None:
        entry["valueBoolean"] = ini["value_boolean"]
    elif ini["value_decimal"] is not None:
        entry["valueDecimal"] = _num(ini["value_decimal"])
    elif ini["value_integer"] is not None:
        entry["valueInteger"] = ini["value_integer"]
    elif ini["value_date"] is not None:
        entry["valueDate"] = _iso(ini["value_date"])
    elif ini["value_date_time"] is not None:
        entry["valueDateTime"] = _iso(ini["value_date_time"])
    elif ini["value_time"] is not None:
        entry["valueTime"] = _iso(ini["value_time"])
    elif ini["value_string"] is not None:
        entry["valueString"] = ini["value_string"]
    elif ini["value_uri"] is not None:
        entry["valueUri"] = ini["value_uri"]
    elif (
        ini["value_attachment_content_type"]
        or ini["value_attachment_url"]
        or ini["value_attachment_data"]
        or ini["value_attachment_title"]
    ):
        entry["valueAttachment"] = {
            "contentType": ini["value_attachment_content_type"],
            "language": ini["value_attachment_language"],
            "data": ini["value_attachment_data"],
            "url": ini["value_attachment_url"],
            "size": ini["value_attachment_size"],
            "hash": ini["value_attachment_hash"],
            "title": ini["value_attachment_title"],
            "creation": _iso(ini["value_attachment_creation"]),
        }
    elif ini["value_coding_system"] or ini["value_coding_code"]:
        entry["valueCoding"] = _coding(ini, "value_coding_")
    elif _has_quantity(ini, "value_quantity"):
        entry["valueQuantity"] = _quantity(ini, "value_quantity", "qc_text")
    elif _has_ref(ini, "value_reference"):
        entry["valueReference"] = _ref(ini, "value_reference")
    return entry


def _item_tree(bind, pk):
    """Rebuild the nested item[] shape from the flat item table: an item is a child of another
    item through `parent_item_id` (NULL = top level)."""
    items = _rows(
        bind,
        f"SELECT *, type::text AS type_text, enable_behavior::text AS behavior_text "
        f"FROM {P}_item WHERE {P}_pk = :v ORDER BY id",
        v=pk,
    )
    sub = f"SELECT id FROM {P}_item WHERE {P}_pk = :v"

    def grouped(table, extra=""):
        out = {}
        for r in _rows(
            bind,
            f"SELECT *{extra} FROM {table} WHERE {P}_item_id IN ({sub}) ORDER BY id",
            v=pk,
        ):
            out.setdefault(r[f"{P}_item_id"], []).append(r)
        return out

    codings = grouped(f"{P}_item_coding")
    enable_whens = grouped(
        f"{P}_item_enable_when",
        ", operator::text AS operator_text, answer_quantity_comparator::text AS qc_text",
    )
    options = grouped(f"{P}_item_answer_option")
    initials = grouped(
        f"{P}_item_initial", ", value_quantity_comparator::text AS qc_text"
    )

    by_parent = {}
    for item in items:
        by_parent.setdefault(item["parent_item_id"], []).append(item)

    def render(parent_id):
        out = []
        for item in by_parent.get(parent_id, []):
            entry = {
                "linkId": item["link_id"],
                "definition": item["definition"],
                "code": [_coding(c) for c in codings.get(item["id"], [])],
                "prefix": item["prefix"],
                "text": item["text"],
                "type": (item["type_text"] or "").replace("open_choice", "open-choice"),
                "enableWhen": [
                    _enable_when(e) for e in enable_whens.get(item["id"], [])
                ],
                "enableBehavior": item["behavior_text"],
                "required": item["required"],
                "repeats": item["repeats"],
                "readOnly": item["read_only"],
                "maxLength": item["max_length"],
                "answerValueSet": item["answer_value_set"],
                "answerOption": [
                    _answer_option(o) for o in options.get(item["id"], [])
                ],
                "initial": [_initial(i) for i in initials.get(item["id"], [])],
                "item": render(item["id"]),
            }
            out.append(entry)
        return out

    return render(None)


def _build_content(bind, r):
    pk = r["id"]
    content = {
        "extension": list(_json(r["extension"]) or []),
        "url": r["url"],
        "identifier": _identifiers(bind, pk),
        "version": r["version"],
        "name": r["name"],
        "title": r["title"],
        "derivedFrom": list(r["derived_from"] or []),
        "status": r["status_text"],
        "experimental": r["experimental"],
        "subjectType": list(r["subject_type"] or []),
        "date": _iso(r["date"]),
        "publisher": r["publisher"],
        "contact": _contacts(bind, pk),
        "description": r["description"],
        "useContext": _use_contexts(bind, pk),
        "jurisdiction": _jurisdictions(bind, pk),
        "purpose": r["purpose"],
        "copyright": r["copyright"],
        "approvalDate": _iso(r["approval_date"]),
        "lastReviewDate": _iso(r["last_review_date"]),
        "effectivePeriod": _period(
            r["effective_period_start"], r["effective_period_end"]
        ),
        "code": [_coding(c) for c in _rows_of(bind, f"{P}_coding", f"{P}_pk", pk)],
        "item": _item_tree(bind, pk),
    }
    return _prune(content)


def _backfill_content(bind):
    # `status` is an enum: cast it to text so the driver returns the label.
    for r in _rows(bind, f"SELECT *, status::text AS status_text FROM {P}"):
        bind.execute(
            sa.text(f"UPDATE {P} SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {
                "c": json.dumps(_build_content(bind, dict(r)), default=str),
                "id": r["id"],
            },
        )


# -- upgrade: content -> search index (frozen copy of _indexer.py) --------------------------


def _items(items):
    out = []
    for item in items or []:
        if isinstance(item, dict):
            out.append(item)
            out += _items(item.get("item"))
    return out


def _insert_identifier(bind, pk, identifier):
    if not (identifier.get("system") or identifier.get("value")):
        return
    itype = identifier.get("type") or {}
    for c in itype.get("coding") or [{}]:
        bind.execute(
            sa.text(
                f"INSERT INTO {P}_identifier ({P}_pk, system, value, type_system, type_code, "
                "type_text_norm, type_display_norm) VALUES (:pk, :s, :v, :ts, :tc, :tt, :td)"
            ),
            {
                "pk": pk,
                "s": identifier.get("system"),
                "v": identifier.get("value"),
                "ts": c.get("system"),
                "tc": c.get("code"),
                "tt": _norm(itype.get("text")),
                "td": _norm(c.get("display")),
            },
        )


def _insert_token(bind, pk, param, slot, system, code, display=None, text=None):
    bind.execute(
        sa.text(
            f"INSERT INTO {P}_token ({P}_pk, param, slot, system, code, display_norm, text_norm) "
            "VALUES (:pk, :param, :slot, :s, :c, :d, :t)"
        ),
        {
            "pk": pk,
            "param": param,
            "slot": slot,
            "s": system,
            "c": code,
            "d": _norm(display),
            "t": _norm(text),
        },
    )


def _insert_concept(bind, pk, param, slot, concept):
    """One row per coding, plus a code-less row for a concept that only has `text`."""
    text = concept.get("text")
    codings = [
        c
        for c in concept.get("coding") or []
        if c.get("system") or c.get("code") or c.get("display")
    ]
    for c in codings:
        _insert_token(
            bind,
            pk,
            param,
            slot,
            c.get("system"),
            c.get("code"),
            c.get("display"),
            text,
        )
    if not codings and text:
        _insert_token(bind, pk, param, slot, None, None, None, text)


def _insert_coding(bind, pk, param, slot, c):
    if c.get("system") or c.get("code") or c.get("display"):
        _insert_token(
            bind, pk, param, slot, c.get("system"), c.get("code"), c.get("display")
        )


def _number(quantity):
    value = (quantity or {}).get("value")
    return value if isinstance(value, (int, float)) else None


def _insert_context_quantity(bind, pk, slot, context):
    quantity, rng = context.get("valueQuantity"), context.get("valueRange")
    if quantity:
        low = high = _number(quantity)
        source = quantity
    elif rng:
        low, high = _number(rng.get("low")), _number(rng.get("high"))
        source = (rng.get("low") if low is not None else rng.get("high")) or {}
    else:
        return
    if low is None and high is None:
        return
    bind.execute(
        sa.text(
            f"INSERT INTO {P}_context_quantity ({P}_pk, slot, quantity_low, quantity_high, "
            "quantity_system, quantity_code, quantity_unit) VALUES (:pk, :slot, :lo, :hi, :s, :c, :u)"
        ),
        {
            "pk": pk,
            "slot": slot,
            "lo": low,
            "hi": high,
            "s": source.get("system"),
            "c": source.get("code"),
            "u": source.get("unit"),
        },
    )


def _rebuild_index(bind):
    for row in _rows(bind, f"SELECT id, content FROM {P}"):
        pk, doc = row["id"], _json(row["content"])
        status = doc.get("status")
        d_start, d_end = _bounds(doc.get("date"))
        period = doc.get("effectivePeriod") or {}
        columns = {
            "url": doc.get("url"),
            "version": doc.get("version"),
            "name": doc.get("name"),
            "name_norm": _norm(doc.get("name")),
            "title": doc.get("title"),
            "title_norm": _norm(doc.get("title")),
            "description": doc.get("description"),
            "description_norm": _norm(doc.get("description")),
            "publisher": doc.get("publisher"),
            "publisher_norm": _norm(doc.get("publisher")),
            "date_start": d_start,
            "date_end": d_end,
            "effective_start": _bounds(period.get("start"))[0],
            "effective_end": _bounds(period.get("end"))[1],
        }
        sets = ", ".join(f"{k} = :{k}" for k in columns)
        bind.execute(
            sa.text(
                f"UPDATE {P} SET status = CAST(:status AS questionnaire_status), {sets} "
                "WHERE id = :pk"
            ),
            {**columns, "status": status if status in _STATUS else None, "pk": pk},
        )
        # subjectType: the enum array (a code outside the value set is dropped).
        known = [c for c in doc.get("subjectType") or [] if c in _SUBJECT_TYPES]
        if known:
            bind.execute(
                sa.text(
                    f"UPDATE {P} SET subject_type = CAST(:types AS questionnaire_subject_type[]) "
                    "WHERE id = :pk"
                ),
                {"types": known, "pk": pk},
            )

        for identifier in doc.get("identifier") or []:
            _insert_identifier(bind, pk, identifier)
        for concept in doc.get("jurisdiction") or []:
            _insert_concept(bind, pk, "jurisdiction", 0, concept)
        for item in _items(doc.get("item")):
            for c in item.get("code") or []:
                _insert_coding(bind, pk, "code", 0, c)
            if item.get("definition"):
                bind.execute(
                    sa.text(
                        f"INSERT INTO {P}_definition ({P}_pk, uri) VALUES (:pk, :u)"
                    ),
                    {"pk": pk, "u": item["definition"]},
                )
        for slot, context in enumerate(doc.get("useContext") or [], start=1):
            _insert_coding(bind, pk, "context-type", slot, context.get("code") or {})
            if context.get("valueCodeableConcept"):
                _insert_concept(
                    bind, pk, "context", slot, context["valueCodeableConcept"]
                )
            _insert_context_quantity(bind, pk, slot, context)


# Every old Questionnaire child table. The new index table (identifier) is dropped with them and
# recreated below; dropped with CASCADE, so order does not matter.
_OLD_TABLES = (
    "questionnaire_item_enable_when",
    "questionnaire_item_answer_option",
    "questionnaire_item_initial",
    "questionnaire_item_coding",
    "questionnaire_item",
    "questionnaire_use_context_value_coding",
    "questionnaire_use_context",
    "questionnaire_contact_telecom",
    "questionnaire_contact",
    "questionnaire_jurisdiction_coding",
    "questionnaire_jurisdiction",
    "questionnaire_coding",
    "questionnaire_identifier_type_coding",
    "questionnaire_identifier",
)

# The per-field enums of the old schema. `questionnaire_status` stays (it already held the true
# FHIR codes); the `questionnaire_response_*` enums belong to another resource.
_OLD_ENUMS = (
    "questionnaire_item_type",
    "questionnaire_enable_behavior",
    "questionnaire_item_operator",
    "questionnaire_quantity_comparator",
    "questionnaire_use_context_value_reference_type",
)

# Main-table columns that survive unchanged: the id, the audit/tenant columns and the plain
# search columns.
_KEEP = {
    "id",
    "questionnaire_id",
    "tenant_id",
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
    "content",
    "status",
    "url",
    "version",
    "name",
    "title",
    "publisher",
    "description",
}


def _fk():
    return sa.Column(
        f"{P}_pk", sa.BigInteger(), sa.ForeignKey(f"{P}.id"), nullable=False
    )


def _index(table, *columns):
    op.create_index(op.f("ix_" + table + "_" + columns[0]), table, list(columns))


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column(
        P, sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    _backfill_content(bind)

    for table in _OLD_TABLES:
        op.execute(f'DROP TABLE IF EXISTS "{table}" CASCADE')
    existing = [
        r[0]
        for r in bind.execute(
            sa.text(
                f"SELECT column_name FROM information_schema.columns WHERE table_name = '{P}' "
                "AND table_schema = current_schema()"
            )
        )
    ]
    for column in existing:
        if column not in _KEEP:
            op.drop_column(P, column)
    for name in _OLD_ENUMS:
        op.execute(f'DROP TYPE IF EXISTS "{name}"')

    # The public id's sequence is now its server default.
    op.execute(
        f"ALTER TABLE {P} ALTER COLUMN questionnaire_id "
        "SET DEFAULT nextval('questionnaire_pub_seq')"
    )

    # The audit columns as the shared mixin declares them (the original table was created with
    # looser ones): tenant/actor NOT NULL, timestamps nullable and indexed, and no UNIQUE on the
    # public id (the sequence keeps it unique).
    op.execute(f"UPDATE {P} SET tenant_id = '' WHERE tenant_id IS NULL")
    op.execute(f"UPDATE {P} SET created_by = '' WHERE created_by IS NULL")
    op.alter_column(P, "tenant_id", existing_type=sa.String(), nullable=False)
    op.alter_column(P, "created_by", existing_type=sa.String(), nullable=False)
    op.alter_column(
        P, "created_at", existing_type=sa.DateTime(timezone=True), nullable=True
    )
    op.alter_column(
        P, "updated_at", existing_type=sa.DateTime(timezone=True), nullable=True
    )
    op.execute(
        f"ALTER TABLE {P} DROP CONSTRAINT IF EXISTS questionnaire_questionnaire_id_key"
    )
    for column in ("tenant_id", "created_at", "updated_at"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)

    # The status column is nullable now (an index, not a requirement).
    op.alter_column(
        P,
        "status",
        existing_type=postgresql.ENUM(
            *_STATUS, name="questionnaire_status", create_type=False
        ),
        nullable=True,
    )
    postgresql.ENUM(*_SUBJECT_TYPES, name="questionnaire_subject_type").create(
        bind, checkfirst=True
    )
    op.add_column(
        P,
        sa.Column(
            "subject_type",
            postgresql.ARRAY(
                postgresql.ENUM(
                    *_SUBJECT_TYPES,
                    name="questionnaire_subject_type",
                    create_type=False,
                )
            ),
            nullable=True,
        ),
    )
    for column in ("name_norm", "title_norm", "publisher_norm"):
        op.add_column(P, sa.Column(column, sa.String(), nullable=True))
    op.add_column(P, sa.Column("description_norm", sa.Text(), nullable=True))
    for column in ("date_start", "date_end", "effective_start", "effective_end"):
        op.add_column(P, sa.Column(column, sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        f"{P}_identifier",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column("system", sa.String(), nullable=True),
        sa.Column("value", sa.String(), nullable=True),
        sa.Column("type_system", sa.String(), nullable=True),
        sa.Column("type_code", sa.String(), nullable=True),
        sa.Column("type_text_norm", sa.String(), nullable=True),
        sa.Column("type_display_norm", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(f"{P}_identifier", f"{P}_pk")
    _index(f"{P}_identifier", "value")

    op.create_table(
        f"{P}_token",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column("param", sa.String(), nullable=False),
        sa.Column("slot", sa.Integer(), server_default="0", nullable=False),
        sa.Column("system", sa.String(), nullable=True),
        sa.Column("code", sa.String(), nullable=True),
        sa.Column("display_norm", sa.String(), nullable=True),
        sa.Column("text_norm", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(f"{P}_token", f"{P}_pk")
    op.create_index(
        "ix_questionnaire_token_param_code", f"{P}_token", ["param", "code"]
    )

    op.create_table(
        f"{P}_definition",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column("uri", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(f"{P}_definition", f"{P}_pk")
    _index(f"{P}_definition", "uri")

    op.create_table(
        f"{P}_context_quantity",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column("slot", sa.Integer(), nullable=False),
        sa.Column("quantity_low", sa.Numeric(), nullable=True),
        sa.Column("quantity_high", sa.Numeric(), nullable=True),
        sa.Column("quantity_system", sa.String(), nullable=True),
        sa.Column("quantity_code", sa.String(), nullable=True),
        sa.Column("quantity_unit", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(f"{P}_context_quantity", f"{P}_pk")

    _rebuild_index(bind)
    op.create_index("ix_questionnaire_date", P, ["date_start", "date_end"])
    op.create_index(
        "ix_questionnaire_effective", P, ["effective_start", "effective_end"]
    )
    op.create_index("ix_questionnaire_name_norm", P, ["name_norm"])
    op.create_index("ix_questionnaire_title_norm", P, ["title_norm"])
    op.create_index("ix_questionnaire_url", P, ["url"])
    op.create_index("ix_questionnaire_status", P, ["status"], if_not_exists=True)
    op.create_index("ix_questionnaire_id", P, ["id"], if_not_exists=True)
    op.create_index(
        "ix_questionnaire_questionnaire_id",
        P,
        ["questionnaire_id"],
        unique=True,
        if_not_exists=True,
    )
    op.alter_column(P, "content", nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "questionnaire content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
