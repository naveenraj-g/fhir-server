"""activity_definition: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: e5f8a1b4c962
Revises: d4e7f0a3b851
Create Date: 2026-12-25 10:00:00.000000

Stores ActivityDefinition whole in `content` (see ActivityDefinitionModel's docstring), like the
other resources already moved (CommunicationRequest d4e7f0a3b851, Questionnaire f7d2b5a9c316,
...). The whole FHIR resource - `identifier`, `contact` (and `author` / `editor` / `reviewer` /
`endorser`), `useContext`, `jurisdiction`, `topic`, `relatedArtifact`, `library`, `code`,
`timing[x]`, `participant`, `product[x]`, `quantity`, `dosage`, `bodySite`, the three
requirement lists, `dynamicValue`, `subject[x]` and `extension` - moves into
`activity_definition.content`; every column/table that survives is a search index for one of the
FHIR R4 ActivityDefinition search parameters (or `_id` / `_lastUpdated`), derived from `content`:

  activity_definition: status (the enum already held the true FHIR codes, so it stays), url,
      version, name / title / description / publisher (each plus a `*_norm` twin), date_start/_end
      (new: the range the dateTime covers; the old `date` instant is dropped) and
      effective_start/_end (new: the half-open range of effectivePeriod); the public id gets its
      sequence as a server default; new: content.
  activity_definition_identifier: rebuilt as an index table (one row per identifier x type coding)
  activity_definition_token: new - jurisdiction, topic, context-type and context (the last two
      carry the useContext's slot)
  activity_definition_reference: new - the `resource` canonical of each relatedArtifact of type
      composed-of / depends-on / derived-from / predecessor / successor and each `library`
      (also `depends-on`)
  activity_definition_context_quantity: new - one row per useContext whose value is a Quantity /
      Range
  dropped: every other child table (contact, use context, jurisdiction, topic, body site, code /
      subject / product codings, related artifact, participant, dosage, dynamic value and the
      three requirement tables), every main-table column with no search parameter and the
      per-field `activity_definition_*` enums (the status enum stays).

upgrade: (1) builds `content` for every existing row from the old columns and tables - a frozen
copy of the old to_fhir_activity_definition() logic (but keeping a reference's raw string, so an
absolute URL is not lost), so this migration never depends on application code that has since
changed; (2) drops the old child tables/columns and creates the index tables; (3) rebuilds the
index from `content`.

downgrade: not supported. Everything the old schema held is preserved in `content`, but
rebuilding the old normalized tables from it is not implemented - restore from a backup taken
before upgrading.
"""

import json
import re
import unicodedata
from collections.abc import Sequence
from datetime import UTC, date, datetime, time, timedelta, timezone
from decimal import Decimal

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e5f8a1b4c962"
down_revision: str | None = "d4e7f0a3b851"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

P = "activity_definition"

_STATUS = ("draft", "active", "retired", "unknown")
_COMPARATOR = {"lt": "<", "le": "<=", "ge": ">=", "gt": ">"}


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
        "Medication",
        "Substance",
        "SpecimenDefinition",
        "ObservationDefinition",
    )
}


def _code(value):
    """An enum label read back as text: a member name (`original_order`) is the FHIR code with
    `_` for `-`."""
    return value.replace("_", "-") if isinstance(value, str) else value


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


def _q(row, prefix, comparator_key=None):
    """A Quantity from `{prefix}_value/_unit/_system/_code` (every column read tolerantly)."""
    comparator = row.get(comparator_key) if comparator_key else None
    return {
        "value": _num(row.get(f"{prefix}_value")),
        "comparator": _COMPARATOR.get(comparator, comparator),
        "unit": row.get(f"{prefix}_unit"),
        "system": row.get(f"{prefix}_system"),
        "code": row.get(f"{prefix}_code"),
    }


def _has_q(row, prefix):
    return any(
        row.get(f"{prefix}_{k}") not in (None, "")
        for k in ("value", "unit", "system", "code")
    )


def _concept(codings, text):
    return {"coding": [_coding(c) for c in codings], "text": text}


def _cc_list(bind, pk, table):
    """The old CodeableConcept-list tables: `{P}_{table}` (text) + `{P}_{table}_coding`."""
    return [
        _concept(
            _rows_of(bind, f"{P}_{table}_coding", f"{P}_{table}_id", row["id"]),
            row["text"],
        )
        for row in _rows_of(bind, f"{P}_{table}", f"{P}_pk", pk)
    ]


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
                "type": _concept(
                    _rows_of(
                        bind,
                        f"{P}_identifier_type_coding",
                        "identifier_id",
                        i["id"],
                    ),
                    i["type_text"],
                ),
                "system": i["system"],
                "value": i["value"],
                "period": _period(i["period_start"], i["period_end"]),
                "assigner": _ref(i, "assigner"),
            }
        )
    return out


