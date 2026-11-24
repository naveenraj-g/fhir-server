"""communication: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: c3d6e9f2a740
Revises: b2c5d8e1f639
Create Date: 2026-12-23 20:00:00.000000

Stores Communication whole in `content` (see CommunicationModel's docstring), like the other
resources already moved (Consent b2c5d8e1f639, Flag a1b4c7d0e528, Task f0a3b6c9e417, ...). The
whole FHIR resource - `identifier`, `instantiatesCanonical/Uri`, `basedOn`, `partOf`,
`inResponseTo`, `status`, `statusReason`, `category`, `priority`, `medium`, `subject`, `topic`,
`about`, `encounter`, `sent`, `received`, `recipient`, `sender`, `reasonCode`, `reasonReference`,
`payload`, `note` and `extension` - moves into `communication.content`; every column/table that
survives is a search index for one of the FHIR R4 Communication search parameters (or `_id` /
`_lastUpdated`), derived from `content`:

  communication: status (the Postgres enum already held the true FHIR codes, so it stays, now
      nullable), sent_* and received_* (new: the range each dateTime covers - the old instants are
      dropped), the subject_*, encounter_* and sender_* reference columns (`*_type` become plain
      strings); the public id gets its sequence as a server default; new: content.
  communication_identifier: rebuilt as an index table
  communication_token: new - category and medium
  communication_reference: new - based-on, part-of, recipient and instantiates-canonical
  communication_instantiates_uri: new - one row per URI
  dropped: every other child table, every main-table column with no search parameter and the
      per-field `communication_*` enums (the status enum stays; **R4 defines no `priority` search
      parameter, so `communication_priority` is dropped and the value lives only in `content`**).

upgrade: (1) builds `content` for every existing row from the old columns and tables - a frozen
copy of the old to_fhir_communication() logic (but keeping a reference's raw string, so an absolute
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
revision: str = "c3d6e9f2a740"
down_revision: Union[str, None] = "b2c5d8e1f639"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

P = "communication"

_STATUS = (
    "preparation",
    "in-progress",
    "not-done",
    "on-hold",
    "stopped",
    "completed",
    "entered-in-error",
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


def _range(value):
    return _bounds(value) if isinstance(value, str) and value else (None, None)


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
                bind,
                "communication_identifier_type_coding",
                "communication_identifier_id",
                i["id"],
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


def _payload(p):
    """content[x]: the string, else the Attachment (any attachment column set), else the
    Reference."""
    if p["content_string"] is not None:
        return {"contentString": p["content_string"]}
    attachment = {
        "contentType": p["content_attachment_content_type"],
        "language": p["content_attachment_language"],
        "data": p["content_attachment_data"],
        "url": p["content_attachment_url"],
        "size": p["content_attachment_size"],
        "hash": p["content_attachment_hash"],
        "title": p["content_attachment_title"],
        "creation": _iso(p["content_attachment_creation"]),
    }
    if _prune(attachment):
        return {"contentAttachment": attachment}
    return {"contentReference": _ref(p, "content_reference")}


def _build_content(bind, r):
    pk = r["id"]

    def by_pk(table):
        return _rows_of(bind, f"{P}_{table}", f"{P}_pk", pk)

    def cc_list(table):
        return [
            _concept(
                _rows_of(bind, f"{P}_{table}_coding", f"{P}_{table}_id", row["id"]),
                row["text"],
            )
            for row in by_pk(table)
        ]

    content = {
        "extension": list(_json(r["extension"]) or []),
        "identifier": [_own_identifier(bind, i) for i in by_pk("identifier")],
        "instantiatesCanonical": list(r["instantiates_canonical"] or []),
        "instantiatesUri": list(r["instantiates_uri"] or []),
        "basedOn": [_ref(x, "reference") for x in by_pk("based_on")],
        "partOf": [_ref(x, "reference") for x in by_pk("part_of")],
        "inResponseTo": [_ref(x, "reference") for x in by_pk("in_response_to")],
        "status": r["status_text"],
        "statusReason": _concept(
            by_pk("status_reason_coding"), r["status_reason_text"]
        ),
        "category": cc_list("category"),
        "priority": r["priority_text"],
        "medium": cc_list("medium"),
        "subject": _ref(r, "subject"),
        "topic": _concept(by_pk("topic_coding"), r["topic_text"]),
        "about": [_ref(x, "reference") for x in by_pk("about")],
        "encounter": _ref(r, "encounter"),
        "sent": _iso(r["sent"]),
        "received": _iso(r["received"]),
        "recipient": [_ref(x, "reference") for x in by_pk("recipient")],
        "sender": _ref(r, "sender"),
        "reasonCode": cc_list("reason_code"),
        "reasonReference": [_ref(x, "reference") for x in by_pk("reason_reference")],
        "payload": [_payload(p) for p in by_pk("payload")],
        "note": [_note(n) for n in by_pk("note")],
    }
    return _prune(content)


def _backfill_content(bind):
    # status / priority are enums: cast them to text so the driver returns the label.
    for r in _rows(
        bind,
        f"SELECT *, status::text AS status_text, priority::text AS priority_text FROM {P}",
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
_SUBJECT_TYPES = ("Patient", "Group")
_ENCOUNTER_TYPES = ("Encounter",)
_SENDER_TYPES = (
    "Device",
    "Organization",
    "Patient",
    "Practitioner",
    "PractitionerRole",
    "RelatedPerson",
    "HealthcareService",
)
_RECIPIENT_TYPES = (
    "Device",
    "Organization",
    "Patient",
    "Practitioner",
    "PractitionerRole",
    "RelatedPerson",
    "Group",
    "CareTeam",
    "HealthcareService",
)
_CANONICAL_TYPES = (
    "PlanDefinition",
    "ActivityDefinition",
    "Measure",
    "OperationDefinition",
    "Questionnaire",
)


def _typed(reference, allowed):
    """allowed None = a Reference(Any): any relative `Type/<id>` names a type."""
    match = _REF.match(reference or "")
    if match and (allowed is None or match["type"] in allowed):
        return match["type"], int(match["id"])
    return None, None


def _ref_params(prefix, ref, allowed):
    ref = ref if isinstance(ref, dict) else {}
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


def _insert_reference(bind, pk, param, ref, allowed):
    if not isinstance(ref, dict):
        return
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
        sent = _range(doc.get("sent"))
        received = _range(doc.get("received"))
        status = doc.get("status")
        columns = {
            "sent_start": sent[0],
            "sent_end": sent[1],
            "received_start": received[0],
            "received_end": received[1],
            **_ref_params("subject", doc.get("subject"), _SUBJECT_TYPES),
            **_ref_params("encounter", doc.get("encounter"), _ENCOUNTER_TYPES),
            **_ref_params("sender", doc.get("sender"), _SENDER_TYPES),
        }
        sets = ", ".join(f"{k} = :{k}" for k in columns)
        bind.execute(
            sa.text(
                f"UPDATE {P} SET status = CAST(:status AS communication_status), {sets} "
                "WHERE id = :pk"
            ),
            {**columns, "status": status if status in _STATUS else None, "pk": pk},
        )
        for i in doc.get("identifier") or []:
            _insert_identifier(bind, pk, i)
        for category in doc.get("category") or []:
            _insert_token(bind, pk, "category", category)
        for medium in doc.get("medium") or []:
            _insert_token(bind, pk, "medium", medium)
        for ref in doc.get("basedOn") or []:
            _insert_reference(bind, pk, "based-on", ref, None)
        for ref in doc.get("partOf") or []:
            _insert_reference(bind, pk, "part-of", ref, None)
        for ref in doc.get("recipient") or []:
            _insert_reference(bind, pk, "recipient", ref, _RECIPIENT_TYPES)
        for canonical in doc.get("instantiatesCanonical") or []:
            _insert_reference(
                bind,
                pk,
                "instantiates-canonical",
                {"reference": canonical},
                _CANONICAL_TYPES,
            )
        for uri in doc.get("instantiatesUri") or []:
            if isinstance(uri, str) and uri:
                bind.execute(
                    sa.text(
                        f"INSERT INTO {P}_instantiates_uri ({P}_pk, uri) VALUES (:pk, :u)"
                    ),
                    {"pk": pk, "u": uri},
                )


# Main-table columns that survive unchanged: the id, the audit/tenant columns, the status (an
# enum that already held the true FHIR codes) and the subject / encounter / sender index columns
# (their reference-type enums become plain strings). The sent / received range columns are new.
_REF_PARTS = ("reference", "type", "id", "identifier_system", "identifier_value")
_KEEP = {
    "id",
    "communication_id",
    "tenant_id",
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
    "content",
    "status",
    *(
        f"{prefix}_{part}"
        for prefix in ("subject", "encounter", "sender")
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
            "AND table_name LIKE 'communication\\_%' "
            "AND table_name NOT LIKE 'communication\\_request%' "
            "AND table_type = 'BASE TABLE'"
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

    # The reference types were enums; they are plain strings now.
    for prefix in ("subject", "encounter", "sender"):
        op.alter_column(
            P,
            f"{prefix}_type",
            type_=sa.String(),
            nullable=True,
            postgresql_using=f"{prefix}_type::text",
        )
    # Every per-field `communication_*` enum of the old schema except the status.
    for (name,) in bind.execute(
        sa.text(
            "SELECT typname FROM pg_type WHERE typtype = 'e' AND typname LIKE 'communication\\_%' "
            "AND typname <> 'communication_status' "
            "AND typname NOT LIKE 'communication\\_request%'"
        )
    ).all():
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # Communications are searched by subject: one index on the pair instead of the lone id.
    op.execute(f"DROP INDEX IF EXISTS ix_{P}_subject_id")
    # The public id's sequence is now its server default.
    op.execute(
        f"ALTER TABLE {P} ALTER COLUMN communication_id SET DEFAULT nextval('communication_pub_seq')"
    )

    # The audit columns as the shared mixin declares them (the original table was created with
    # looser ones): tenant/actor NOT NULL, timestamps nullable and indexed, and no UNIQUE on the
    # public id (the sequence keeps it unique).
    # tenant_id was a bigint in this table; the shared mixin declares a string.
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
        f"ALTER TABLE {P} DROP CONSTRAINT IF EXISTS communication_communication_id_key"
    )
    for column in ("id", "tenant_id", "created_at", "updated_at"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)

    # status: the enum stays; the column is nullable (an index, not a requirement).
    op.alter_column(
        P,
        "status",
        existing_type=postgresql.ENUM(
            *_STATUS, name="communication_status", create_type=False
        ),
        nullable=True,
    )
    for column in ("sent_start", "sent_end", "received_start", "received_end"):
        op.add_column(P, sa.Column(column, sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_communication_sent", P, ["sent_start", "sent_end"])
    op.create_index("ix_communication_received", P, ["received_start", "received_end"])
    op.create_index(
        "ix_communication_subject_type_id", P, ["subject_type", "subject_id"]
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
        "ix_communication_token_param_code", f"{P}_token", ["param", "code"]
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
        "ix_communication_reference_param_type_id",
        f"{P}_reference",
        ["param", "reference_type", "reference_id"],
    )

    op.create_table(
        f"{P}_instantiates_uri",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column("uri", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(f"{P}_instantiates_uri", f"{P}_pk")
    _index(f"{P}_instantiates_uri", "uri")

    _rebuild_index(bind)
    op.create_index("ix_communication_status", P, ["status"], if_not_exists=True)
    for column in ("encounter_id", "sender_id"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)
    op.create_index(
        "ix_communication_communication_id",
        P,
        ["communication_id"],
        unique=True,
        if_not_exists=True,
    )
    op.alter_column(P, "content", nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "communication content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
