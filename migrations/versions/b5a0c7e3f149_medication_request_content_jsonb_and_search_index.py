"""medication_request: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: b5a0c7e3f149
Revises: a4f9b6d2e038
Create Date: 2026-12-14 10:00:00.000000

Medplum-style storage for MedicationRequest (see MedicationRequestModel's docstring), same as the
other resources already moved (the latest being Medication a4f9b6d2e038). The whole FHIR resource
moves into `medication_request.content`; every column/table that survives is a search index for
one of the FHIR R4 MedicationRequest search parameters (or `_id` / `_lastUpdated`), derived from
`content`:

  medication_request: status / intent / priority (recreated as enums holding the real FHIR codes -
      the old ones stored `on_hold`, `original_order`, ...), authored_start/_end, the subject_* /
      encounter_* / requester_* / performer_* columns (their `*_type` becomes a plain string), and
      the new medication_* (medicationReference) and dispenser_* (dispenseRequest.performer)
      reference columns; the public id gets its sequence as a server default; new: content.
  medication_request_identifier: rebuilt as an index table
  medication_request_token: new - category, code (medicationCodeableConcept), intended-performertype
  medication_request_timing: new - one row per dosageInstruction.timing.event
  dropped: every old child table (dosage instructions and their codings, categories, reasons, notes,
      references, identifier type codings, ...), every main-table column with no search parameter
      and the per-field `medication_request_*` enums.

upgrade: (1) builds `content` for every existing row from the old columns and tables - a frozen
copy of the old to_fhir_medication_request() logic (but keeping a reference's raw string, so an
absolute URL is not lost), so this migration never depends on application code that has since
changed; (2) drops the old child tables/columns and creates the index tables; (3) rebuilds the
index from `content`.

downgrade: not supported. Everything the old schema held is preserved in `content`, but rebuilding
the old normalized tables from it is not implemented - restore from a backup taken before
upgrading.
"""

import json
import re
import unicodedata
from datetime import UTC, date, datetime, time, timedelta, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b5a0c7e3f149"
down_revision: Union[str, None] = "a4f9b6d2e038"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

P = "medication_request"

_STATUS = (
    "active",
    "on-hold",
    "cancelled",
    "completed",
    "entered-in-error",
    "stopped",
    "draft",
    "unknown",
)
_INTENT = (
    "proposal",
    "plan",
    "order",
    "original-order",
    "reflex-order",
    "filler-order",
    "instance-order",
    "option",
)
_PRIORITY = ("routine", "urgent", "asap", "stat")


# -- shared helpers (frozen - never import application code here) --------------


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


def _hyphenate(old):
    """The FHIR code for an old enum label (`on_hold` becomes `on-hold`)."""
    return old.replace("_", "-") if old else old


def _norm(text):
    """Frozen copy of app.fhir.search.values.normalize."""
    if text is None:
        return None
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


_DATE_RE = re.compile(
    r"^(?P<y>\d{4})(?:-(?P<m>\d{2})(?:-(?P<d>\d{2})(?:T(?P<H>\d{2}):(?P<M>\d{2})"
    r"(?::(?P<S>\d{2})(?P<f>\.\d+)?)?(?P<tz>Z|[+-]\d{2}:\d{2})?)?)?)?$"
)


def _bounds(value):
    """(start, end) instants of a FHIR date/dateTime at its written precision - the half-open
    range it covers (frozen copy of app.fhir.search.values.parse_date). (None, None) if absent or
    unparseable."""
    if not value:
        return None, None
    g = _DATE_RE.match(str(value))
    if not g:
        return None, None
    g = g.groupdict()
    tz = UTC
    if g["tz"] and g["tz"] != "Z":
        sign = 1 if g["tz"][0] == "+" else -1
        tz = timezone(sign * timedelta(hours=int(g["tz"][1:3]), minutes=int(g["tz"][4:6])))
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


def _point(value):
    return _bounds(value) if value else (None, None)


# -- upgrade: old columns/tables -> content (frozen copy of the old mapper) ------

_COMPARATORS = {"lt": "<", "le": "<=", "ge": ">=", "gt": ">"}


def _coding(c):
    return {
        "system": c["system"],
        "version": c["version"],
        "code": c["code"],
        "display": c["display"],
        "userSelected": c["user_selected"],
    }


def _concept(codings, text):
    return {"coding": [_coding(c) for c in codings], "text": text}