def _contacts(bind, pk, role):
    out = []
    for c in _rows(
        bind,
        f"SELECT *, role::text AS role_text FROM {P}_contact WHERE {P}_pk = :v ORDER BY id",
        v=pk,
    ):
        if _code(c["role_text"]) != role:
            continue
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
            entry["valueCodeableConcept"] = _concept(
                codings, uc["value_codeable_concept_text"]
            )
        elif _has_q(uc, "value_quantity"):
            entry["valueQuantity"] = _q(uc, "value_quantity", "comparator_text")
        elif (
            uc["value_range_low_value"] is not None
            or uc["value_range_high_value"] is not None
        ):
            entry["valueRange"] = {
                "low": _q(uc, "value_range_low"),
                "high": _q(uc, "value_range_high"),
            }
        elif _has_ref(uc, "value_reference"):
            entry["valueReference"] = _ref(uc, "value_reference")
        out.append(entry)
    return out


def _related_artifacts(bind, pk):
    return [
        {
            "type": _code(a["type_text"]),
            "label": a["label"],
            "display": a["display"],
            "citation": a["citation"],
            "url": a["url"],
            "document": _json(a["document"]),
            "resource": a["resource"],
        }
        for a in _rows(
            bind,
            f"SELECT *, type::text AS type_text FROM {P}_related_artifact "
            f"WHERE {P}_pk = :v ORDER BY id",
            v=pk,
        )
    ]


def _participants(bind, pk):
    return [
        {
            "type": _code(p["type_text"]),
            "role": _concept(
                _rows_of(
                    bind,
                    f"{P}_participant_role_coding",
                    f"{P}_participant_id",
                    p["id"],
                ),
                p["role_text"],
            ),
        }
        for p in _rows(
            bind,
            f"SELECT *, type::text AS type_text FROM {P}_participant "
            f"WHERE {P}_pk = :v ORDER BY id",
            v=pk,
        )
    ]


def _dosage_cc(bind, d):
    def cc(kind, text_col):
        return _concept(
            _rows_of(bind, f"{P}_dosage_{kind}_coding", f"{P}_dosage_id", d["id"]),
            d[text_col],
        )

    return cc


def _dosages(bind, pk):
    out = []
    for d in _rows_of(bind, f"{P}_dosage", f"{P}_pk", pk):
        cc = _dosage_cc(bind, d)

        out.append(
            {
                "sequence": d["sequence"],
                "text": d["text"],
                "patientInstruction": d["patient_instruction"],
                "timing": _json(d["timing"]),
                "asNeededBoolean": d["as_needed_boolean"],
                "asNeededCodeableConcept": cc(
                    "as_needed", "as_needed_codeable_concept_text"
                ),
                "site": cc("site", "site_text"),
                "route": cc("route", "route_text"),
                "method": cc("method", "method_text"),
                "doseAndRate": _json(d["dose_and_rate"]),
                "maxDosePerPeriod": _json(d["max_dose_per_period"]),
                "maxDosePerAdministration": _q(d, "max_dose_per_administration"),
                "maxDosePerLifetime": _q(d, "max_dose_per_lifetime"),
            }
        )
    return out


def _dynamic_values(bind, pk):
    return [
        {
            "path": dv["path"],
            "expression": {
                "description": dv["expression_description"],
                "name": dv["expression_name"],
                "language": dv["expression_language"],
                "expression": dv["expression_expression"],
                "reference": dv["expression_reference"],
            },
        }
        for dv in _rows_of(bind, f"{P}_dynamic_value", f"{P}_pk", pk)
    ]


def _requirements(bind, pk, table):
    return [_ref(r, "reference") for r in _rows_of(bind, f"{P}_{table}", f"{P}_pk", pk)]


def _timing(r):
    """timing[x]: the same precedence the old mapper used."""
    if r["timing_timing"]:
        return {"timingTiming": _json(r["timing_timing"])}
    if r["timing_date_time"]:
        return {"timingDateTime": _iso(r["timing_date_time"])}
    if _has_q(r, "timing_age"):
        return {"timingAge": _q(r, "timing_age")}
    if r["timing_period_start"] or r["timing_period_end"]:
        return {
            "timingPeriod": _period(r["timing_period_start"], r["timing_period_end"])
        }
    if _has_q(r, "timing_range_low") or _has_q(r, "timing_range_high"):
        return {
            "timingRange": {
                "low": _q(r, "timing_range_low"),
                "high": _q(r, "timing_range_high"),
            }
        }
    if _has_q(r, "timing_duration"):
        return {"timingDuration": _q(r, "timing_duration")}
    return {}


