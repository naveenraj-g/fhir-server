"""group: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: c6b1d8f4a250
Revises: b5a0c7e3f149
Create Date: 2026-12-15 10:00:00.000000

Medplum-style storage for Group (see GroupModel's docstring), same as the other resources already
moved (the latest being MedicationRequest b5a0c7e3f149). The whole FHIR resource moves into
`group.content`; every column/table that survives is a search index for one of the FHIR R4 Group
search parameters (or `_id` / `_lastUpdated`), derived from `content`:

  group: type (the Postgres enum already held the real FHIR codes, so it stays), actual, the
      managing_entity_* columns (`managing_entity_type` becomes a plain string); the public id gets
      its sequence as a server default; new: content, managing_entity_identifier_*.
  group_identifier: rebuilt as an index table
  group_token: new - code (slot 0), characteristic / value / exclude (slot n = the n-th
      characteristic; what the `characteristic-value` composite pairs on)
  group_member: rebuilt - one row per member.entity
  dropped: every old child table (code / characteristic / value codings, characteristics,
      identifier type codings), every main-table column with no search parameter (active, name,
      quantity, code text, extension, the manager's display) and the per-field `group_*` enums
      other than `group_type`.

upgrade: (1) builds `content` for every existing row from the old columns and tables - a frozen
copy of the old to_fhir_group() logic (but keeping a reference's raw string, so an absolute URL is
not lost), so this migration never depends on application code that has since changed; (2) drops
the old child tables/columns and creates the index tables; (3) rebuilds the index from `content`.

downgrade: not supported. Everything the old schema held is preserved in `content`, but rebuilding
the old normalized tables from it is not implemented - restore from a backup taken before
upgrading.
"""

import json
import re
import unicodedata
from datetime import date, datetime, time
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "c6b1d8f4a250"
down_revision: Union[str, None] = "b5a0c7e3f149"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

P = "group"
Q = '"group"'  # `group` is a reserved word

_TYPES = ("person", "animal", "practitioner", "device", "medication", "substance")


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


def _norm(text):
    """Frozen copy of app.fhir.search.values.normalize."""
    if text is None:
        return None
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


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


def _ref(row, prefix):
    """A Reference from the old `{prefix}_reference/_type/_id/_display` columns."""
    g = row.get
    raw = g(f"{prefix}_reference")
    if not raw and g(f"{prefix}_type") and g(f"{prefix}_id"):
        raw = f"{g(f'{prefix}_type')}/{g(f'{prefix}_id')}"
    return {"reference": raw, "display": g(f"{prefix}_display")}


def _rows_of(bind, table, fk, value):
    return _rows(bind, f"SELECT * FROM {table} WHERE {fk} = :v ORDER BY id", v=value)


def _identifier(bind, i):
    return {
        "use": i["use"],
        "type": _concept(
            _rows_of(bind, "group_identifier_type_coding", "identifier_id", i["id"]),
            i["type_text"],
        ),
        "system": i["system"],
        "value": i["value"],
        "period": _period(i["period_start"], i["period_end"]),
        "assigner": _ref(i, "assigner"),
    }


def _characteristic(bind, c):
    entry = {
        "code": _concept(
            _rows_of(
                bind, "group_characteristic_code_coding", "characteristic_id", c["id"]
            ),
            c["code_text"],
        ),
        "exclude": c["exclude"],
        "period": _period(c["period_start"], c["period_end"]),
    }
    value_cc = _concept(
        _rows_of(
            bind, "group_characteristic_value_coding", "characteristic_id", c["id"]
        ),
        c["value_codeable_concept_text"],
    )
    if c["value_boolean"] is not None:
        entry["valueBoolean"] = c["value_boolean"]
    elif _prune(value_cc):
        entry["valueCodeableConcept"] = value_cc
    elif c["value_quantity"]:
        entry["valueQuantity"] = _json(c["value_quantity"])
    elif c["value_range"]:
        entry["valueRange"] = _json(c["value_range"])
    else:
        entry["valueReference"] = _ref(c, "value_reference")
    return entry


