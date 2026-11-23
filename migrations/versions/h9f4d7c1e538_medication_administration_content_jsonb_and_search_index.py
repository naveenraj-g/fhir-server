"""medication_administration: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: h9f4d7c1e538
Revises: g8e3c6b0d427
Create Date: 2026-12-21 10:00:00.000000

Stores MedicationAdministration whole in `content` (see MedicationAdministrationModel's
docstring), like the other resources already moved (MedicationStatement g8e3c6b0d427,
MedicationRequest b5a0c7e3f149, ...). The whole FHIR resource - `instantiates`, `partOf`,
`statusReason`, `category`, `supportingInformation`, `performer` (with its function),
`reasonCode`, `reasonReference`, `device`, `note`, `dosage` and `eventHistory` - moves into
`medication_administration.content`; every column/table that survives is a search index for one
of the FHIR R4 MedicationAdministration search parameters (or `_id` / `_lastUpdated`), derived
from `content`:

  medication_administration: status (the Postgres enum already held the true FHIR codes, so it
      stays), effective_start/_end (new: the half-open range `effective[x]` covers - the old
      dateTime and period columns are dropped), the subject_*, context_*, medication_* and
      request_* columns (`*_type` become plain strings); the public id gets its sequence as a
      server default; new: content.
  medication_administration_identifier: rebuilt as an index table
  medication_administration_token: new - code, reason-given and reason-not-given
  medication_administration_reference: new - device and performer (performer.actor)
  dropped: every other child table, every main-table column with no search parameter (the
      dosage columns, instantiates, the category / medication CodeableConcept text, ...) and the
      per-field `medication_administration_*` reference-type enums.

upgrade: (1) builds `content` for every existing row from the old columns and tables - a frozen
copy of the old to_fhir_medication_administration() logic (but keeping a reference's raw string,
so an absolute URL is not lost), so this migration never depends on application code that has
since changed; (2) drops the old child tables/columns and creates the index tables; (3) rebuilds
the index from `content`.

downgrade: not supported. Everything the old schema held is preserved in `content`, but
rebuilding the old normalized tables from it is not implemented - restore from a backup taken
before upgrading.
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
revision: str = "h9f4d7c1e538"
down_revision: Union[str, None] = "g8e3c6b0d427"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

P = "medication_administration"

_STATUS = (
    "in-progress",
    "not-done",
    "on-hold",
    "completed",
    "entered-in-error",
    "stopped",
    "unknown",
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
        quantity["comparator"] = _COMPARATORS.get(
            str(g(f"{prefix}_comparator")).lower()
        )
    quantity = {k: v for k, v in quantity.items() if v is not None}
    return quantity or None


def _own_identifier(row, prefix, bind, type_table, type_fk, type_fk_value):
    """An Identifier carried either by a child row (prefix "") or flattened into the main row."""
    g = row.get
    return {
        "use": g(f"{prefix}use"),
        "type": _concept(
            _rows_of(bind, type_table, type_fk, type_fk_value), g(f"{prefix}type_text")
        ),
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
            _concept(
                _rows_of(bind, f"{P}_{table}_coding", f"{P}_{table}_id", row["id"]),
                row["text"],
            )
        )
    return out


def _cc_of(bind, table, pk, text):
    """A 0..1 CodeableConcept held as `<table>` codings (FK to the main row) + a text column."""
    return _concept(_rows_of(bind, f"{P}_{table}", f"{P}_pk", pk), text)


def _refs(bind, r, table):
    return [
        _ref(x, "reference") for x in _rows_of(bind, f"{P}_{table}", f"{P}_pk", r["id"])
    ]


def _note(n):
    note = {"time": _iso(n["time"]), "text": n["text"]}
    if n["author_string"]:
        note["authorString"] = n["author_string"]
    else:
        author = _prune(_ref(n, "author"))
        if author:
            note["authorReference"] = author
    return note


def _num_or_none(value):
    return float(value) if value is not None else None


def _q(row, prefix):
    """A Quantity from `{prefix}_value/_unit/_system/_code` (None when empty)."""
    quantity = {
        "value": _num_or_none(row.get(f"{prefix}_value")),
        "unit": row.get(f"{prefix}_unit"),
        "system": row.get(f"{prefix}_system"),
        "code": row.get(f"{prefix}_code"),
    }
    return {k: v for k, v in quantity.items() if v is not None} or None


def _dosage(bind, r):
    pk = r["id"]
    dosage = {
        "text": r["dosage_text"],
        "site": _cc_of(bind, "dosage_site_coding", pk, r["dosage_site_text"]),
        "route": _cc_of(bind, "dosage_route_coding", pk, r["dosage_route_text"]),
        "method": _cc_of(bind, "dosage_method_coding", pk, r["dosage_method_text"]),
        "dose": _q(r, "dosage_dose"),
    }
    numerator = _q(r, "dosage_rate_ratio_numerator")
    denominator = _q(r, "dosage_rate_ratio_denominator")
    if numerator or denominator:
        dosage["rateRatio"] = {"numerator": numerator, "denominator": denominator}
    else:
        dosage["rateQuantity"] = _q(r, "dosage_rate_quantity")
    return dosage


def _performers(bind, pk):
    out = []
    for p in _rows_of(bind, f"{P}_performer", f"{P}_pk", pk):
        out.append(
            {
                "function": _concept(
                    _rows_of(
                        bind,
                        f"{P}_performer_function_coding",
                        f"{P}_performer_id",
                        p["id"],
                    ),
                    p["function_text"],
                ),
                "actor": _ref(p, "actor"),
            }
        )
    return out


def _build_content(bind, r):
    pk = r["id"]
    content = {
        "extension": list(_json(r["extension"]) or []),
        "identifier": [
            _own_identifier(
                i,
                "",
                bind,
                f"{P}_identifier_type_coding",
                f"{P}_identifier_id",
                i["id"],
            )
            for i in _rows_of(bind, f"{P}_identifier", f"{P}_pk", pk)
        ],
        "instantiates": list(r["instantiates"] or []),
        "partOf": _refs(bind, r, "part_of"),
        "status": r["status_text"],
        "statusReason": _cc_list(bind, r, "status_reason"),
        "category": _cc_of(bind, "category_coding", pk, r["category_text"]),
        "subject": _ref(r, "subject"),
        "context": _ref(r, "context"),
        "supportingInformation": _refs(bind, r, "supporting_information"),
        "performer": _performers(bind, pk),
        "reasonCode": _cc_list(bind, r, "reason_code"),
        "reasonReference": _refs(bind, r, "reason_reference"),
        "request": _ref(r, "request"),
        "device": _refs(bind, r, "device"),
        "note": [_note(n) for n in _rows_of(bind, f"{P}_note", f"{P}_pk", pk)],
        "dosage": _dosage(bind, r),
        "eventHistory": _refs(bind, r, "event_history"),
    }
    # medication[x]
    medication = _cc_of(
        bind, "medication_coding", pk, r["medication_codeable_concept_text"]
    )
    if _prune(medication):
        content["medicationCodeableConcept"] = medication
    else:
        content["medicationReference"] = _ref(r, "medication")
    # effective[x]
    if r["effective_date_time"] is not None:
        content["effectiveDateTime"] = _iso(r["effective_date_time"])
    else:
        content["effectivePeriod"] = _period(
            r["effective_period_start"], r["effective_period_end"]
        )
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


# -- upgrade: content -> search index (frozen copy of _indexer.py) ---------------

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")
_SUBJECT_TYPES = ("Patient", "Group")
_CONTEXT_TYPES = ("Encounter", "EpisodeOfCare")
_MEDICATION_TYPES = ("Medication",)
_REQUEST_TYPES = ("MedicationRequest",)
_REFERENCE_TYPES = {
    "device": ("Device",),
    "performer": (
        "Practitioner",
        "PractitionerRole",
        "Patient",
        "RelatedPerson",
        "Device",
    ),
}


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
    codings = [
        c
        for c in concept.get("coding") or []
        if c.get("system") or c.get("code") or c.get("display")
    ]
    for c in codings or ([{}] if text else []):
        bind.execute(
            sa.text(
                f"INSERT INTO {P}_token ({P}_pk, param, system, code, display_norm, text_norm) "
                "VALUES (:pk, :param, :s, :c, :d, :t)"
            ),
            {
                "pk": pk,
                "param": param,
                "s": c.get("system"),
                "c": c.get("code"),
                "d": _norm(c.get("display")),
                "t": text,
            },
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


def _insert_reference(bind, pk, param, ref):
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return
    rtype, rid = _typed(reference, _REFERENCE_TYPES[param])
    bind.execute(
        sa.text(
            f"INSERT INTO {P}_reference ({P}_pk, param, reference_reference, reference_type, "
            "reference_id, reference_identifier_system, reference_identifier_value) "
            "VALUES (:pk, :param, :r, :t, :i, :s, :v)"
        ),
        {
            "pk": pk,
            "param": param,
            "r": reference,
            "t": rtype,
            "i": rid,
            "s": identifier.get("system"),
            "v": identifier.get("value"),
        },
    )


def _rebuild_index(bind):
    for row in _rows(bind, f"SELECT id, content FROM {P}"):
        pk, doc = row["id"], _json(row["content"])
        if doc.get("effectiveDateTime"):
            effective_start, effective_end = _bounds(doc["effectiveDateTime"])
        else:
            period = doc.get("effectivePeriod") or {}
            effective_start = _bounds(period.get("start"))[0]
            effective_end = _bounds(period.get("end"))[1]
        status = doc.get("status")
        columns = {
            "effective_start": effective_start,
            "effective_end": effective_end,
            **_ref_params("subject", doc.get("subject"), _SUBJECT_TYPES),
            **_ref_params("context", doc.get("context"), _CONTEXT_TYPES),
            **_ref_params(
                "medication", doc.get("medicationReference"), _MEDICATION_TYPES
            ),
            **_ref_params("request", doc.get("request"), _REQUEST_TYPES),
        }
        sets = ", ".join(f"{k} = :{k}" for k in columns)
        bind.execute(
            sa.text(
                f"UPDATE {P} SET status = CAST(:status AS medication_administration_status), {sets} "
                "WHERE id = :pk"
            ),
            {**columns, "status": status if status in _STATUS else None, "pk": pk},
        )
        for i in doc.get("identifier") or []:
            _insert_identifier(bind, pk, i)
        _insert_token(bind, pk, "code", doc.get("medicationCodeableConcept"))
        for concept in doc.get("reasonCode") or []:
            _insert_token(bind, pk, "reason-given", concept)
        for concept in doc.get("statusReason") or []:
            _insert_token(bind, pk, "reason-not-given", concept)
        for ref in doc.get("device") or []:
            _insert_reference(bind, pk, "device", ref)
        for performer in doc.get("performer") or []:
            _insert_reference(bind, pk, "performer", (performer or {}).get("actor"))


# Main-table columns that survive unchanged: the id, the audit/tenant columns, the status (an
# enum that already held the true FHIR codes) and the subject / context / medication / request
# index columns (their reference-type enums become plain strings). The effective columns are new.
_REF_PARTS = ("reference", "type", "id", "identifier_system", "identifier_value")
_KEEP = {
    "id",
    "medication_administration_id",
    "tenant_id",
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
    "content",
    "status",
    *(
        f"{prefix}_{part}"
        for prefix in ("subject", "context", "medication", "request")
        for part in _REF_PARTS
    ),
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

    # Every old child table (the prefix is unique to this resource).
    for (table,) in bind.execute(
        sa.text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema() "
            "AND table_name LIKE 'medication\\_administration\\_%' AND table_type = 'BASE TABLE'"
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

    # The reference types were enums; they are plain strings now. subject was NOT NULL: R4
    # requires it, but that is the validator's job, not an index column's.
    for prefix in ("subject", "context", "medication", "request"):
        op.alter_column(
            P,
            f"{prefix}_type",
            type_=sa.String(),
            nullable=True,
            postgresql_using=f"{prefix}_type::text",
        )
    op.alter_column(P, "subject_reference", existing_type=sa.String(), nullable=True)
    # Every per-field `medication_administration_*` enum of the old schema except the status.
    for (name,) in bind.execute(
        sa.text(
            "SELECT typname FROM pg_type WHERE typtype = 'e' AND typname LIKE 'medication\\_administration\\_%' "
            "AND typname <> 'medication_administration_status'"
        )
    ).all():
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # Administrations are searched by subject: one index on the pair instead of the lone id.
    op.execute(f"DROP INDEX IF EXISTS ix_{P}_subject_id")
    # The public id's sequence is now its server default.
    op.execute(
        f"ALTER TABLE {P} ALTER COLUMN medication_administration_id SET DEFAULT nextval('medication_administration_pub_seq')"
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
        f"ALTER TABLE {P} DROP CONSTRAINT IF EXISTS medication_administration_medication_administration_id_key"
    )
    for column in ("id", "tenant_id", "created_at", "updated_at"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)

    # status: the enum stays; the column is nullable now (an index, not a requirement).
    op.alter_column(
        P,
        "status",
        existing_type=postgresql.ENUM(
            *_STATUS, name="medication_administration_status", create_type=False
        ),
        nullable=True,
    )
    op.add_column(
        P, sa.Column("effective_start", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        P, sa.Column("effective_end", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index(
        "ix_medication_administration_effective",
        P,
        ["effective_start", "effective_end"],
    )
    op.create_index(
        "ix_medication_administration_subject_type_id",
        P,
        ["subject_type", "subject_id"],
    )

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
    op.create_index(
        "ix_medication_administration_token_param_code", f"{P}_token", ["param", "code"]
    )

    op.create_table(
        f"{P}_reference",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column("param", sa.String(), nullable=False),
        sa.Column("reference_reference", sa.String(), nullable=True),
        sa.Column("reference_type", sa.String(), nullable=True),
        sa.Column("reference_id", sa.BigInteger(), nullable=True),
        sa.Column("reference_identifier_system", sa.String(), nullable=True),
        sa.Column("reference_identifier_value", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(f"{P}_reference", f"{P}_pk")
    op.create_index(
        "ix_medication_administration_reference_param_type_id",
        f"{P}_reference",
        ["param", "reference_type", "reference_id"],
    )

    _rebuild_index(bind)
    op.create_index(
        "ix_medication_administration_status", P, ["status"], if_not_exists=True
    )
    for column in ("context_id", "medication_id", "request_id"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)
    op.create_index(
        "ix_medication_administration_medication_administration_id",
        P,
        ["medication_administration_id"],
        unique=True,
        if_not_exists=True,
    )
    op.alter_column(P, "content", nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "medication_administration content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
