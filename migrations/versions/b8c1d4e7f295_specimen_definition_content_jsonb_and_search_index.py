"""specimen_definition: store the whole resource in `content` JSONB; keep only search-index tables

Revision ID: b8c1d4e7f295
Revises: a7b0c3d6e184
Create Date: 2026-12-28 10:00:00.000000

Stores SpecimenDefinition whole in `content` (see SpecimenDefinitionModel's docstring), like the
other resources already moved (ObservationDefinition a7b0c3d6e184, ...). The whole FHIR resource
- `identifier` (flattened onto the old main row), `typeCollected`, `patientPreparation`,
`timeAspect`, `collection` and the whole `typeTested` tree (container, additives, retention time,
rejection criteria, handling) - moves into `specimen_definition.content`; what survives is a
search index for R4's three parameters (all tokens), derived from `content`:

  specimen_definition_identifier: new (one row per identifier type coding)
  specimen_definition_token: new - `type` (typeCollected) and `container`
      (typeTested.container.type of every entry)
  dropped: every old child table, every main-table column (the flattened identifier, type
      collected text, time aspect) and the per-field `specimen_definition_*` enums.

upgrade: (1) builds `content` for every existing row from the old columns and tables - a frozen
copy of the old to_fhir_specimen_definition() logic (but keeping a reference's raw string, so an
absolute URL is not lost), so this migration never depends on application code that has since
changed; (2) drops the old child tables/columns/enums and creates the index tables; (3) rebuilds
the index from `content`.

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
revision: str = "b8c1d4e7f295"
down_revision: str | None = "a7b0c3d6e184"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

P = "specimen_definition"

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
        "SpecimenDefinition",
        "ResearchStudy",
        "InsurancePlan",
        "HealthcareService",
        "Group",
        "Location",
        "Medication",
        "Substance",
        "SpecimenDefinition",
        "SpecimenDefinition",
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


def _cc(bind, table, fk, pk, text):
    """A CodeableConcept from a `{table}` of codings keyed by `fk` and a text column."""
    return _concept(_rows_of(bind, table, fk, pk), text)


def _cc_rows(bind, table, fk_col, pk):
    """The old CodeableConcept-list tables: `{table}` (text) + `{table}_coding` (fk `fk_col`)."""
    return [
        _cc(bind, f"{table}_coding", fk_col, row["id"], row["text"])
        for row in _rows_of(bind, table, f"{P}_pk", pk)
    ]


def _identifier(bind, r):
    """The old table flattened the single identifier onto the main row."""
    return {
        "use": r["identifier_use_text"],
        "type": _concept(
            _rows_of(bind, f"{P}_identifier_type_coding", f"{P}_pk", r["id"]),
            r["identifier_type_text"],
        ),
        "system": r["identifier_system"],
        "value": r["identifier_value"],
        "period": _period(r["identifier_period_start"], r["identifier_period_end"]),
        "assigner": _ref(r, "identifier_assigner"),
    }


def _container(bind, t):
    tid = t["id"]
    additives = []
    for a in _rows_of(bind, f"{P}_container_additive", "type_tested_pk", tid):
        entry = {
            "additiveCodeableConcept": _cc(
                bind,
                f"{P}_container_additive_coding",
                "container_additive_pk",
                a["id"],
                a["additive_codeable_concept_text"],
            )
        }
        if _has_ref(a, "additive_reference"):
            entry["additiveReference"] = _ref(a, "additive_reference")
        additives.append(entry)
    container = {
        "material": _cc(
            bind,
            f"{P}_container_material_coding",
            "type_tested_pk",
            tid,
            t["container_material_text"],
        ),
        "type": _cc(
            bind,
            f"{P}_container_type_coding",
            "type_tested_pk",
            tid,
            t["container_type_text"],
        ),
        "cap": _cc(
            bind,
            f"{P}_container_cap_coding",
            "type_tested_pk",
            tid,
            t["container_cap_text"],
        ),
        "description": t["container_description"],
        "capacity": _q(t, "container_capacity"),
        "additive": additives,
        "preparation": t["container_preparation"],
    }
    # minimumVolume[x]: the Quantity when it has anything, else the string.
    if _has_q(t, "container_minimum_volume_quantity"):
        container["minimumVolumeQuantity"] = _q(
            t, "container_minimum_volume_quantity", "min_volume_comparator"
        )
    elif t["container_minimum_volume_string"]:
        container["minimumVolumeString"] = t["container_minimum_volume_string"]
    return container


def _handlings(bind, tid):
    out = []
    for h in _rows(
        bind,
        f"SELECT *, max_duration_comparator::text AS duration_comparator "
        f"FROM {P}_type_tested_handling WHERE type_tested_pk = :v ORDER BY id",
        v=tid,
    ):
        out.append(
            {
                "temperatureQualifier": _cc(
                    bind,
                    f"{P}_handling_temp_qual_coding",
                    "handling_pk",
                    h["id"],
                    h["temperature_qualifier_text"],
                ),
                "temperatureRange": {
                    "low": _q(h, "temperature_range_low"),
                    "high": _q(h, "temperature_range_high"),
                },
                "maxDuration": _q(h, "max_duration", "duration_comparator"),
                "instruction": h["instruction"],
            }
        )
    return out


def _types_tested(bind, pk):
    out = []
    for t in _rows(
        bind,
        f"SELECT *, preference::text AS preference_text, "
        f"retention_time_comparator::text AS retention_comparator, "
        f"container_minimum_volume_quantity_comparator::text AS min_volume_comparator "
        f"FROM {P}_type_tested WHERE {P}_pk = :v ORDER BY id",
        v=pk,
    ):
        tid = t["id"]
        out.append(
            {
                "isDerived": t["is_derived"],
                "type": _cc(
                    bind,
                    f"{P}_type_tested_type_coding",
                    "type_tested_pk",
                    tid,
                    t["type_text"],
                ),
                "preference": t["preference_text"],
                "container": _container(bind, t),
                "requirement": t["requirement"],
                "retentionTime": _q(t, "retention_time", "retention_comparator"),
                "rejectionCriterion": [
                    _cc(
                        bind,
                        f"{P}_type_tested_rejection_criterion_coding",
                        "rejection_criterion_pk",
                        rc["id"],
                        rc["text"],
                    )
                    for rc in _rows_of(
                        bind,
                        f"{P}_type_tested_rejection_criterion",
                        "type_tested_pk",
                        tid,
                    )
                ],
                "handling": _handlings(bind, tid),
            }
        )
    return out


def _build_content(bind, r):
    pk = r["id"]
    content = {
        "identifier": _identifier(bind, r),
        "typeCollected": _cc(
            bind,
            f"{P}_type_collected_coding",
            f"{P}_pk",
            pk,
            r["type_collected_text"],
        ),
        "patientPreparation": _cc_rows(
            bind, f"{P}_patient_preparation", "patient_preparation_pk", pk
        ),
        "timeAspect": r["time_aspect"],
        "collection": _cc_rows(bind, f"{P}_collection", "collection_pk", pk),
        "typeTested": _types_tested(bind, pk),
    }
    return _prune(content)


def _backfill_content(bind):
    # identifier.use is an enum: cast it to text so the driver returns the label.
    for r in _rows(
        bind, f"SELECT *, identifier_use::text AS identifier_use_text FROM {P}"
    ):
        bind.execute(
            sa.text(f"UPDATE {P} SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {
                "c": json.dumps(_build_content(bind, dict(r)), default=str),
                "id": r["id"],
            },
        )


# -- upgrade: content -> search index (frozen copy of _indexer.py) --------------------------


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


def _insert_token(bind, pk, param, system, code, display=None, text=None):
    bind.execute(
        sa.text(
            f"INSERT INTO {P}_token ({P}_pk, param, system, code, display_norm, text_norm) "
            "VALUES (:pk, :param, :s, :c, :d, :t)"
        ),
        {
            "pk": pk,
            "param": param,
            "s": system,
            "c": code,
            "d": _norm(display),
            "t": _norm(text),
        },
    )


def _insert_concept(bind, pk, param, concept):
    """One row per coding, plus a code-less row for a concept that only has `text`."""
    if not isinstance(concept, dict):
        return
    text = concept.get("text")
    codings = [
        c
        for c in concept.get("coding") or []
        if c.get("system") or c.get("code") or c.get("display")
    ]
    for c in codings:
        _insert_token(
            bind, pk, param, c.get("system"), c.get("code"), c.get("display"), text
        )
    if not codings and text:
        _insert_token(bind, pk, param, None, None, None, text)


def _rebuild_index(bind):
    for row in _rows(bind, f"SELECT id, content FROM {P}"):
        pk, doc = row["id"], _json(row["content"])
        if isinstance(doc.get("identifier"), dict):
            _insert_identifier(bind, pk, doc["identifier"])
        _insert_concept(bind, pk, "type", doc.get("typeCollected"))
        for tested in doc.get("typeTested") or []:
            container = tested.get("container") if isinstance(tested, dict) else None
            if isinstance(container, dict):
                _insert_concept(bind, pk, "container", container.get("type"))


# The main-table columns that survive unchanged: the id, the audit/tenant columns and `content`.
# Everything else of the old table is dropped; so is every `specimen_definition_*` child table
# and per-field enum (matched by prefix, which no other resource shares - `specimen_*` belongs to
# Specimen, and the shared `identifier_use` type is not touched).
_KEEP = {
    "id",
    "specimen_definition_id",
    "tenant_id",
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
    "content",
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

    # Every old child table (`specimen_definition_*`), but not this table itself.
    for (table,) in bind.execute(
        sa.text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema() "
            "AND table_name LIKE 'specimen\\_definition\\_%' AND table_type = 'BASE TABLE'"
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
            "AND typname LIKE 'specimen\\_definition\\_%'"
        )
    ).all():
        op.execute(f'DROP TYPE IF EXISTS "{name}"')

    # The public id's sequence is now its server default.
    op.execute(
        f"ALTER TABLE {P} ALTER COLUMN specimen_definition_id "
        "SET DEFAULT nextval('specimen_definition_pub_seq')"
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
        f"ALTER TABLE {P} DROP CONSTRAINT IF EXISTS specimen_definition_specimen_definition_id_key"
    )
    for column in ("tenant_id", "created_at", "updated_at"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)
    op.create_index("ix_specimen_definition_id", P, ["id"], if_not_exists=True)
    op.create_index(
        "ix_specimen_definition_specimen_definition_id",
        P,
        ["specimen_definition_id"],
        unique=True,
        if_not_exists=True,
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
        "ix_specimen_definition_token_param_code", f"{P}_token", ["param", "code"]
    )

    _rebuild_index(bind)
    op.alter_column(P, "content", nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "specimen_definition content/index migration is one-way: its old normalized tables are "
        "not rebuilt from `content`. Restore from a backup taken before upgrading."
    )