def _build_content(bind, r):
    pk = r["id"]
    content = {
        "extension": list(_json(r["extension"]) or []),
        "identifier": [
            _identifier(bind, i)
            for i in _rows_of(bind, "group_identifier", "group_pk", pk)
        ],
        "active": r["active"],
        "type": r["type_text"],
        "actual": r["actual"],
        "code": _concept(
            _rows_of(bind, "group_code_coding", "group_pk", pk), r["code_text"]
        ),
        "name": r["name"],
        "quantity": r["quantity"],
        "managingEntity": _ref(r, "managing_entity"),
        "characteristic": [
            _characteristic(bind, c)
            for c in _rows_of(bind, "group_characteristic", "group_pk", pk)
        ],
        "member": [
            {
                "entity": _ref(m, "entity"),
                "period": _period(m["period_start"], m["period_end"]),
                "inactive": m["inactive"],
            }
            for m in _rows_of(bind, "group_member", "group_pk", pk)
        ],
    }
    pruned = _prune(content)
    # `exclude: false` and `active: false` / `actual: false` are values, not absences
    for source, target in zip(
        _rows_of(bind, "group_characteristic", "group_pk", pk),
        pruned.get("characteristic", []),
    ):
        if source["exclude"] is not None:
            target["exclude"] = source["exclude"]
    for key in ("active", "actual"):
        if r[key] is not None:
            pruned[key] = r[key]
    return pruned


def _backfill_content(bind):
    # `type` is an enum: cast it to text so the driver returns the label.
    for r in _rows(bind, f"SELECT *, type::text AS type_text FROM {Q}"):
        bind.execute(
            sa.text(f"UPDATE {Q} SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {
                "c": json.dumps(_build_content(bind, dict(r)), default=str),
                "id": r["id"],
            },
        )


# -- upgrade: content -> search index (frozen copy of _indexer.py) ---------------

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")
_MANAGING = ("Organization", "RelatedPerson", "Practitioner", "PractitionerRole")
_MEMBER = (
    "Patient",
    "Practitioner",
    "PractitionerRole",
    "Device",
    "Medication",
    "Substance",
    "Group",
)


def _typed(reference, allowed):
    match = _REF.match(reference or "")
    if match and match["type"] in allowed:
        return match["type"], int(match["id"])
    return None, None


def _insert_token(bind, pk, param, slot, concept):
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
                "INSERT INTO group_token (group_pk, param, slot, system, code, display_norm, text_norm) "
                "VALUES (:pk, :param, :slot, :s, :c, :d, :t)"
            ),
            {
                "pk": pk,
                "param": param,
                "slot": slot,
                "s": c.get("system"),
                "c": c.get("code"),
                "d": _norm(c.get("display")),
                "t": text,
            },
        )


def _insert_bool(bind, pk, param, slot, value):
    if isinstance(value, bool):
        bind.execute(
            sa.text(
                "INSERT INTO group_token (group_pk, param, slot, code) VALUES (:pk, :param, :slot, :c)"
            ),
            {"pk": pk, "param": param, "slot": slot, "c": "true" if value else "false"},
        )


