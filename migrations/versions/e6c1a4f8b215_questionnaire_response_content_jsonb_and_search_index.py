"""questionnaire_response: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: e6c1a4f8b215
Revises: d5b9e2f7a103
Create Date: 2026-12-18 10:00:00.000000

Stores QuestionnaireResponse whole in `content` (see QuestionnaireResponseModel's docstring), like
the other resources already moved (CareTeam d7c2e9a5b361, EpisodeOfCare c4a8d1e6f092,
DocumentReference d5b9e2f7a103, ...). The whole FHIR resource - including the nested `item` /
`answer` / `answer.item` tree - moves into `questionnaire_response.content`; every column/table that
survives is a search index for one of the FHIR R4 QuestionnaireResponse search parameters (or `_id` /
`_lastUpdated`), derived from `content`:

  questionnaire_response: status (recreated as an enum holding the real FHIR codes - the old one
      stored `in_progress` / `entered_in_error`), authored_start/_end (new: the range the dateTime
      covers; the old `authored` instant is dropped), the subject_*, encounter_*, author_* and
      source_* columns (`*_type` become plain strings); the public id gets its sequence as a server
      default; new: content.
  questionnaire_response_identifier: rebuilt as an index table
  questionnaire_response_reference: new - based-on, part-of, questionnaire (the canonical URL)
  dropped: the item / answer tables (the whole answer tree now lives in `content`), the
      identifier type coding, based_on and part_of tables, every main-table column with no search
      parameter (the identifier columns, extension and the display / logical-identifier details of
      every reference) and the per-field `questionnaire_response_*` enums.

upgrade: (1) builds `content` for every existing row from the old columns and tables - a frozen
copy of the old to_fhir_questionnaire_response() logic, including rebuilding the nested item and
answer tree from the flat tables (but keeping a reference's raw string, so an absolute URL is not
lost), so this migration never depends on application code that has since changed; (2) drops the
old child tables/columns and creates the index tables; (3) rebuilds the index from `content`.

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
revision: str = "e6c1a4f8b215"
down_revision: Union[str, None] = "d5b9e2f7a103"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

P = "questionnaire_response"

_STATUS = ("in-progress", "completed", "amended", "entered-in-error", "stopped")
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
    """The FHIR code for an old enum label (`entered_in_error` becomes `entered-in-error`)."""
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
        "Encounter",
        "CarePlan",
        "ServiceRequest",
        "Observation",
        "Procedure",
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


def _identifier(bind, r):
    """The old schema flattened the one identifier onto the main row (its type codings in their
    own table)."""
    return {
        "use": r["identifier_use"],
        "type": {
            "coding": [
                _coding(c)
                for c in _rows_of(
                    bind, f"{P}_identifier_type_coding", f"{P}_pk", r["id"]
                )
            ],
            "text": r["identifier_type_text"],
        },
        "system": r["identifier_system"],
        "value": r["identifier_value"],
        "period": _period(r["identifier_period_start"], r["identifier_period_end"]),
        "assigner": _ref(r, "identifier_assigner"),
    }


def _num(value):
    return float(value) if isinstance(value, Decimal) else value


def _answer_value(a):
    """One answer's value[x], in the old mapper's precedence order."""
    entry = {}
    if a["value_boolean"] is not None:
        entry["valueBoolean"] = a["value_boolean"]
    elif a["value_decimal"] is not None:
        entry["valueDecimal"] = _num(a["value_decimal"])
    elif a["value_integer"] is not None:
        entry["valueInteger"] = a["value_integer"]
    elif a["value_date"] is not None:
        entry["valueDate"] = _iso(a["value_date"])
    elif a["value_date_time"] is not None:
        entry["valueDateTime"] = _iso(a["value_date_time"])
    elif a["value_time"] is not None:
        entry["valueTime"] = _iso(a["value_time"])
    elif a["value_string"] is not None:
        entry["valueString"] = a["value_string"]
    elif a["value_uri"] is not None:
        entry["valueUri"] = a["value_uri"]
    elif (
        a["value_attachment_content_type"]
        or a["value_attachment_url"]
        or a["value_attachment_data"]
        or a["value_attachment_title"]
    ):
        entry["valueAttachment"] = {
            "contentType": a["value_attachment_content_type"],
            "language": a["value_attachment_language"],
            "data": a["value_attachment_data"],
            "url": a["value_attachment_url"],
            "size": a["value_attachment_size"],
            "hash": a["value_attachment_hash"],
            "title": a["value_attachment_title"],
            "creation": _iso(a["value_attachment_creation"]),
        }
    elif a["value_coding_system"] or a["value_coding_code"]:
        entry["valueCoding"] = {
            "system": a["value_coding_system"],
            "version": a["value_coding_version"],
            "code": a["value_coding_code"],
            "display": a["value_coding_display"],
            "userSelected": a["value_coding_user_selected"],
        }
    elif (
        a["value_quantity_value"] is not None
        or a["value_quantity_unit"]
        or a["value_quantity_system"]
        or a["value_quantity_code"]
    ):
        entry["valueQuantity"] = {
            "value": _num(a["value_quantity_value"]),
            "comparator": _COMPARATOR.get(a["comparator_text"], a["comparator_text"]),
            "unit": a["value_quantity_unit"],
            "system": a["value_quantity_system"],
            "code": a["value_quantity_code"],
        }
    elif (
        a["value_reference_reference"]
        or (a["value_reference_type"] and a["value_reference_id"])
        or a["value_reference_identifier_value"]
    ):
        entry["valueReference"] = _ref(a, "value_reference")
    return entry


def _item_tree(items, answers):
    """Rebuild the nested item[] / answer[].item[] shape from the flat tables: an item is a child
    of another item (`parent_item_id`) XOR of one specific answer (`parent_answer_id`)."""
    by_parent_item, by_parent_answer = {}, {}
    for item in items:
        if item["parent_answer_id"] is not None:
            by_parent_answer.setdefault(item["parent_answer_id"], []).append(item)
        else:
            by_parent_item.setdefault(item["parent_item_id"], []).append(item)
    answers_by_item = {}
    for answer in answers:
        answers_by_item.setdefault(answer["item_id"], []).append(answer)

    def render_answer(a):
        entry = _answer_value(a)
        children = render_items(by_parent_answer.get(a["id"], []))
        if children:
            entry["item"] = children
        return entry

    def render_items(item_list):
        out = []
        for item in item_list:
            entry = {"linkId": item["link_id"]}
            if item["definition"]:
                entry["definition"] = item["definition"]
            if item["text"]:
                entry["text"] = item["text"]
            rendered = [render_answer(a) for a in answers_by_item.get(item["id"], [])]
            if rendered:
                entry["answer"] = rendered
            children = render_items(by_parent_item.get(item["id"], []))
            if children:
                entry["item"] = children
            out.append(entry)
        return out

    return render_items(by_parent_item.get(None, []))


def _build_content(bind, r):
    pk = r["id"]
    items = _rows_of(bind, f"{P}_item", f"{P}_pk", pk)
    answers = _rows(
        bind,
        f"SELECT *, value_quantity_comparator::text AS comparator_text FROM {P}_answer "
        f"WHERE {P}_pk = :v ORDER BY id",
        v=pk,
    )
    content = {
        "extension": list(_json(r["extension"]) or []),
        "identifier": _identifier(bind, r),
        "basedOn": [
            _ref(x, "reference") for x in _rows_of(bind, f"{P}_based_on", f"{P}_pk", pk)
        ],
        "partOf": [
            _ref(x, "reference") for x in _rows_of(bind, f"{P}_part_of", f"{P}_pk", pk)
        ],
        "questionnaire": r["questionnaire"],
        "status": _hyphenate(r["status_text"]),
        "subject": _ref(r, "subject"),
        "encounter": _ref(r, "encounter"),
        "authored": _iso(r["authored"]),
        "author": _ref(r, "author"),
        "source": _ref(r, "source"),
        "item": _item_tree(items, answers),
    }
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


# -- upgrade: content -> search index (frozen copy of _indexer.py) --------------------------

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")
_ENCOUNTER_TYPES = ("Encounter",)
_AUTHOR_TYPES = (
    "Practitioner",
    "PractitionerRole",
    "Organization",
    "Device",
    "Patient",
    "RelatedPerson",
)
_SOURCE_TYPES = ("Practitioner", "Patient", "PractitionerRole", "RelatedPerson")
_REFERENCE_TYPES = {
    "based-on": ("CarePlan", "ServiceRequest"),
    "part-of": ("Observation", "Procedure"),
    "questionnaire": ("Questionnaire",),
}


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
        authored = doc.get("authored")
        start = _bounds(authored)[0] if authored else None
        end = _bounds(authored)[1] if authored else None
        status = doc.get("status")
        columns = {
            "authored_start": start,
            "authored_end": end,
            **_ref_params("subject", doc.get("subject"), None),
            **_ref_params("encounter", doc.get("encounter"), _ENCOUNTER_TYPES),
            **_ref_params("author", doc.get("author"), _AUTHOR_TYPES),
            **_ref_params("source", doc.get("source"), _SOURCE_TYPES),
        }
        sets = ", ".join(f"{k} = :{k}" for k in columns)
        bind.execute(
            sa.text(
                f"UPDATE {P} SET status = CAST(:status AS questionnaire_response_status), "
                f"{sets} WHERE id = :pk"
            ),
            {**columns, "status": status if status in _STATUS else None, "pk": pk},
        )

        if doc.get("identifier"):
            _insert_identifier(bind, pk, doc["identifier"])
        for ref in doc.get("basedOn") or []:
            _insert_reference(bind, pk, "based-on", ref)
        for ref in doc.get("partOf") or []:
            _insert_reference(bind, pk, "part-of", ref)
        if doc.get("questionnaire"):
            _insert_reference(
                bind, pk, "questionnaire", {"reference": doc["questionnaire"]}
            )


# Every old QuestionnaireResponse table. The new index table (identifier) is dropped with them and
# recreated below; dropped with CASCADE, so order does not matter.
_OLD_TABLES = (
    "questionnaire_response_answer",
    "questionnaire_response_item",
    "questionnaire_response_identifier_type_coding",
    "questionnaire_response_based_on",
    "questionnaire_response_part_of",
)

# Main-table columns that survive unchanged: the id, the audit/tenant columns and the subject /
# encounter / author / source index columns (their reference-type enums become plain strings).
_KEEP = {
    "id",
    "questionnaire_response_id",
    "tenant_id",
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
    "content",
    *(
        f"{ref}_{part}"
        for ref in ("subject", "encounter", "author", "source")
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

    # The subject / encounter / author / source types were enums (or already strings); they are
    # plain strings now.
    for column in ("subject_type", "encounter_type", "author_type", "source_type"):
        op.alter_column(
            P,
            column,
            type_=sa.String(),
            nullable=True,
            postgresql_using=f"{column}::text",
        )
    # Every per-field `questionnaire_response_*` enum of the old schema, status included (it is
    # recreated below with the real FHIR codes). The shared `identifier_use` does not start with
    # this prefix.
    for name in [
        r[0]
        for r in bind.execute(
            sa.text(
                "SELECT typname FROM pg_type WHERE typtype = 'e' "
                "AND typname LIKE 'questionnaire\\_response\\_%'"
            )
        )
    ]:
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # Responses are searched by subject: one index on the pair instead of the lone id.
    op.execute(f"DROP INDEX IF EXISTS ix_{P}_subject_id")
    # The public id's sequence is now its server default.
    op.execute(
        f"ALTER TABLE {P} ALTER COLUMN questionnaire_response_id "
        "SET DEFAULT nextval('questionnaire_response_pub_seq')"
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
        f"ALTER TABLE {P} DROP CONSTRAINT IF EXISTS "
        "questionnaire_response_questionnaire_response_id_key"
    )
    for column in ("tenant_id", "created_at", "updated_at"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)

    # status: recreated as an enum holding the real FHIR codes.
    postgresql.ENUM(*_STATUS, name="questionnaire_response_status").create(
        bind, checkfirst=True
    )
    op.add_column(
        P,
        sa.Column(
            "status",
            postgresql.ENUM(
                *_STATUS, name="questionnaire_response_status", create_type=False
            ),
            nullable=True,
        ),
    )
    op.add_column(
        P, sa.Column("authored_start", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        P, sa.Column("authored_end", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_index(
        "ix_questionnaire_response_authored", P, ["authored_start", "authored_end"]
    )
    op.create_index(
        "ix_questionnaire_response_subject_type_id", P, ["subject_type", "subject_id"]
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
        "ix_questionnaire_response_reference_param_type_id",
        f"{P}_reference",
        ["param", "reference_type", "reference_id"],
    )

    _rebuild_index(bind)
    for column in ("id", "encounter_id", "author_id", "source_id", "status"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)
    op.create_index(
        f"ix_{P}_questionnaire_response_id",
        P,
        ["questionnaire_response_id"],
        unique=True,
        if_not_exists=True,
    )
    op.alter_column(P, "content", nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "questionnaire_response content/index migration is one-way: its old normalized tables "
        "are not rebuilt from `content`. Restore from a backup taken before upgrading."
    )