def _fallback_identifier(row, prefix):
    """The logical identifier of a Reference (read tolerantly)."""
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
    g = row.get
    raw = g(f"{prefix}_reference")
    if not raw and g(f"{prefix}_type") and g(f"{prefix}_id"):
        raw = f"{g(f'{prefix}_type')}/{g(f'{prefix}_id')}"
    return {
        "reference": raw,
        "display": g(f"{prefix}_display"),
        "identifier": _fallback_identifier(row, f"{prefix}_identifier"),
    }


def _rows_of(bind, table, fk, value):
    return _rows(bind, f"SELECT * FROM {table} WHERE {fk} = :v ORDER BY id", v=value)


def _num(value):
    return float(value) if value is not None else None


def _quantity(row, prefix):
    g = row.get
    quantity = {
        "value": _num(g(f"{prefix}_value")),
        "unit": g(f"{prefix}_unit"),
        "system": g(f"{prefix}_system"),
        "code": g(f"{prefix}_code"),
    }
    if g(f"{prefix}_comparator"):
        quantity["comparator"] = _COMPARATORS.get(str(g(f"{prefix}_comparator")).lower())
    quantity = {k: v for k, v in quantity.items() if v is not None}
    return quantity or None


def _own_identifier(row, prefix, bind, type_table, type_fk, type_fk_value):
    """An Identifier carried either by a child row (prefix "") or flattened into the main row."""
    g = row.get
    return {
        "use": g(f"{prefix}use"),
        "type": _concept(_rows_of(bind, type_table, type_fk, type_fk_value), g(f"{prefix}type_text")),
        "system": g(f"{prefix}system"),
        "value": g(f"{prefix}value"),
        "period": _period(g(f"{prefix}period_start"), g(f"{prefix}period_end")),
        "assigner": _ref(row, f"{prefix}assigner"),
    }


def _cc_list(bind, r, table):
    """A 0..* CodeableConcept held as `<table>` (text) + `<table>_coding`."""
    out = []
    for row in _rows_of(bind, f"{P}_{table}", f"{P}_pk", r["id"]):
        out.append(
            _concept(_rows_of(bind, f"{P}_{table}_coding", f"{P}_{table}_id", row["id"]), row["text"])
        )
    return out


def _cc_of(bind, table, pk, text):
    """A 0..1 CodeableConcept held as `<table>` codings (FK to the main row) + a text column."""
    return _concept(_rows_of(bind, f"{P}_{table}", f"{P}_pk", pk), text)


def _refs(bind, r, table):
    return [_ref(x, "reference") for x in _rows_of(bind, f"{P}_{table}", f"{P}_pk", r["id"])]


def _note(n):
    note = {"time": _iso(n["time"]), "text": n["text"]}
    if n["author_string"]:
        note["authorString"] = n["author_string"]
    else:
        author = _prune(_ref(n, "author"))
        if author:
            note["authorReference"] = author
    return note


def _dosage(bind, d):
    did = d["id"]
    by_dosage = "medication_request_dosage_instruction_id"
    entry = {
        "sequence": d["sequence"],
        "text": d["text"],
        "additionalInstruction": [
            _concept(
                _rows_of(
                    bind,
                    f"{P}_dosage_additional_instruction_coding",
                    f"{P}_dosage_additional_instruction_id",
                    ai["id"],
                ),
                ai["text"],
            )
            for ai in _rows_of(bind, f"{P}_dosage_additional_instruction", by_dosage, did)
        ],
        "patientInstruction": d["patient_instruction"],
        "timing": _json(d["timing"]),
        "site": _concept(_rows_of(bind, f"{P}_dosage_site_coding", by_dosage, did), d["site_text"]),
        "route": _concept(_rows_of(bind, f"{P}_dosage_route_coding", by_dosage, did), d["route_text"]),
        "method": _concept(_rows_of(bind, f"{P}_dosage_method_coding", by_dosage, did), d["method_text"]),
        "doseAndRate": _json(d["dose_and_rate"]),
        "maxDosePerPeriod": _json(d["max_dose_per_period"]),
        "maxDosePerAdministration": _quantity(d, "max_dose_per_administration"),
        "maxDosePerLifetime": _quantity(d, "max_dose_per_lifetime"),
    }
    needed = _concept(
        _rows_of(bind, f"{P}_dosage_as_needed_coding", by_dosage, did), d["as_needed_codeable_concept_text"]
    )
    if d["as_needed_boolean"] is not None:
        entry["asNeededBoolean"] = d["as_needed_boolean"]
    elif _prune(needed):
        entry["asNeededCodeableConcept"] = needed
    return entry