def _insert_identifier(bind, pk, identifier):
    if not (identifier.get("system") or identifier.get("value")):
        return
    itype = identifier.get("type") or {}
    for c in itype.get("coding") or [{}]:
        bind.execute(
            sa.text(
                "INSERT INTO group_identifier (group_pk, system, value, type_system, type_code, "
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
    for row in _rows(bind, f"SELECT id, content FROM {Q}"):
        pk, doc = row["id"], _json(row["content"])
        manager = doc.get("managingEntity") or {}
        reference = manager.get("reference")
        identifier = manager.get("identifier") or {}
        mtype, mid = _typed(reference, _MANAGING)
        group_type = doc.get("type")
        actual = doc.get("actual")
        bind.execute(
            sa.text(
                f"UPDATE {Q} SET type = CAST(:type AS group_type), actual = :actual, "
                "managing_entity_reference = :mr, managing_entity_type = :mt, managing_entity_id = :mi, "
                "managing_entity_identifier_system = :ms, managing_entity_identifier_value = :mv "
                "WHERE id = :pk"
            ),
            {
                "type": group_type if group_type in _TYPES else None,
                "actual": actual if isinstance(actual, bool) else None,
                "mr": reference,
                "mt": mtype,
                "mi": mid,
                "ms": identifier.get("system"),
                "mv": identifier.get("value"),
                "pk": pk,
            },
        )
        for i in doc.get("identifier") or []:
            _insert_identifier(bind, pk, i)
        _insert_token(bind, pk, "code", 0, doc.get("code"))
        for slot, characteristic in enumerate(doc.get("characteristic") or [], start=1):
            characteristic = characteristic or {}
            _insert_token(bind, pk, "characteristic", slot, characteristic.get("code"))
            _insert_token(
                bind, pk, "value", slot, characteristic.get("valueCodeableConcept")
            )
            _insert_bool(bind, pk, "value", slot, characteristic.get("valueBoolean"))
            _insert_bool(bind, pk, "exclude", slot, characteristic.get("exclude"))
        for member in doc.get("member") or []:
            entity = (member or {}).get("entity") or {}
            ref_value = entity.get("reference")
            ref_identifier = entity.get("identifier") or {}
            if not (ref_value or ref_identifier.get("value")):
                continue
            etype, eid = _typed(ref_value, _MEMBER)
            bind.execute(
                sa.text(
                    "INSERT INTO group_member (group_pk, reference_reference, reference_type, reference_id, "
                    "reference_identifier_system, reference_identifier_value) VALUES (:pk, :r, :t, :i, :s, :v)"
                ),
                {
                    "pk": pk,
                    "r": ref_value,
                    "t": etype,
                    "i": eid,
                    "s": ref_identifier.get("system"),
                    "v": ref_identifier.get("value"),
                },
            )


# Main-table columns that survive unchanged: the id, the audit/tenant columns, `type` and `actual`
# and the manager's index columns (`managing_entity_type`'s enum becomes a plain string).
_KEEP = {
    "id",
    "group_id",
    "tenant_id",
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
    "content",
    "type",
    "actual",
    "managing_entity_reference",
    "managing_entity_type",
    "managing_entity_id",
}


def _fk():
    return sa.Column(
        "group_pk", sa.BigInteger(), sa.ForeignKey("group.id"), nullable=False
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
            "AND table_name LIKE 'group\\_%' AND table_type = 'BASE TABLE'"
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

    op.alter_column(
        P,
        "managing_entity_type",
        type_=sa.String(),
        nullable=True,
        postgresql_using="managing_entity_type::text",
    )
    for (name,) in bind.execute(
        sa.text(
            "SELECT typname FROM pg_type WHERE typtype = 'e' AND typname LIKE 'group\\_%' "
            "AND typname <> 'group_type'"
        )
    ).all():
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # The public id's sequence is now its server default.
    op.execute(
        f"ALTER TABLE {Q} ALTER COLUMN group_id SET DEFAULT nextval('group_pub_seq')"
    )
    # No UNIQUE constraint on the public id (the sequence and the unique index keep it unique).
    op.execute(f"ALTER TABLE {Q} DROP CONSTRAINT IF EXISTS group_group_id_key")
    # Every index column is nullable (R4's minimums are the validator's rule).
    op.alter_column(
        P,
        "type",
        existing_type=postgresql.ENUM(*_TYPES, name="group_type", create_type=False),
        nullable=True,
    )
    op.alter_column(P, "actual", existing_type=sa.Boolean(), nullable=True)

    # The audit columns as the shared mixin declares them (the original table was created with
    # looser ones): tenant/actor NOT NULL, timestamps nullable and indexed.
    op.execute(f"UPDATE {Q} SET tenant_id = '' WHERE tenant_id IS NULL")
    op.execute(f"UPDATE {Q} SET created_by = '' WHERE created_by IS NULL")
    op.alter_column(P, "tenant_id", existing_type=sa.String(), nullable=False)
    op.alter_column(P, "created_by", existing_type=sa.String(), nullable=False)
    op.alter_column(
        P, "created_at", existing_type=sa.DateTime(timezone=True), nullable=True
    )
    op.alter_column(
        P, "updated_at", existing_type=sa.DateTime(timezone=True), nullable=True
    )
    for column in ("id", "tenant_id", "created_at", "updated_at", "managing_entity_id"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)
    op.add_column(
        P, sa.Column("managing_entity_identifier_system", sa.String(), nullable=True)
    )
    op.add_column(
        P, sa.Column("managing_entity_identifier_value", sa.String(), nullable=True)
    )

    op.create_table(
        "group_identifier",
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
    _index("group_identifier", "group_pk")
    _index("group_identifier", "value")

    op.create_table(
        "group_token",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column("param", sa.String(), nullable=False),
        sa.Column("slot", sa.Integer(), nullable=False),
        sa.Column("system", sa.String(), nullable=True),
        sa.Column("code", sa.String(), nullable=True),
        sa.Column("display_norm", sa.String(), nullable=True),
        sa.Column("text_norm", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("group_token", "group_pk")
    op.create_index("ix_group_token_param_code", "group_token", ["param", "code"])

    op.create_table(
        "group_member",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column("reference_reference", sa.String(), nullable=True),
        sa.Column("reference_type", sa.String(), nullable=True),
        sa.Column("reference_id", sa.BigInteger(), nullable=True),
        sa.Column("reference_identifier_system", sa.String(), nullable=True),
        sa.Column("reference_identifier_value", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    _index("group_member", "group_pk")
    op.create_index(
        "ix_group_member_type_id", "group_member", ["reference_type", "reference_id"]
    )

    _rebuild_index(bind)
    op.alter_column(P, "content", nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "group content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