def _build_content(bind, r):
    pk = r["id"]
    codings = lambda table: _rows_of(bind, table, f"{P}_pk", pk)
    content = {
        "extension": list(_json(r["extension"]) or []),
        "url": r["url"],
        "identifier": _identifiers(bind, pk),
        "version": r["version"],
        "name": r["name"],
        "title": r["title"],
        "subtitle": r["subtitle"],
        "status": r["status_text"],
        "experimental": r["experimental"],
        "date": _iso(r["date"]),
        "publisher": r["publisher"],
        "contact": _contacts(bind, pk, "contact"),
        "author": _contacts(bind, pk, "author"),
        "editor": _contacts(bind, pk, "editor"),
        "reviewer": _contacts(bind, pk, "reviewer"),
        "endorser": _contacts(bind, pk, "endorser"),
        "description": r["description"],
        "useContext": _use_contexts(bind, pk),
        "jurisdiction": _cc_list(bind, pk, "jurisdiction"),
        "purpose": r["purpose"],
        "usage": r["usage"],
        "copyright": r["copyright"],
        "approvalDate": _iso(r["approval_date"]),
        "lastReviewDate": _iso(r["last_review_date"]),
        "effectivePeriod": _period(
            r["effective_period_start"], r["effective_period_end"]
        ),
        "topic": _cc_list(bind, pk, "topic"),
        "relatedArtifact": _related_artifacts(bind, pk),
        "library": list(r["library"] or []),
        "kind": r["kind_text"],
        "profile": r["profile"],
        "code": _concept(codings(f"{P}_code_coding"), r["code_text"]),
        "intent": _code(r["intent_text"]),
        "priority": _code(r["priority_text"]),
        "doNotPerform": r["do_not_perform"],
        "location": _ref(r, "location"),
        "participant": _participants(bind, pk),
        "quantity": _q(r, "quantity", "comparator_text"),
        "dosage": _dosages(bind, pk),
        "bodySite": _cc_list(bind, pk, "body_site"),
        "specimenRequirement": _requirements(bind, pk, "specimen_requirement"),
        "observationRequirement": _requirements(bind, pk, "observation_requirement"),
        "observationResultRequirement": _requirements(
            bind, pk, "observation_result_requirement"
        ),
        "transform": r["transform"],
        "dynamicValue": _dynamic_values(bind, pk),
        **_timing(r),
    }
    # subject[x] / product[x]: the CodeableConcept when it has anything, else the Reference.
    subject_codings = codings(f"{P}_subject_coding")
    if subject_codings or r["subject_codeable_concept_text"]:
        content["subjectCodeableConcept"] = _concept(
            subject_codings, r["subject_codeable_concept_text"]
        )
    else:
        content["subjectReference"] = _ref(r, "subject")
    product_codings = codings(f"{P}_product_coding")
    if product_codings or r["product_codeable_concept_text"]:
        content["productCodeableConcept"] = _concept(
            product_codings, r["product_codeable_concept_text"]
        )
    else:
        content["productReference"] = _ref(r, "product")
    return _prune(content)


def _backfill_content(bind):
    # status / kind / intent / priority / quantity comparator are enums: cast them to text so the
    # driver returns the label.
    for r in _rows(
        bind,
        f"SELECT *, status::text AS status_text, kind::text AS kind_text, "
        f"intent::text AS intent_text, priority::text AS priority_text, "
        f"quantity_comparator::text AS comparator_text FROM {P}",
    ):
        bind.execute(
            sa.text(f"UPDATE {P} SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {
                "c": json.dumps(_build_content(bind, dict(r)), default=str),
                "id": r["id"],
            },
        )


# -- upgrade: content -> search index (frozen copy of _indexer.py) --------------------------

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")
_REFERENCE_TYPES = (
    "composed-of",
    "depends-on",
    "derived-from",
    "predecessor",
    "successor",
)


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