def _dispense_request(r):
    p = "dispense_request_"
    return {
        "initialFill": {
            "quantity": _quantity(r, p + "initial_fill_quantity"),
            "duration": _quantity(r, p + "initial_fill_duration"),
        },
        "dispenseInterval": _quantity(r, p + "dispense_interval"),
        "validityPeriod": _period(r[p + "validity_period_start"], r[p + "validity_period_end"]),
        "numberOfRepeatsAllowed": r[p + "number_of_repeats_allowed"],
        "quantity": _quantity(r, p + "quantity"),
        "expectedSupplyDuration": _quantity(r, p + "expected_supply_duration"),
        "performer": _ref(r, p + "performer"),
    }


def _build_content(bind, r):
    pk = r["id"]
    content = {
        "extension": list(_json(r["extension"]) or []),
        "identifier": [
            _own_identifier(
                i, "", bind, f"{P}_identifier_type_coding", f"{P}_identifier_id", i["id"]
            )
            for i in _rows_of(bind, f"{P}_identifier", f"{P}_pk", pk)
        ],
        "status": _hyphenate(r["status_text"]),
        "statusReason": _cc_of(bind, "status_reason_coding", pk, r["status_reason_text"]),
        "intent": _hyphenate(r["intent_text"]),
        "category": _cc_list(bind, r, "category"),
        "priority": _hyphenate(r["priority_text"]),
        "doNotPerform": r["do_not_perform"],
        "subject": _ref(r, "subject"),
        "encounter": _ref(r, "encounter"),
        "supportingInformation": _refs(bind, r, "supporting_information"),
        "authoredOn": _iso(r["authored_on"]),
        "requester": _ref(r, "requester"),
        "performer": _ref(r, "performer"),
        "performerType": _cc_of(bind, "performer_type_coding", pk, r["performer_type_text"]),
        "recorder": _ref(r, "recorder"),
        "reasonCode": _cc_list(bind, r, "reason_code"),
        "reasonReference": _refs(bind, r, "reason_reference"),
        "instantiatesCanonical": list(r["instantiates_canonical"] or []),
        "instantiatesUri": list(r["instantiates_uri"] or []),
        "basedOn": _refs(bind, r, "based_on"),
        "groupIdentifier": _own_identifier(
            r,
            "group_identifier_",
            bind,
            f"{P}_group_identifier_type_coding",
            f"{P}_pk",
            pk,
        ),
        "courseOfTherapyType": _cc_of(
            bind, "course_of_therapy_type_coding", pk, r["course_of_therapy_type_text"]
        ),
        "insurance": _refs(bind, r, "insurance"),
        "note": [_note(n) for n in _rows_of(bind, f"{P}_note", f"{P}_pk", pk)],
        "dosageInstruction": [
            _dosage(bind, d) for d in _rows_of(bind, f"{P}_dosage_instruction", f"{P}_pk", pk)
        ],
        "dispenseRequest": _dispense_request(r),
        "priorPrescription": _ref(r, "prior_prescription"),
        "detectedIssue": _refs(bind, r, "detected_issue"),
        "eventHistory": _refs(bind, r, "event_history"),
    }
    # reported[x]
    if r["reported_boolean"] is not None:
        content["reportedBoolean"] = r["reported_boolean"]
    else:
        content["reportedReference"] = _ref(r, "reported_reference")
    # medication[x]
    medication = _cc_of(bind, "medication_coding", pk, r["medication_codeable_concept_text"])
    if _prune(medication):
        content["medicationCodeableConcept"] = medication
    else:
        content["medicationReference"] = _ref(r, "medication_reference")
    # substitution.allowed[x]
    substitution = {
        "reason": _cc_of(bind, "substitution_reason_coding", pk, r["substitution_reason_text"]),
    }
    allowed = _cc_of(
        bind, "substitution_allowed_coding", pk, r["substitution_allowed_codeable_concept_text"]
    )
    if r["substitution_allowed_boolean"] is not None:
        substitution["allowedBoolean"] = r["substitution_allowed_boolean"]
    elif _prune(allowed):
        substitution["allowedCodeableConcept"] = allowed
    content["substitution"] = substitution
    return _prune(content)


