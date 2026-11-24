"""measure_report: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: f1b4c7d0e529
Revises: c9d2e5f8a306
Create Date: 2026-12-26 10:00:00.000000

Stores MeasureReport whole in `content` (see MeasureReportModel's docstring), like the other
resources already moved (Measure c9d2e5f8a306, QuestionnaireResponse e6c1a4f8b215, ...). The whole
FHIR resource - including the `group` tree (populations, stratifiers, strata, components, scores)
- moves into `measure_report.content`; every column/table that survives is a search index for one
of the FHIR R4 MeasureReport search parameters (or `_id` / `_lastUpdated`), derived from `content`:

  measure_report: status (the enum already held the real FHIR codes, so it stays), date_start/_end
      (new: the range the `date` dateTime covers; the old `date` instant is dropped),
      period_start/_end (rebuilt from `content`), the subject_* and reporter_* columns (`*_type`
      become plain strings); the public id gets its sequence as a server default; new: content.
  measure_report_identifier: rebuilt as an index table
  measure_report_reference: new - measure (the canonical URL) and evaluated-resource
  dropped: the group / population / stratifier / stratum / component tables, the improvement
      notation coding, evaluated-resource and identifier type-coding tables, every main-table
      column with no search parameter (type, measure, improvement notation, extension and the
      display / logical-identifier details of every reference) and the per-field
      `measure_report_*` enums (`measure_report_status` stays).

upgrade: (1) builds `content` for every existing row from the old columns and tables - a frozen
copy of the old to_fhir_measure_report() logic, so this migration never depends on application code
that has since changed; (2) drops the old child tables/columns and creates the index tables; (3)
rebuilds the index from `content`.

downgrade: not supported. Everything the old schema held is preserved in `content`, but rebuilding
the old normalized tables from it is not implemented - restore from a backup taken before
upgrading.
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
revision: str = "f1b4c7d0e529"
down_revision: Union[str, None] = "c9d2e5f8a306"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

P = "measure_report"

_STATUS = ("complete", "pending", "error")
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


def _hyphenate(old):
    """The FHIR code for an old enum label (`subject_list` becomes `subject-list`)."""
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


def _period_bounds(period):
    """Half-open [start, end) range a Period covers; NULL = open (frozen copy of
    app.repository._content_index.period_bounds)."""
    period = period or {}
    start = _bounds(period.get("start"))[0] if period.get("start") else None
    end = _bounds(period.get("end"))[1] if period.get("end") else None
    return start, end


# -- upgrade: old columns/tables -> content (frozen copy of the old mapper) -----------------

_TYPE_NAMES = {
    t.upper(): t
    for t in (
        "Patient",
        "Practitioner",
        "PractitionerRole",
        "RelatedPerson",
        "Organization",
        "Device",
        "Location",
        "Group",
        "List",
    )
}


def _coding(c):
    return {
        "system": c["system"],
        "version": c["version"],
        "code": c["code"],
        "display": c["display"],
        "userSelected": c["user_selected"],
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


def _rows_of(bind, table, fk, value):
    return _rows(bind, f"SELECT * FROM {table} WHERE {fk} = :v ORDER BY id", v=value)


def _num(value):
    return float(value) if isinstance(value, Decimal) else value


def _concept(bind, table, fk, value, text):
    """A CodeableConcept from a coding table and a text column."""
    return {
        "coding": [_coding(c) for c in _rows_of(bind, table, fk, value)],
        "text": text,
    }


def _score(r):
    """The Quantity held as measure_score_* columns (comparator read as text)."""
    return {
        "value": _num(r["measure_score_value"]),
        "comparator": _COMPARATOR.get(r["comparator_text"], r["comparator_text"]),
        "unit": r["measure_score_unit"],
        "system": r["measure_score_system"],
        "code": r["measure_score_code"],
    }


def _identifier(bind, r):
    return {
        "use": r["use"],
        "type": {
            "coding": [
                _coding(c)
                for c in _rows_of(
                    bind, f"{P}_identifier_type_coding", "identifier_id", r["id"]
                )
            ],
            "text": r["type_text"],
        },
        "system": r["system"],
        "value": r["value"],
        "period": _period(r["period_start"], r["period_end"]),
        "assigner": _ref(r, "assigner"),
    }


def _population(bind, r, table, fk_coding):
    return {
        "code": _concept(bind, table, fk_coding, r["id"], r["code_text"]),
        "count": r["count"],
        "subjectResults": _ref(r, "subject_results"),
    }


def _stratum(bind, s):
    sid = s["id"]
    return {
        "value": _concept(
            bind,
            f"{P}_group_stratifier_stratum_value_coding",
            "stratum_id",
            sid,
            s["value_text"],
        ),
        "component": [
            {
                "code": _concept(
                    bind,
                    f"{P}_group_stratifier_stratum_comp_code_coding",
                    "component_id",
                    c["id"],
                    c["code_text"],
                ),
                "value": _concept(
                    bind,
                    f"{P}_group_stratifier_stratum_comp_value_coding",
                    "component_id",
                    c["id"],
                    c["value_text"],
                ),
            }
            for c in _rows_of(
                bind, f"{P}_group_stratifier_stratum_component", "stratum_id", sid
            )
        ],
        "population": [
            _population(
                bind,
                p,
                f"{P}_group_stratifier_stratum_pop_code_coding",
                "stratum_population_id",
            )
            for p in _rows(
                bind,
                f"SELECT * FROM {P}_group_stratifier_stratum_population "
                "WHERE stratum_id = :v ORDER BY id",
                v=sid,
            )
        ],
        "measureScore": _score(s),
    }


def _group(bind, g):
    gid = g["id"]
    stratifiers = []
    for st in _rows_of(bind, f"{P}_group_stratifier", "group_id", gid):
        stratifiers.append(
            {
                "code": [
                    _concept(
                        bind,
                        f"{P}_group_stratifier_code_coding",
                        "stratifier_code_id",
                        c["id"],
                        c["code_text"],
                    )
                    for c in _rows_of(
                        bind, f"{P}_group_stratifier_code", "stratifier_id", st["id"]
                    )
                ],
                "stratum": [
                    _stratum(bind, s)
                    for s in _rows(
                        bind,
                        f"SELECT *, measure_score_comparator::text AS comparator_text "
                        f"FROM {P}_group_stratifier_stratum WHERE stratifier_id = :v "
                        "ORDER BY id",
                        v=st["id"],
                    )
                ],
            }
        )
    return {
        "code": _concept(
            bind, f"{P}_group_code_coding", "group_id", gid, g["code_text"]
        ),
        "population": [
            _population(bind, p, f"{P}_group_population_code_coding", "population_id")
            for p in _rows_of(bind, f"{P}_group_population", "group_id", gid)
        ],
        "measureScore": _score(g),
        "stratifier": stratifiers,
    }


def _build_content(bind, r):
    pk = r["id"]
    groups = _rows(
        bind,
        f"SELECT *, measure_score_comparator::text AS comparator_text FROM {P}_group "
        f"WHERE {P}_pk = :v ORDER BY id",
        v=pk,
    )
    content = {
        "extension": list(_json(r["extension"]) or []),
        "identifier": [
            _identifier(bind, i)
            for i in _rows_of(bind, f"{P}_identifier", f"{P}_pk", pk)
        ],
        "status": _hyphenate(r["status_text"]),
        "type": _hyphenate(r["type_text"]),
        "measure": r["measure"],
        "subject": _ref(r, "subject"),
        "date": _iso(r["date"]),
        "reporter": _ref(r, "reporter"),
        "period": _period(r["period_start"], r["period_end"]),
        "improvementNotation": {
            "coding": [
                _coding(c)
                for c in _rows_of(
                    bind, f"{P}_improvement_notation_coding", f"{P}_pk", pk
                )
            ],
            "text": r["improvement_notation_text"],
        },
        "group": [_group(bind, g) for g in groups],
        "evaluatedResource": [
            _ref(x, "evaluated_resource")
            for x in _rows_of(bind, f"{P}_evaluated_resource", f"{P}_pk", pk)
        ],
    }
    return _prune(content)


def _backfill_content(bind):
    # `status` / `type` are enums: cast them to text so the driver returns the label.
    for r in _rows(
        bind, f"SELECT *, status::text AS status_text, type::text AS type_text FROM {P}"
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
_SUBJECT_TYPES = (
    "Practitioner",
    "Group",
    "Device",
    "Patient",
    "PractitionerRole",
    "RelatedPerson",
    "Location",
)
_REPORTER_TYPES = ("Practitioner", "PractitionerRole", "Location", "Organization")
_MEASURE_TYPES = ("Measure",)


def _typed(reference, allowed):
    """(type, id) of a relative `Type/<id>` whose type is in `allowed` (any type when `allowed`
    is None); (None, None) otherwise."""
    match = _REF.match(reference or "")
    return (
        (match["type"], int(match["id"]))
        if match and (allowed is None or match["type"] in allowed)
        else (None, None)
    )


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


def _insert_reference(bind, pk, param, ref, allowed):
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return
    rtype, rid = _typed(reference, allowed)
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
        date_value = doc.get("date")
        date_start = _bounds(date_value)[0] if date_value else None
        date_end = _bounds(date_value)[1] if date_value else None
        period_start, period_end = _period_bounds(doc.get("period"))
        status = doc.get("status")
        columns = {
            "date_start": date_start,
            "date_end": date_end,
            "period_start": period_start,
            "period_end": period_end,
            **_ref_params("subject", doc.get("subject"), _SUBJECT_TYPES),
            **_ref_params("reporter", doc.get("reporter"), _REPORTER_TYPES),
        }
        sets = ", ".join(f"{k} = :{k}" for k in columns)
        bind.execute(
            sa.text(
                f"UPDATE {P} SET status = CAST(:status AS measure_report_status), "
                f"{sets} WHERE id = :pk"
            ),
            {**columns, "status": status if status in _STATUS else None, "pk": pk},
        )

        for identifier in doc.get("identifier") or []:
            _insert_identifier(bind, pk, identifier)
        for ref in doc.get("evaluatedResource") or []:
            _insert_reference(bind, pk, "evaluated-resource", ref, None)
        if isinstance(doc.get("measure"), str) and doc["measure"]:
            _insert_reference(
                bind, pk, "measure", {"reference": doc["measure"]}, _MEASURE_TYPES
            )


# Main-table columns that survive unchanged: the id, the audit/tenant columns, the status, the
# period range and the subject / reporter index columns (their reference-type enums become plain
# strings).
_KEEP = {
    "id",
    "measure_report_id",
    "tenant_id",
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
    "content",
    "status",
    "period_start",
    "period_end",
    *(
        f"{ref}_{part}"
        for ref in ("subject", "reporter")
        for part in ("reference", "type", "id", "identifier_system", "identifier_value")
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

    # Every old child table (all `measure_report_*` tables; no other resource shares the prefix).
    # The new index tables are recreated below; dropped with CASCADE, so order does not matter.
    for table in [
        r[0]
        for r in bind.execute(
            sa.text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = current_schema() "
                "AND table_name LIKE 'measure\\_report\\_%'"
            )
        )
    ]:
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

    # The subject / reporter types were enums; they are plain strings now.
    for column in ("subject_type", "reporter_type"):
        op.alter_column(
            P,
            column,
            type_=sa.String(),
            nullable=True,
            postgresql_using=f"{column}::text",
        )
    # Every per-field `measure_report_*` enum of the old schema except the status (which already
    # holds the real FHIR codes). The shared `identifier_use` does not start with this prefix.
    for name in [
        r[0]
        for r in bind.execute(
            sa.text(
                "SELECT typname FROM pg_type WHERE typtype = 'e' "
                "AND typname LIKE 'measure\\_report\\_%' "
                "AND typname <> 'measure_report_status'"
            )
        )
    ]:
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    op.alter_column(P, "status", nullable=True)
    # The public id's sequence is now its server default.
    op.execute(
        f"ALTER TABLE {P} ALTER COLUMN measure_report_id "
        "SET DEFAULT nextval('measure_report_pub_seq')"
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
        f"ALTER TABLE {P} DROP CONSTRAINT IF EXISTS measure_report_measure_report_id_key"
    )
    for column in ("tenant_id", "created_at", "updated_at"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)

    op.add_column(P, sa.Column("date_start", sa.DateTime(timezone=True), nullable=True))
    op.add_column(P, sa.Column("date_end", sa.DateTime(timezone=True), nullable=True))
    op.execute(f"DROP INDEX IF EXISTS ix_{P}_subject_id")
    op.create_index("ix_measure_report_date", P, ["date_start", "date_end"])
    op.create_index("ix_measure_report_period", P, ["period_start", "period_end"])
    op.create_index(
        "ix_measure_report_subject_type_id", P, ["subject_type", "subject_id"]
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
        "ix_measure_report_reference_param_type_id",
        f"{P}_reference",
        ["param", "reference_type", "reference_id"],
    )

    _rebuild_index(bind)
    for column in ("id", "reporter_id", "status"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)
    op.create_index(
        f"ix_{P}_measure_report_id",
        P,
        ["measure_report_id"],
        unique=True,
        if_not_exists=True,
    )
    op.alter_column(P, "content", nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "measure_report content/index migration is one-way: its old normalized tables "
        "are not rebuilt from `content`. Restore from a backup taken before upgrading."
    )