def _insert_reference(bind, pk, param, value):
    match = _REF.match(value or "")
    bind.execute(
        sa.text(
            f"INSERT INTO {P}_reference ({P}_pk, param, reference_reference, reference_type, "
            "reference_id) VALUES (:pk, :param, :r, :t, :i)"
        ),
        {
            "pk": pk,
            "param": param,
            "r": value,
            "t": match["type"] if match else None,
            "i": int(match["id"]) if match else None,
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
                f"UPDATE {P} SET status = CAST(:status AS activity_definition_status), {sets} "
                "WHERE id = :pk"
            ),
            {**columns, "status": status if status in _STATUS else None, "pk": pk},
        )

        for identifier in doc.get("identifier") or []:
            _insert_identifier(bind, pk, identifier)
        for concept in doc.get("jurisdiction") or []:
            _insert_concept(bind, pk, "jurisdiction", 0, concept)
        for concept in doc.get("topic") or []:
            _insert_concept(bind, pk, "topic", 0, concept)
        for slot, context in enumerate(doc.get("useContext") or [], start=1):
            _insert_coding(bind, pk, "context-type", slot, context.get("code") or {})
            if context.get("valueCodeableConcept"):
                _insert_concept(
                    bind, pk, "context", slot, context["valueCodeableConcept"]
                )
            _insert_context_quantity(bind, pk, slot, context)
        for artifact in doc.get("relatedArtifact") or []:
            resource = artifact.get("resource") if isinstance(artifact, dict) else None
            if (
                isinstance(resource, str)
                and resource
                and artifact.get("type") in _REFERENCE_TYPES
            ):
                _insert_reference(bind, pk, artifact["type"], resource)
        for library in doc.get("library") or []:
            if isinstance(library, str) and library:
                _insert_reference(bind, pk, "depends-on", library)


# The main-table columns that survive unchanged: the id, the audit/tenant columns and the plain
# search columns. Everything else of the old table is dropped; so is every `activity_definition_*`
# child table and per-field enum (matched by prefix, which no other resource shares) - the status
# enum stays, it already held the true FHIR codes.
_KEEP = {
    "id",
    "activity_definition_id",
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

    # Every old child table (`activity_definition_*`), but not this table itself.
    for (table,) in bind.execute(
        sa.text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema() "
            "AND table_name LIKE 'activity\\_definition\\_%' AND table_type = 'BASE TABLE'"
        )
    ).all():
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
    for (name,) in bind.execute(
        sa.text(
            "SELECT typname FROM pg_type WHERE typtype = 'e' "
            "AND typname LIKE 'activity\\_definition\\_%' "
            "AND typname <> 'activity_definition_status'"
        )
    ).all():
        op.execute(f'DROP TYPE IF EXISTS "{name}"')

    # The public id's sequence is now its server default.
    op.execute(
        f"ALTER TABLE {P} ALTER COLUMN activity_definition_id "
        "SET DEFAULT nextval('activity_definition_pub_seq')"
    )

    # The audit columns as the shared mixin declares them (the original table was created with
    # looser ones; tenant_id may be a bigint): tenant/actor NOT NULL strings, timestamps nullable
    # and indexed, and no UNIQUE on the public id (the sequence keeps it unique).
    op.alter_column(
        P,
        "tenant_id",
        type_=sa.String(),
        existing_nullable=True,
        postgresql_using="tenant_id::text",
    )
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
        f"ALTER TABLE {P} DROP CONSTRAINT IF EXISTS activity_definition_activity_definition_id_key"
    )
    for column in ("tenant_id", "created_at", "updated_at"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)

    # The status column is nullable now (an index, not a requirement).
    op.alter_column(
        P,
        "status",
        existing_type=postgresql.ENUM(
            *_STATUS, name="activity_definition_status", create_type=False
        ),
        nullable=True,
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
        "ix_activity_definition_token_param_code", f"{P}_token", ["param", "code"]
    )

    op.create_table(
        f"{P}_reference",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column("param", sa.String(), nullable=False),
        sa.Column("reference_reference", sa.String(), nullable=True),
        sa.Column("reference_type", sa.String(), nullable=True),
        sa.Column("reference_id", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(f"{P}_reference", f"{P}_pk")
    op.create_index(
        "ix_activity_definition_reference_param_type_id",
        f"{P}_reference",
        ["param", "reference_type", "reference_id"],
    )

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
    # The old lone-name index goes; the new ones follow the model.
    op.execute("DROP INDEX IF EXISTS ix_activity_definition_name")
    op.create_index("ix_activity_definition_date", P, ["date_start", "date_end"])
    op.create_index(
        "ix_activity_definition_effective", P, ["effective_start", "effective_end"]
    )
    op.create_index("ix_activity_definition_name_norm", P, ["name_norm"])
    op.create_index("ix_activity_definition_title_norm", P, ["title_norm"])
    op.create_index("ix_activity_definition_url", P, ["url"], if_not_exists=True)
    op.create_index("ix_activity_definition_status", P, ["status"], if_not_exists=True)
    op.create_index("ix_activity_definition_id", P, ["id"], if_not_exists=True)
    op.create_index(
        "ix_activity_definition_activity_definition_id",
        P,
        ["activity_definition_id"],
        unique=True,
        if_not_exists=True,
    )
    op.alter_column(P, "content", nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "activity_definition content/index migration is one-way: its old normalized tables are "
        "not rebuilt from `content`. Restore from a backup taken before upgrading."
    )