def _backfill_content(bind):
    # status / intent / priority are enums: cast them to text so the driver returns the label.
    for r in _rows(
        bind,
        f"SELECT *, status::text AS status_text, intent::text AS intent_text, "
        f"priority::text AS priority_text FROM {P}",
    ):
        bind.execute(
            sa.text(f"UPDATE {P} SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, dict(r)), default=str), "id": r["id"]},
        )


# -- upgrade: content -> search index (frozen copy of _indexer.py) ---------------

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")
_SUBJECT_TYPES = ("Patient", "Group")
_REQUESTER_TYPES = ("Practitioner", "PractitionerRole", "Organization", "Patient", "RelatedPerson", "Device")
_PERFORMER_TYPES = (
    "Practitioner",
    "PractitionerRole",
    "Organization",
    "Patient",
    "Device",
    "RelatedPerson",
    "CareTeam",
)


def _typed(reference, allowed):
    match = _REF.match(reference or "")
    if match and match["type"] in allowed:
        return match["type"], int(match["id"])
    return None, None


def _ref_params(prefix, ref, allowed):
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    rtype, rid = _typed(reference, allowed)
    return {
        f"{prefix}_reference": reference,
        f"{prefix}_type": rtype,
        f"{prefix}_id": rid,
        f"{prefix}_identifier_system": identifier.get("system"),
        f"{prefix}_identifier_value": identifier.get("value"),
    }


def _insert_token(bind, pk, param, concept):
    if not concept:
        return
    text = _norm(concept.get("text"))
    codings = [c for c in concept.get("coding") or [] if c.get("system") or c.get("code") or c.get("display")]
    for c in codings or ([{}] if text else []):
        bind.execute(
            sa.text(
                f"INSERT INTO {P}_token ({P}_pk, param, system, code, display_norm, text_norm) "
                "VALUES (:pk, :param, :s, :c, :d, :t)"
            ),
            {"pk": pk, "param": param, "s": c.get("system"), "c": c.get("code"), "d": _norm(c.get("display")), "t": text},
        )


def _insert_identifier(bind, pk, identifier):
    if not (identifier.get("system") or identifier.get("value")):
        return
    itype = identifier.get("type") or {}
    for c in itype.get("coding") or [{}]:
        bind.execute(
            sa.text(
                f"INSERT INTO {P}_identifier ({P}_pk, system, value, type_system, type_code, type_text_norm, "
                "type_display_norm) VALUES (:pk, :s, :v, :ts, :tc, :tt, :td)"
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


def _rebuild_index(bind):
    for row in _rows(bind, f"SELECT id, content FROM {P}"):
        pk, doc = row["id"], _json(row["content"])
        authored_start, authored_end = _point(doc.get("authoredOn"))
        status, intent, priority = doc.get("status"), doc.get("intent"), doc.get("priority")
        columns = {
            "authored_start": authored_start,
            "authored_end": authored_end,
            **_ref_params("subject", doc.get("subject"), _SUBJECT_TYPES),
            **_ref_params("encounter", doc.get("encounter"), ("Encounter",)),
            **_ref_params("requester", doc.get("requester"), _REQUESTER_TYPES),
            **_ref_params("performer", doc.get("performer"), _PERFORMER_TYPES),
            **_ref_params("medication", doc.get("medicationReference"), ("Medication",)),
            **_ref_params(
                "dispenser", (doc.get("dispenseRequest") or {}).get("performer"), ("Organization",)
            ),
        }
        sets = ", ".join(f"{k} = :{k}" for k in columns)
        bind.execute(
            sa.text(
                f"UPDATE {P} SET status = CAST(:status AS medication_request_status), "
                f"intent = CAST(:intent AS medication_request_intent), "
                f"priority = CAST(:priority AS medication_request_priority), {sets} WHERE id = :pk"
            ),
            {
                **columns,
                "status": status if status in _STATUS else None,
                "intent": intent if intent in _INTENT else None,
                "priority": priority if priority in _PRIORITY else None,
                "pk": pk,
            },
        )
        for i in doc.get("identifier") or []:
            _insert_identifier(bind, pk, i)
        for category in doc.get("category") or []:
            _insert_token(bind, pk, "category", category)
        _insert_token(bind, pk, "code", doc.get("medicationCodeableConcept"))
        _insert_token(bind, pk, "intended-performertype", doc.get("performerType"))
        for dosage in doc.get("dosageInstruction") or []:
            for event in ((dosage or {}).get("timing") or {}).get("event") or []:
                start, end = _point(event)
                if start or end:
                    bind.execute(
                        sa.text(
                            f"INSERT INTO {P}_timing ({P}_pk, event_start, event_end) VALUES (:pk, :s, :e)"
                        ),
                        {"pk": pk, "s": start, "e": end},
                    )


# Main-table columns that survive unchanged: the id, the audit/tenant columns and the subject /
# encounter / requester / performer index columns (their reference-type enums become plain
# strings). The status, date, medication and dispenser columns are new.
_REF_PARTS = ("reference", "type", "id", "identifier_system", "identifier_value")
_KEEP = {
    "id",
    "medication_request_id",
    "tenant_id",
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
    "content",
    *(
        f"{prefix}_{part}"
        for prefix in ("subject", "encounter", "requester", "performer")
        for part in _REF_PARTS
    ),
}


def _fk():
    return sa.Column(f"{P}_pk", sa.BigInteger(), sa.ForeignKey(f"{P}.id"), nullable=False)


def _index(table, *columns):
    op.create_index(op.f("ix_" + table + "_" + columns[0]), table, list(columns))


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column(P, sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    _backfill_content(bind)

    # Every old child table (the prefix is unique to this resource).
    for (table,) in bind.execute(
        sa.text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema() "
            "AND table_name LIKE 'medication\\_request\\_%' AND table_type = 'BASE TABLE'"
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

    # The reference types were enums; they are plain strings now (the shared `subject_reference_type`
    # and `encounter_reference_type` enums stay for the other resources that use them).
    for prefix in ("subject", "encounter", "requester", "performer"):
        op.alter_column(
            P, f"{prefix}_type", type_=sa.String(), nullable=True, postgresql_using=f"{prefix}_type::text"
        )
    for (name,) in bind.execute(
        sa.text("SELECT typname FROM pg_type WHERE typtype = 'e' AND typname LIKE 'medication\\_request\\_%'")
    ).all():
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # Medication requests are searched by subject: one index on the pair instead of the lone id.
    op.execute(f"DROP INDEX IF EXISTS ix_{P}_subject_id")
    # The public id's sequence is now its server default.
    op.execute(
        f"ALTER TABLE {P} ALTER COLUMN medication_request_id SET DEFAULT nextval('medication_request_pub_seq')"
    )

    # The audit columns as the shared mixin declares them (the original table was created with
    # looser ones): tenant/actor NOT NULL, timestamps nullable and indexed.
    op.execute(f"UPDATE {P} SET tenant_id = '' WHERE tenant_id IS NULL")
    op.execute(f"UPDATE {P} SET created_by = '' WHERE created_by IS NULL")
    op.alter_column(P, "tenant_id", existing_type=sa.String(), nullable=False)
    op.alter_column(P, "created_by", existing_type=sa.String(), nullable=False)
    op.alter_column(P, "created_at", existing_type=sa.DateTime(timezone=True), nullable=True)
    op.alter_column(P, "updated_at", existing_type=sa.DateTime(timezone=True), nullable=True)
    for column in ("id", "tenant_id", "created_at", "updated_at"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)

    # status / intent / priority: recreated as enums holding the real FHIR codes.
    for name, values in (("status", _STATUS), ("intent", _INTENT), ("priority", _PRIORITY)):
        postgresql.ENUM(*values, name=f"{P}_{name}").create(bind, checkfirst=True)
        op.add_column(
            P,
            sa.Column(name, postgresql.ENUM(*values, name=f"{P}_{name}", create_type=False), nullable=True),
        )
    op.add_column(P, sa.Column("authored_start", sa.DateTime(timezone=True), nullable=True))
    op.add_column(P, sa.Column("authored_end", sa.DateTime(timezone=True), nullable=True))
    for prefix in ("medication", "dispenser"):
        op.add_column(P, sa.Column(f"{prefix}_reference", sa.String(), nullable=True))
        op.add_column(P, sa.Column(f"{prefix}_type", sa.String(), nullable=True))
        op.add_column(P, sa.Column(f"{prefix}_id", sa.BigInteger(), nullable=True))
        op.add_column(P, sa.Column(f"{prefix}_identifier_system", sa.String(), nullable=True))
        op.add_column(P, sa.Column(f"{prefix}_identifier_value", sa.String(), nullable=True))
        op.create_index(f"ix_{P}_{prefix}_id", P, [f"{prefix}_id"])
    op.create_index("ix_medication_request_authored", P, ["authored_start", "authored_end"])
    op.create_index("ix_medication_request_subject_type_id", P, ["subject_type", "subject_id"])

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
        sa.Column("system", sa.String(), nullable=True),
        sa.Column("code", sa.String(), nullable=True),
        sa.Column("display_norm", sa.String(), nullable=True),
        sa.Column("text_norm", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(f"{P}_token", f"{P}_pk")
    op.create_index("ix_medication_request_token_param_code", f"{P}_token", ["param", "code"])

    op.create_table(
        f"{P}_timing",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column("event_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("event_end", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(f"{P}_timing", f"{P}_pk")
    op.create_index("ix_medication_request_timing_event", f"{P}_timing", ["event_start", "event_end"])

    _rebuild_index(bind)
    op.alter_column(P, "content", nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "medication_request content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
