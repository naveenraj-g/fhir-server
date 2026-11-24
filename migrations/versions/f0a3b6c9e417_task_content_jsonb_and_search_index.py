"""task: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: f0a3b6c9e417
Revises: e9f2a5b8d306
Create Date: 2026-12-23 14:00:00.000000

Stores Task whole in `content` (see TaskModel's docstring), like the other resources already moved
(Goal e9f2a5b8d306, MedicationKnowledge d8e1f4a7c295, CarePlan e8d3f0b6c472, ...). The whole FHIR
resource - `identifier`, `instantiates*`, `basedOn`, `groupIdentifier`, `partOf`, `statusReason`,
`businessStatus`, `code`, `description`, `focus`, `for`, `encounter`, `executionPeriod`,
`authoredOn`, `lastModified`, `requester`, `performerType`, `owner`, `location`, `reasonCode`,
`reasonReference`, `insurance`, `note`, `relevantHistory`, `restriction`, `input`, `output` and
`extension` - moves into `task.content`; every column/table that survives is a search index for one
of the FHIR R4 Task search parameters (or `_id` / `_lastUpdated`), derived from `content`:

  task: status / intent / priority (the Postgres enums already held the true FHIR codes, so they
      stay, now nullable), authored_*, modified_* and period_* (new: the range each date covers -
      the old instants are dropped), group_identifier_system/_value, and the for_*, focus_*,
      encounter_*, requester_* and owner_* reference columns (`*_type` becomes a plain string); the
      public id gets its sequence as a server default; new: content.
  task_identifier: rebuilt as an index table
  task_token: new - business-status, code and performer
  task_reference: new - based-on and part-of
  dropped: every other child table, every main-table column with no search parameter and the
      per-field `task_*` reference-type enums (the status, intent and priority enums stay).

upgrade: (1) builds `content` for every existing row from the old columns and tables - a frozen
copy of the old to_fhir_task() logic (but keeping a reference's raw string, so an absolute URL is
not lost), so this migration never depends on application code that has since changed; (2) drops
the old child tables/columns and creates the index tables; (3) rebuilds the index from `content`.

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
revision: str = "f0a3b6c9e417"
down_revision: Union[str, None] = "e9f2a5b8d306"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

P = "task"

_STATUS = (
    "draft",
    "requested",
    "received",
    "accepted",
    "rejected",
    "ready",
    "cancelled",
    "in-progress",
    "on-hold",
    "failed",
    "completed",
    "entered-in-error",
)
_INTENT = (
    "unknown",
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


def _period_bounds(period):
    """Frozen copy of app.repository._content_index.period_bounds: (first instant covered, first
    instant after), NULL = open."""
    period = period or {}
    low = _bounds(period.get("start"))[0]
    high = _bounds(period.get("end"))[1]
    return low, high


# -- upgrade: old columns/tables -> content (frozen copy of the old mapper) ------


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


def _own_identifier(bind, i):
    return {
        "use": i["use"],
        "type": _concept(
            _rows_of(
                bind, "task_identifier_type_coding", "task_identifier_id", i["id"]
            ),
            i["type_text"],
        ),
        "system": i["system"],
        "value": i["value"],
        "period": _period(i["period_start"], i["period_end"]),
        "assigner": _ref(i, "assigner"),
    }


def _note(n):
    note = {"time": _iso(n["time"]), "text": n["text"]}
    if n["author_string"]:
        note["authorString"] = n["author_string"]
    else:
        author = _prune(_ref(n, "author"))
        if author:
            note["authorReference"] = author
    return note


def _io(bind, row, table):
    """One input / output entry: the type and the first populated `value[x]` column, then whatever
    `value_json` held (the complex choices)."""
    entry = {
        "type": _concept(
            _rows_of(bind, f"{table}_type_coding", f"{table}_id", row["id"]),
            row["type_text"],
        )
    }
    scalars = (
        ("valueString", "value_string", lambda v: v),
        ("valueBoolean", "value_boolean", lambda v: v),
        ("valueInteger", "value_integer", lambda v: v),
        ("valueDecimal", "value_decimal", float),
        ("valueDate", "value_date", _iso),
        ("valueDateTime", "value_date_time", _iso),
        ("valueTime", "value_time", str),
        ("valueUri", "value_uri", lambda v: v),
        ("valueCode", "value_code", lambda v: v),
    )
    for key, column, convert in scalars:
        if row[column] is not None:
            entry[key] = convert(row[column])
            break
    else:
        reference = _prune(_ref(row, "value_reference"))
        if reference:
            entry["valueReference"] = reference
    extra = _json(row["value_json"])
    if isinstance(extra, dict):
        entry.update(extra)
    return entry


def _build_content(bind, r):
    pk = r["id"]

    def by_pk(table):
        return _rows_of(bind, f"{P}_{table}", f"{P}_pk", pk)

    def cc(coding_table, text):
        return _concept(by_pk(coding_table), text)

    content = {
        "extension": list(_json(r["extension"]) or []),
        "identifier": [_own_identifier(bind, i) for i in by_pk("identifier")],
        "instantiatesCanonical": r["instantiates_canonical"],
        "instantiatesUri": r["instantiates_uri"],
        "basedOn": [_ref(x, "reference") for x in by_pk("based_on")],
        "groupIdentifier": {
            "use": r["group_identifier_use"],
            "system": r["group_identifier_system"],
            "value": r["group_identifier_value"],
            "period": _period(
                r["group_identifier_period_start"], r["group_identifier_period_end"]
            ),
            "assigner": _ref(r, "group_identifier_assigner"),
        },
        "partOf": [_ref(x, "reference") for x in by_pk("part_of")],
        "status": r["status_text"],
        "statusReason": cc("status_reason_coding", r["status_reason_text"]),
        "businessStatus": cc("business_status_coding", r["business_status_text"]),
        "intent": r["intent_text"],
        "priority": r["priority_text"],
        "code": cc("code_coding", r["code_text"]),
        "description": r["description"],
        "focus": _ref(r, "focus"),
        "for": _ref(r, "for"),
        "encounter": _ref(r, "encounter"),
        "executionPeriod": _period(
            r["execution_period_start"], r["execution_period_end"]
        ),
        "authoredOn": _iso(r["authored_on"]),
        "lastModified": _iso(r["last_modified"]),
        "requester": _ref(r, "requester"),
        "performerType": [
            _concept(
                _rows_of(
                    bind,
                    f"{P}_performer_type_coding",
                    f"{P}_performer_type_id",
                    pt["id"],
                ),
                pt["text"],
            )
            for pt in by_pk("performer_type")
        ],
        "owner": _ref(r, "owner"),
        "location": _ref(r, "location"),
        "reasonCode": cc("reason_code_coding", r["reason_code_text"]),
        "reasonReference": _ref(r, "reason_reference"),
        "insurance": [_ref(x, "reference") for x in by_pk("insurance")],
        "note": [_note(n) for n in by_pk("note")],
        "relevantHistory": [_ref(x, "reference") for x in by_pk("relevant_history")],
        "restriction": {
            "repetitions": r["restriction_repetitions"],
            "period": _period(
                r["restriction_period_start"], r["restriction_period_end"]
            ),
            "recipient": [_ref(x, "reference") for x in by_pk("restriction_recipient")],
        },
        "input": [_io(bind, x, f"{P}_input") for x in by_pk("input")],
        "output": [_io(bind, x, f"{P}_output") for x in by_pk("output")],
    }
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
            {
                "c": json.dumps(_build_content(bind, dict(r)), default=str),
                "id": r["id"],
            },
        )


# -- upgrade: content -> search index (frozen copy of _indexer.py) ---------------

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")
_ENCOUNTER_TYPES = ("Encounter",)
_REQUESTER_TYPES = (
    "Device",
    "Organization",
    "Patient",
    "Practitioner",
    "PractitionerRole",
    "RelatedPerson",
)
_OWNER_TYPES = (
    "Practitioner",
    "PractitionerRole",
    "Organization",
    "CareTeam",
    "HealthcareService",
    "Patient",
    "Device",
    "RelatedPerson",
)
_PART_OF_TYPES = ("Task",)


def _typed(reference, allowed):
    """allowed None = a Reference(Any): any relative `Type/<id>` names a type."""
    match = _REF.match(reference or "")
    if match and (allowed is None or match["type"] in allowed):
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
    if not isinstance(concept, dict):
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


def _insert_reference(bind, pk, param, ref):
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return
    rtype, rid = _typed(reference, None if param == "based-on" else _PART_OF_TYPES)
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


def _range(value):
    return _bounds(value) if isinstance(value, str) and value else (None, None)


def _rebuild_index(bind):
    for row in _rows(bind, f"SELECT id, content FROM {P}"):
        pk, doc = row["id"], _json(row["content"])
        authored = _range(doc.get("authoredOn"))
        modified = _range(doc.get("lastModified"))
        period = _period_bounds(
            doc.get("executionPeriod")
            if isinstance(doc.get("executionPeriod"), dict)
            else None
        )
        group = doc.get("groupIdentifier") or {}
        status, intent, priority = (
            doc.get("status"),
            doc.get("intent"),
            doc.get("priority"),
        )
        columns = {
            "authored_start": authored[0],
            "authored_end": authored[1],
            "modified_start": modified[0],
            "modified_end": modified[1],
            "period_start": period[0],
            "period_end": period[1],
            "group_identifier_system": group.get("system"),
            "group_identifier_value": group.get("value"),
            **_ref_params("for", doc.get("for"), None),
            **_ref_params("focus", doc.get("focus"), None),
            **_ref_params("encounter", doc.get("encounter"), _ENCOUNTER_TYPES),
            **_ref_params("requester", doc.get("requester"), _REQUESTER_TYPES),
            **_ref_params("owner", doc.get("owner"), _OWNER_TYPES),
        }
        sets = ", ".join(f"{k} = :{k}" for k in columns)
        bind.execute(
            sa.text(
                f"UPDATE {P} SET status = CAST(:status AS task_status), "
                f"intent = CAST(:intent AS task_intent), "
                f"priority = CAST(:priority AS task_priority), {sets} WHERE id = :pk"
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
        _insert_token(bind, pk, "business-status", doc.get("businessStatus"))
        _insert_token(bind, pk, "code", doc.get("code"))
        for concept in doc.get("performerType") or []:
            _insert_token(bind, pk, "performer", concept)
        for ref in doc.get("basedOn") or []:
            _insert_reference(bind, pk, "based-on", ref)
        for ref in doc.get("partOf") or []:
            _insert_reference(bind, pk, "part-of", ref)


# Main-table columns that survive unchanged: the id, the audit/tenant columns, the status / intent
# / priority (enums that already held the true FHIR codes) and the encounter / requester / owner /
# for / focus index columns (their reference-type enums become plain strings). The date and
# group-identifier columns are new.
_REF_PARTS = ("reference", "type", "id", "identifier_system", "identifier_value")
_KEEP = {
    "id",
    "task_id",
    "tenant_id",
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
    "content",
    "status",
    "intent",
    "priority",
    "group_identifier_system",
    "group_identifier_value",
    *(
        f"{prefix}_{part}"
        for prefix in ("for", "focus", "encounter", "requester", "owner")
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
            "AND table_name LIKE 'task\\_%' AND table_type = 'BASE TABLE'"
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
    # The group identifier's system / value stay (new content-derived columns of the same name
    # are re-filled below); every other old column goes.
    for column in existing:
        if column not in _KEEP:
            op.drop_column(P, column)

    # The reference types were enums; they are plain strings now.
    for prefix in ("encounter", "requester", "owner"):
        op.alter_column(
            P,
            f"{prefix}_type",
            type_=sa.String(),
            nullable=True,
            postgresql_using=f"{prefix}_type::text",
        )
    # Every per-field `task_*` enum of the old schema except the status, intent and priority.
    for (name,) in bind.execute(
        sa.text(
            "SELECT typname FROM pg_type WHERE typtype = 'e' AND typname LIKE 'task\\_%' "
            "AND typname NOT IN ('task_status', 'task_intent', 'task_priority')"
        )
    ).all():
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # The `for` and `focus` ids were indexed alone; `for` is searched by type and id.
    op.execute(f"DROP INDEX IF EXISTS ix_{P}_for_id")
    # The public id's sequence is now its server default.
    op.execute(
        f"ALTER TABLE {P} ALTER COLUMN task_id SET DEFAULT nextval('task_pub_seq')"
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
    op.execute(f"ALTER TABLE {P} DROP CONSTRAINT IF EXISTS task_task_id_key")
    for column in ("id", "tenant_id", "created_at", "updated_at"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)

    # status / intent / priority: the enums stay; the columns are nullable (an index, not a
    # requirement).
    for column, name, labels in (
        ("status", "task_status", _STATUS),
        ("intent", "task_intent", _INTENT),
        ("priority", "task_priority", _PRIORITY),
    ):
        op.alter_column(
            P,
            column,
            existing_type=postgresql.ENUM(*labels, name=name, create_type=False),
            nullable=True,
        )
    # group_identifier_* were kept as columns; they are nullable already.
    for column in (
        "authored_start",
        "authored_end",
        "modified_start",
        "modified_end",
        "period_start",
        "period_end",
    ):
        op.add_column(P, sa.Column(column, sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_task_authored", P, ["authored_start", "authored_end"])
    op.create_index("ix_task_modified", P, ["modified_start", "modified_end"])
    op.create_index("ix_task_period", P, ["period_start", "period_end"])
    op.create_index("ix_task_for_type_id", P, ["for_type", "for_id"])

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
    op.create_index("ix_task_token_param_code", f"{P}_token", ["param", "code"])

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
        "ix_task_reference_param_type_id",
        f"{P}_reference",
        ["param", "reference_type", "reference_id"],
    )

    _rebuild_index(bind)
    op.create_index("ix_task_status", P, ["status"], if_not_exists=True)
    for column in ("focus_id", "encounter_id", "requester_id", "owner_id"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)
    op.create_index("ix_task_task_id", P, ["task_id"], unique=True, if_not_exists=True)
    op.alter_column(P, "content", nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "task content/index migration is one-way: its old normalized tables are not rebuilt "
        "from `content`. Restore from a backup taken before upgrading."
    )
