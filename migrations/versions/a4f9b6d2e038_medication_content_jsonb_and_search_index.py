"""medication: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: a4f9b6d2e038
Revises: z3e8a5c1d927
Create Date: 2026-12-13 10:00:00.000000

Medplum-style storage for Medication (see MedicationModel's docstring), same as the other
resources already moved (the latest being ServiceRequest z3e8a5c1d927). The whole FHIR resource
moves into `medication.content`; every column/table that survives is a search index for one of
the FHIR R4 Medication search parameters (or `_id` / `_lastUpdated`), derived from `content`:

  medication: status (the Postgres enum already held the real FHIR codes, so it stays),
      expiration_start/_end (batch.expirationDate, the range the dateTime covers), lot_number,
      the manufacturer_* columns (`manufacturer_type` becomes a plain string); the public id gets
      its sequence as a server default; new: content.
  medication_identifier: rebuilt as an index table
  medication_token: new - code, form, ingredient-code
  medication_reference: new - ingredient (a Substance or a Medication)
  dropped: the old child tables (identifier + its type coding, code / form codings, ingredient +
      its item coding), every main-table column with no search parameter (code / form text,
      amount, extension, the display / logical-identifier details of the manufacturer) and the
      per-field `medication_*` enums except `medication_status`.

upgrade: (1) builds `content` for every existing row from the old columns and tables - a frozen
copy of the old to_fhir_medication() logic (but keeping a reference's raw string, so an absolute
URL is not lost), so this migration never depends on application code that has since changed; (2)
drops the old child tables/columns and creates the index tables; (3) rebuilds the index from
`content`.

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
revision: str = "a4f9b6d2e038"
down_revision: Union[str, None] = "z3e8a5c1d927"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

P = "medication"

_STATUS = ("active", "inactive", "entered-in-error")


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


def _ratio(row, prefix):
    return {
        "numerator": _quantity(row, f"{prefix}_numerator"),
        "denominator": _quantity(row, f"{prefix}_denominator"),
    }


def _identifier(bind, i):
    return {
        "use": i["use"],
        "type": _concept(
            _rows_of(bind, f"{P}_identifier_type_coding", f"{P}_identifier_id", i["id"]),
            i["type_text"],
        ),
        "system": i["system"],
        "value": i["value"],
        "period": _period(i["period_start"], i["period_end"]),
        "assigner": _ref(i, "assigner"),
    }


def _ingredient(bind, ing):
    item = _concept(
        _rows_of(bind, f"{P}_ingredient_item_coding", f"{P}_ingredient_id", ing["id"]),
        ing["item_codeable_concept_text"],
    )
    entry = {"isActive": ing["is_active"], "strength": _ratio(ing, "strength")}
    if _prune(item):
        entry["itemCodeableConcept"] = item
    else:
        entry["itemReference"] = _ref(ing, "item")
    return entry


def _build_content(bind, r):
    pk = r["id"]
    content = {
        "extension": list(_json(r["extension"]) or []),
        "identifier": [_identifier(bind, i) for i in _rows_of(bind, f"{P}_identifier", f"{P}_pk", pk)],
        "code": _concept(_rows_of(bind, f"{P}_code_coding", f"{P}_pk", pk), r["code_text"]),
        "status": r["status_text"],
        "manufacturer": _ref(r, "manufacturer"),
        "form": _concept(_rows_of(bind, f"{P}_form_coding", f"{P}_pk", pk), r["form_text"]),
        "amount": _ratio(r, "amount"),
        "ingredient": [_ingredient(bind, i) for i in _rows_of(bind, f"{P}_ingredient", f"{P}_pk", pk)],
        "batch": {"lotNumber": r["batch_lot_number"], "expirationDate": _iso(r["batch_expiration_date"])},
    }
    return _prune(content)


def _backfill_content(bind):
    # `status` is an enum: cast it to text so the driver returns the label.
    for r in _rows(bind, f"SELECT *, status::text AS status_text FROM {P}"):
        bind.execute(
            sa.text(f"UPDATE {P} SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, dict(r)), default=str), "id": r["id"]},
        )


# -- upgrade: content -> search index (frozen copy of _indexer.py) ---------------

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")
_INGREDIENT_TYPES = ("Substance", "Medication")


def _typed(reference, allowed):
    match = _REF.match(reference or "")
    if match and match["type"] in allowed:
        return match["type"], int(match["id"])
    return None, None


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
        batch = doc.get("batch") or {}
        expiration = batch.get("expirationDate")
        start, end = _bounds(expiration)[0], _bounds(expiration)[1]
        manufacturer = doc.get("manufacturer") or {}
        reference = manufacturer.get("reference")
        identifier = manufacturer.get("identifier") or {}
        rtype, rid = _typed(reference, ("Organization",))
        status = doc.get("status")
        bind.execute(
            sa.text(
                f"UPDATE {P} SET status = CAST(:status AS medication_status), expiration_start = :es, "
                "expiration_end = :ee, lot_number = :lot, manufacturer_reference = :mr, "
                "manufacturer_type = :mt, manufacturer_id = :mi, manufacturer_identifier_system = :ms, "
                "manufacturer_identifier_value = :mv WHERE id = :pk"
            ),
            {
                "status": status if status in _STATUS else None,
                "es": start,
                "ee": end,
                "lot": batch.get("lotNumber"),
                "mr": reference,
                "mt": rtype,
                "mi": rid,
                "ms": identifier.get("system"),
                "mv": identifier.get("value"),
                "pk": pk,
            },
        )
        for i in doc.get("identifier") or []:
            _insert_identifier(bind, pk, i)
        _insert_token(bind, pk, "code", doc.get("code"))
        _insert_token(bind, pk, "form", doc.get("form"))
        for ingredient in doc.get("ingredient") or []:
            ingredient = ingredient or {}
            _insert_token(bind, pk, "ingredient-code", ingredient.get("itemCodeableConcept"))
            ref = ingredient.get("itemReference") or {}
            ref_value = ref.get("reference")
            ref_identifier = ref.get("identifier") or {}
            if not (ref_value or ref_identifier.get("value")):
                continue
            itype, iid = _typed(ref_value, _INGREDIENT_TYPES)
            bind.execute(
                sa.text(
                    f"INSERT INTO {P}_reference ({P}_pk, param, reference_reference, reference_type, "
                    "reference_id, reference_identifier_system, reference_identifier_value) "
                    "VALUES (:pk, 'ingredient', :r, :t, :i, :s, :v)"
                ),
                {
                    "pk": pk,
                    "r": ref_value,
                    "t": itype,
                    "i": iid,
                    "s": ref_identifier.get("system"),
                    "v": ref_identifier.get("value"),
                },
            )


# The old child tables (listed explicitly: `medication_%` would also match the other Medication*
# resources) and the per-field enums of the old schema (`medication_status` stays).
_OLD_TABLES = (
    "medication_identifier_type_coding",
    "medication_identifier",
    "medication_code_coding",
    "medication_form_coding",
    "medication_ingredient_item_coding",
    "medication_ingredient",
)
_OLD_ENUMS = (
    "medication_identifier_assigner_reference_type",
    "medication_ingredient_item_reference_type",
    "medication_manufacturer_reference_type",
    "medication_quantity_comparator",
)

# Main-table columns that survive unchanged: the id, the audit/tenant columns, the status enum
# column and the manufacturer index columns (`manufacturer_type`'s enum becomes a plain string).
_KEEP = {
    "id",
    "medication_id",
    "tenant_id",
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
    "content",
    "status",
    "manufacturer_reference",
    "manufacturer_type",
    "manufacturer_id",
    "manufacturer_identifier_system",
    "manufacturer_identifier_value",
}


def _fk():
    return sa.Column(f"{P}_pk", sa.BigInteger(), sa.ForeignKey(f"{P}.id"), nullable=False)


def _index(table, *columns):
    op.create_index(op.f("ix_" + table + "_" + columns[0]), table, list(columns))


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column(P, sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
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

    op.alter_column(
        P, "manufacturer_type", type_=sa.String(), nullable=True, postgresql_using="manufacturer_type::text"
    )
    for name in _OLD_ENUMS:
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # The public id's sequence is now its server default.
    op.execute(f"ALTER TABLE {P} ALTER COLUMN medication_id SET DEFAULT nextval('medication_pub_seq')")

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

    op.add_column(P, sa.Column("expiration_start", sa.DateTime(timezone=True), nullable=True))
    op.add_column(P, sa.Column("expiration_end", sa.DateTime(timezone=True), nullable=True))
    op.add_column(P, sa.Column("lot_number", sa.String(), nullable=True))
    op.create_index("ix_medication_expiration", P, ["expiration_start", "expiration_end"])
    op.create_index("ix_medication_lot_number", P, ["lot_number"])

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
    op.create_index("ix_medication_token_param_code", f"{P}_token", ["param", "code"])

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
        "ix_medication_reference_param_type_id", f"{P}_reference", ["param", "reference_type", "reference_id"]
    )

    _rebuild_index(bind)
    op.alter_column(P, "content", nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "medication content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
