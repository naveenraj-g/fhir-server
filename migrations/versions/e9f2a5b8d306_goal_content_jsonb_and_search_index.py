"""goal: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: e9f2a5b8d306
Revises: d8e1f4a7c295
Create Date: 2026-12-23 12:00:00.000000

Stores Goal whole in `content` (see GoalModel's docstring), like the other resources already moved
(MedicationKnowledge d8e1f4a7c295, MedicationDispense i0a5e8d2f649, CarePlan e8d3f0b6c472, ...).
The whole FHIR resource - `identifier`, `achievementStatus`, `category`, `priority`,
`description`, `start[x]`, `target`, `statusDate`, `statusReason`, `expressedBy`, `addresses`,
`note`, `outcomeCode`, `outcomeReference` and `extension` - moves into `goal.content`; every
column/table that survives is a search index for one of the FHIR R4 Goal search parameters (or
`_id` / `_lastUpdated`), derived from `content`:

  goal: lifecycle_status (the Postgres enum already held the true FHIR codes, so it stays, now
      nullable), start_start/_end (new: the range `startDate` covers), the subject_* columns
      (`subject_type` becomes a plain string); the public id gets its sequence as a server
      default; new: content.
  goal_identifier: rebuilt as an index table
  goal_token: new - achievement-status and category
  goal_target: rebuilt as an index table - one row per target with a `dueDate`
  dropped: every other child table, every main-table column with no search parameter and the
      per-field `goal_*` reference-type enums (the lifecycle-status enum stays).

upgrade: (1) builds `content` for every existing row from the old columns and tables - a frozen
copy of the old to_fhir_goal() logic (but keeping a reference's raw string, so an absolute URL is
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
revision: str = "e9f2a5b8d306"
down_revision: Union[str, None] = "d8e1f4a7c295"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

P = "goal"

_STATUS = (
    "proposed",
    "planned",
    "accepted",
    "active",
    "on-hold",
    "completed",
    "cancelled",
    "entered-in-error",
    "rejected",
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


def _num(value):
    return float(value) if value is not None else None


def _quantity(row, prefix):
    """A Quantity from `{prefix}_value/_unit/_system/_code` (+ `_comparator` when stored)."""
    g = row.get
    quantity = {
        "value": _num(g(f"{prefix}_value")),
        "unit": g(f"{prefix}_unit"),
        "system": g(f"{prefix}_system"),
        "code": g(f"{prefix}_code"),
        "comparator": g(f"{prefix}_comparator"),
    }
    quantity = {k: v for k, v in quantity.items() if v is not None}
    return quantity or None


def _own_identifier(bind, i):
    return {
        "use": i["use"],
        "type": _concept(
            _rows_of(
                bind, "goal_identifier_type_coding", "goal_identifier_id", i["id"]
            ),
            i["type_text"],
        ),
        "system": i["system"],
        "value": i["value"],
        "period": _period(i["period_start"], i["period_end"]),
        "assigner": _ref(i, "assigner"),
    }


def _cc_list(bind, table, coding_table, coding_fk, pk):
    """A 0..* CodeableConcept held as `<table>` (text) + `<coding_table>`."""
    return [
        _concept(_rows_of(bind, coding_table, coding_fk, row["id"]), row["text"])
        for row in _rows_of(bind, table, "goal_pk", pk)
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


def _target(bind, t):
    tid = t["id"]
    entry = {
        "measure": _concept(
            _rows_of(bind, "goal_target_measure_coding", "goal_target_id", tid),
            t["measure_text"],
        ),
        "detailQuantity": _quantity(t, "detail_quantity"),
        "detailRange": {
            "low": _quantity(t, "detail_range_low"),
            "high": _quantity(t, "detail_range_high"),
        },
        "detailString": t["detail_string"],
        "detailBoolean": t["detail_boolean"],
        "detailInteger": t["detail_integer"],
        "detailRatio": {
            "numerator": _quantity(t, "detail_ratio_numerator"),
            "denominator": _quantity(t, "detail_ratio_denominator"),
        },
        "dueDate": _iso(t["due_date"]),
        "dueDuration": _quantity(t, "due_duration"),
    }
    detail = _concept(
        _rows_of(bind, "goal_target_detail_coding", "goal_target_id", tid),
        t["detail_codeable_concept_text"],
    )
    if _prune(detail):
        entry["detailCodeableConcept"] = detail
    return entry


def _build_content(bind, r):
    pk = r["id"]

    def by_pk(table):
        return _rows_of(bind, f"{P}_{table}", f"{P}_pk", pk)

    content = {
        "extension": list(_json(r["extension"]) or []),
        "identifier": [_own_identifier(bind, i) for i in by_pk("identifier")],
        "lifecycleStatus": r["status_text"],
        "achievementStatus": _concept(
            by_pk("achievement_status_coding"), r["achievement_status_text"]
        ),
        "category": _cc_list(
            bind, "goal_category", "goal_category_coding", "goal_category_id", pk
        ),
        "priority": _concept(by_pk("priority_coding"), r["priority_text"]),
        "description": _concept(by_pk("description_coding"), r["description_text"]),
        "subject": _ref(r, "subject"),
        "startDate": _iso(r["start_date"]),
        "target": [_target(bind, t) for t in by_pk("target")],
        "statusDate": _iso(r["status_date"]),
        "statusReason": r["status_reason"],
        "expressedBy": _ref(r, "expressed_by"),
        "addresses": [_ref(a, "reference") for a in by_pk("addresses")],
        "note": [_note(n) for n in by_pk("note")],
        "outcomeCode": _cc_list(
            bind,
            "goal_outcome_code",
            "goal_outcome_code_coding",
            "goal_outcome_code_id",
            pk,
        ),
        "outcomeReference": [_ref(o, "reference") for o in by_pk("outcome_reference")],
    }
    start = _concept(by_pk("start_coding"), r["start_codeable_concept_text"])
    if r["start_date"] is None and _prune(start):
        content["startCodeableConcept"] = start
    return _prune(content)


def _backfill_content(bind):
    # `lifecycle_status` is an enum: cast it to text so the driver returns the label.
    for r in _rows(bind, f"SELECT *, lifecycle_status::text AS status_text FROM {P}"):
        bind.execute(
            sa.text(f"UPDATE {P} SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {
                "c": json.dumps(_build_content(bind, dict(r)), default=str),
                "id": r["id"],
            },
        )


# -- upgrade: content -> search index (frozen copy of _indexer.py) ---------------

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")
_SUBJECT_TYPES = ("Patient", "Group", "Organization")


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


def _rebuild_index(bind):
    for row in _rows(bind, f"SELECT id, content FROM {P}"):
        pk, doc = row["id"], _json(row["content"])
        start = _bounds(doc.get("startDate"))
        status = doc.get("lifecycleStatus")
        columns = {
            "start_start": start[0],
            "start_end": start[1],
            **_ref_params("subject", doc.get("subject"), _SUBJECT_TYPES),
        }
        sets = ", ".join(f"{k} = :{k}" for k in columns)
        bind.execute(
            sa.text(
                f"UPDATE {P} SET lifecycle_status = CAST(:status AS goal_lifecycle_status), {sets} "
                "WHERE id = :pk"
            ),
            {**columns, "status": status if status in _STATUS else None, "pk": pk},
        )
        for i in doc.get("identifier") or []:
            _insert_identifier(bind, pk, i)
        _insert_token(bind, pk, "achievement-status", doc.get("achievementStatus"))
        for concept in doc.get("category") or []:
            _insert_token(bind, pk, "category", concept)
        for target in doc.get("target") or []:
            low, high = _bounds((target or {}).get("dueDate"))
            if low is not None:
                bind.execute(
                    sa.text(
                        f"INSERT INTO {P}_target ({P}_pk, due_start, due_end) "
                        "VALUES (:pk, :s, :e)"
                    ),
                    {"pk": pk, "s": low, "e": high},
                )


# Main-table columns that survive unchanged: the id, the audit/tenant columns, the lifecycle
# status (an enum that already held the true FHIR codes) and the subject index columns (the
# reference-type enum becomes a plain string). The start range columns are new.
_KEEP = {
    "id",
    "goal_id",
    "tenant_id",
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
    "content",
    "lifecycle_status",
    "subject_reference",
    "subject_type",
    "subject_id",
    "subject_identifier_system",
    "subject_identifier_value",
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
            "AND table_name LIKE 'goal\\_%' AND table_type = 'BASE TABLE'"
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

    # The subject's reference type was an enum; it is a plain string now.
    op.alter_column(
        P,
        "subject_type",
        type_=sa.String(),
        nullable=True,
        postgresql_using="subject_type::text",
    )
    op.alter_column(P, "subject_reference", existing_type=sa.String(), nullable=True)
    # Every per-field `goal_*` enum of the old schema except the lifecycle status.
    for (name,) in bind.execute(
        sa.text(
            "SELECT typname FROM pg_type WHERE typtype = 'e' AND typname LIKE 'goal\\_%' "
            "AND typname <> 'goal_lifecycle_status'"
        )
    ).all():
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # Goals are searched by subject: one index on the pair instead of the lone id.
    op.execute(f"DROP INDEX IF EXISTS ix_{P}_subject_id")
    # The public id's sequence is now its server default.
    op.execute(
        f"ALTER TABLE {P} ALTER COLUMN goal_id SET DEFAULT nextval('goal_pub_seq')"
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
    op.execute(f"ALTER TABLE {P} DROP CONSTRAINT IF EXISTS goal_goal_id_key")
    for column in ("id", "tenant_id", "created_at", "updated_at"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)

    # lifecycle_status: the enum stays; the column is nullable (an index, not a requirement).
    op.alter_column(
        P,
        "lifecycle_status",
        existing_type=postgresql.ENUM(
            *_STATUS, name="goal_lifecycle_status", create_type=False
        ),
        nullable=True,
    )
    op.add_column(
        P, sa.Column("start_start", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(P, sa.Column("start_end", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_goal_start", P, ["start_start", "start_end"])
    op.create_index("ix_goal_subject_type_id", P, ["subject_type", "subject_id"])

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
    op.create_index("ix_goal_token_param_code", f"{P}_token", ["param", "code"])

    op.create_table(
        f"{P}_target",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column("due_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_end", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(f"{P}_target", f"{P}_pk")
    op.create_index("ix_goal_target_due", f"{P}_target", ["due_start", "due_end"])

    _rebuild_index(bind)
    op.create_index(
        "ix_goal_lifecycle_status", P, ["lifecycle_status"], if_not_exists=True
    )
    op.create_index("ix_goal_goal_id", P, ["goal_id"], unique=True, if_not_exists=True)
    op.alter_column(P, "content", nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "goal content/index migration is one-way: its old normalized tables are not rebuilt "
        "from `content`. Restore from a backup taken before upgrading."
    )
