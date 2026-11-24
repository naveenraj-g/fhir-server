"""observation_definition: store the whole resource in `content` JSONB; nothing is indexed

Revision ID: a7b0c3d6e184
Revises: f6a9b2c5d073
Create Date: 2026-12-27 10:00:00.000000

Stores ObservationDefinition whole in `content` (see ObservationDefinitionModel's docstring),
like the other resources already moved (PlanDefinition f6a9b2c5d073, ...). The whole FHIR
resource - `identifier`, `category`, `code`, `permittedDataType`, `multipleResultsAllowed`,
`method`, `preferredReportName`, `quantitativeDetails`, `qualifiedInterval`, the four
`*CodedValueSet` references and `extension` - moves into `observation_definition.content`.

**R4 defines no search parameter for ObservationDefinition**, so there is no search index: no
index column and no index table. What survives of the old schema is the id, the public id with
its sequence as a server default, the tenant / audit columns and `content`; every old child table,
every other column and the per-field `observation_definition_*` enums are dropped.

upgrade: (1) builds `content` for every existing row from the old columns and tables - a frozen
copy of the old to_fhir_observation_definition() logic (but keeping a reference's raw string, so
an absolute URL is not lost), so this migration never depends on application code that has since
changed; (2) drops the old child tables / columns / enums.

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
revision: str = "a7b0c3d6e184"
down_revision: str | None = "f6a9b2c5d073"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

P = "observation_definition"

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
        "ObservationDefinition",
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


def _cc_by(bind, table, fk, pk, text):
    """A CodeableConcept from a `{table}` of codings keyed by `fk` and a text column."""
    return _concept(_rows_of(bind, table, fk, pk), text)


def _range(row, prefix):
    low, high = _q(row, f"{prefix}_low"), _q(row, f"{prefix}_high")
    return {"low": low, "high": high}


def _qualified_intervals(bind, pk):
    out = []
    for qi in _rows(
        bind,
        f"SELECT *, category::text AS category_text, gender::text AS gender_text "
        f"FROM {P}_qualified_interval WHERE {P}_pk = :v ORDER BY id",
        v=pk,
    ):
        applies = [
            _cc_by(
                bind,
                f"{P}_qualified_interval_applies_to_coding",
                "applies_to_id",
                a["id"],
                a["text"],
            )
            for a in _rows_of(
                bind,
                f"{P}_qualified_interval_applies_to",
                "qualified_interval_id",
                qi["id"],
            )
        ]
        out.append(
            {
                "category": _code(qi["category_text"]),
                "range": _range(qi, "range"),
                "context": _cc_by(
                    bind,
                    f"{P}_qualified_interval_context_coding",
                    "qualified_interval_id",
                    qi["id"],
                    qi["context_text"],
                ),
                "appliesTo": applies,
                "gender": _code(qi["gender_text"]),
                "age": _range(qi, "age"),
                "gestationalAge": _range(qi, "gestational_age"),
                "condition": qi["condition"],
            }
        )
    return out


def _build_content(bind, r):
    pk = r["id"]
    codings = lambda table: _rows_of(bind, table, f"{P}_pk", pk)
    categories = [
        _cc_by(bind, f"{P}_category_coding", "category_id", c["id"], c["text"])
        for c in _rows_of(bind, f"{P}_category", f"{P}_pk", pk)
    ]
    details = {
        "customaryUnit": _concept(
            codings(f"{P}_quantitative_details_customary_unit_coding"),
            r["quantitative_details_customary_unit_text"],
        ),
        "unit": _concept(
            codings(f"{P}_quantitative_details_unit_coding"),
            r["quantitative_details_unit_text"],
        ),
        "conversionFactor": _num(r["quantitative_details_conversion_factor"]),
        "decimalPrecision": r["quantitative_details_decimal_precision"],
    }
    content = {
        "extension": list(_json(r["extension"]) or []),
        "identifier": _identifiers(bind, pk),
        "category": categories,
        "code": _concept(codings(f"{P}_code_coding"), r["code_text"]),
        "permittedDataType": list(r["permitted_text"] or []),
        "multipleResultsAllowed": r["multiple_results_allowed"],
        "method": _concept(codings(f"{P}_method_coding"), r["method_text"]),
        "preferredReportName": r["preferred_report_name"],
        "quantitativeDetails": details,
        "qualifiedInterval": _qualified_intervals(bind, pk),
        "validCodedValueSet": _ref(r, "valid_coded_value_set"),
        "normalCodedValueSet": _ref(r, "normal_coded_value_set"),
        "abnormalCodedValueSet": _ref(r, "abnormal_coded_value_set"),
        "criticalCodedValueSet": _ref(r, "critical_coded_value_set"),
    }
    return _prune(content)


def _backfill_content(bind):
    # permitted_data_type is an array of an enum: cast it to text[] so the driver returns labels.
    for r in _rows(
        bind, f"SELECT *, permitted_data_type::text[] AS permitted_text FROM {P}"
    ):
        bind.execute(
            sa.text(f"UPDATE {P} SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {
                "c": json.dumps(_build_content(bind, dict(r)), default=str),
                "id": r["id"],
            },
        )


# The main-table columns that survive unchanged: the id, the audit/tenant columns and `content`.
# Everything else of the old table is dropped; so is every `observation_definition_*` child table
# and per-field enum (matched by prefix, which no other resource shares).
_KEEP = {
    "id",
    "observation_definition_id",
    "tenant_id",
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
    "content",
}


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column(
        P, sa.Column("content", postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    )
    _backfill_content(bind)

    # Every old child table (`observation_definition_*`), but not this table itself.
    for (table,) in bind.execute(
        sa.text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = current_schema() "
            "AND table_name LIKE 'observation\\_definition\\_%' AND table_type = 'BASE TABLE'"
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
            "AND typname LIKE 'observation\\_definition\\_%'"
        )
    ).all():
        op.execute(f'DROP TYPE IF EXISTS "{name}"')

    # The public id's sequence is now its server default.
    op.execute(
        f"ALTER TABLE {P} ALTER COLUMN observation_definition_id "
        "SET DEFAULT nextval('observation_definition_pub_seq')"
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
        f"ALTER TABLE {P} DROP CONSTRAINT IF EXISTS observation_definition_observation_definition_id_key"
    )
    for column in ("tenant_id", "created_at", "updated_at"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)
    op.create_index("ix_observation_definition_id", P, ["id"], if_not_exists=True)
    op.create_index(
        "ix_observation_definition_observation_definition_id",
        P,
        ["observation_definition_id"],
        unique=True,
        if_not_exists=True,
    )
    op.alter_column(P, "content", nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "observation_definition content migration is one-way: its old normalized tables are "
        "not rebuilt from `content`. Restore from a backup taken before upgrading."
    )
