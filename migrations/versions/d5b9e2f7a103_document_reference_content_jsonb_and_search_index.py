"""document_reference: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: d5b9e2f7a103
Revises: c4a8d1e6f092
Create Date: 2026-12-17 10:00:00.000000

Medplum-style storage for DocumentReference (see DocumentReferenceModel's docstring), same as the
other resources already moved (CareTeam d7c2e9a5b361, CarePlan e8d3f0b6c472, EpisodeOfCare
c4a8d1e6f092, ...). The whole FHIR resource moves into `document_reference.content`; every
column/table that survives is a search index for one of the FHIR R4 DocumentReference search
parameters (or `_id` / `_lastUpdated`), derived from `content`:

  document_reference: status (the enum already held the real FHIR codes, so it stays; now
      nullable), date, description (+ new description_norm), context_period_start/_end
      (`context.period`, the half-open range it covers; recomputed), the subject_*,
      authenticator_* and custodian_* reference columns (`*_type` become plain strings); the
      public id gets its sequence as a server default; new: content.
  document_reference_identifier: rebuilt as an index table (masterIdentifier and identifier)
  document_reference_token: new - type, category, security-label, event, facility, setting
  document_reference_reference: new - author, encounter (context.encounter), related
      (context.related)
  document_reference_relates_to: rebuilt as an index table (code is the enum
      `document_relationship_type`, which stays)
  document_reference_content: rebuilt as an index table (contentType, language, url, format)
  dropped: every other old child table (identifier/master identifier/type/category/security label
      codings, author, context encounter/event/related/facility/practice setting), every
      main-table column with no search parameter (docStatus, extension, sourcePatientInfo and the
      display / logical-identifier details of every reference), the `document_reference_doc_status`
      enum and the per-field `document_reference_*` reference-type enums.

upgrade: (1) builds `content` for every existing row from the old columns and tables - a frozen
copy of the old to_fhir_document_reference() logic (but keeping a reference's raw string, so an
absolute URL is not lost), so this migration never depends on application code that has since
changed; (2) drops the old child tables/columns and creates the index tables; (3) rebuilds the
index from `content`.

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
revision: str = "d5b9e2f7a103"
down_revision: Union[str, None] = "c4a8d1e6f092"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

P = "document_reference"

_STATUS = ("current", "superseded", "entered-in-error")
_RELATION = ("replaces", "transforms", "signs", "appends")


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


def _period_bounds(period):
    """(start, end) of a Period: the first instant it covers and the first instant after it (None
    = open on that side). Frozen copy of app.repository._content_index.period_bounds."""
    period = period or {}
    start = _bounds(period.get("start"))[0] if period.get("start") else None
    end = _bounds(period.get("end"))[1] if period.get("end") else None
    return start, end


def _instant(value):
    """A FHIR instant as a UTC datetime (None if absent or unparseable)."""
    return _bounds(value)[0]


# -- upgrade: old columns/tables -> content (frozen copy of the old mapper) -----------------

_TYPE_NAMES = {
    t.upper(): t
    for t in (
        "Patient",
        "Practitioner",
        "PractitionerRole",
        "Organization",
        "Device",
        "Group",
        "RelatedPerson",
        "Encounter",
        "EpisodeOfCare",
        "DocumentReference",
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


def _concept(codings, text):
    return {"coding": [_coding(c) for c in codings], "text": text}


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
    raw = row[f"{prefix}_reference"]
    if not raw and row[f"{prefix}_type"] and row[f"{prefix}_id"]:
        ref_type = str(row[f"{prefix}_type"])
        raw = f"{_TYPE_NAMES.get(ref_type.upper(), ref_type)}/{row[f'{prefix}_id']}"
    return {
        "reference": raw,
        "display": row.get(f"{prefix}_display"),
        "identifier": _fallback_identifier(row, f"{prefix}_identifier"),
    }


def _rows_of(bind, table, fk, value):
    return _rows(bind, f"SELECT * FROM {table} WHERE {fk} = :v ORDER BY id", v=value)


def _identifier(bind, i):
    return {
        "use": i["use"],
        "type": _concept(
            _rows_of(
                bind,
                f"{P}_identifier_type_coding",
                f"{P}_identifier_id",
                i["id"],
            ),
            i["type_text"],
        ),
        "system": i["system"],
        "value": i["value"],
        "period": _period(i["period_start"], i["period_end"]),
        "assigner": _ref(i, "assigner"),
    }


def _master_identifier(bind, r):
    return {
        "use": r["master_identifier_use"],
        "type": _concept(
            _rows_of(bind, f"{P}_master_identifier_type_coding", f"{P}_pk", r["id"]),
            r["master_identifier_type_text"],
        ),
        "system": r["master_identifier_system"],
        "value": r["master_identifier_value"],
        "period": _period(
            r["master_identifier_period_start"], r["master_identifier_period_end"]
        ),
        "assigner": _ref(r, "master_identifier_assigner"),
    }


def _content_entry(c):
    return {
        # the old table prefixes its attachment columns with `attachment_`
        "attachment": {
            "contentType": c["attachment_content_type"],
            "language": c["attachment_language"],
            "data": c["attachment_data"],
            "url": c["attachment_url"],
            "size": c["attachment_size"],
            "hash": c["attachment_hash"],
            "title": c["attachment_title"],
            "creation": _iso(c["attachment_creation"]),
        },
        "format": {
            "system": c["format_system"],
            "version": c["format_version"],
            "code": c["format_code"],
            "display": c["format_display"],
            "userSelected": c["format_user_selected"],
        },
    }


def _build_content(bind, r):
    pk = r["id"]
    content = {
        "extension": list(_json(r["extension"]) or []),
        "masterIdentifier": _master_identifier(bind, r),
        "identifier": [
            _identifier(bind, i)
            for i in _rows_of(bind, f"{P}_identifier", f"{P}_pk", pk)
        ],
        "status": _hyphenate(r["status_text"]),
        "docStatus": _hyphenate(r["doc_status_text"]),
        "type": _concept(
            _rows_of(bind, f"{P}_type_coding", f"{P}_pk", pk), r["type_text"]
        ),
        "category": [
            _concept(
                _rows_of(bind, f"{P}_category_coding", f"{P}_category_id", c["id"]),
                c["text"],
            )
            for c in _rows_of(bind, f"{P}_category", f"{P}_pk", pk)
        ],
        "subject": _ref(r, "subject"),
        "date": _iso(r["date"]),
        "author": [
            _ref(a, "author") for a in _rows_of(bind, f"{P}_author", f"{P}_pk", pk)
        ],
        "authenticator": _ref(r, "authenticator"),
        "custodian": _ref(r, "custodian"),
        "relatesTo": [
            {"code": x["code_text"], "target": _ref(x, "target")}
            for x in _rows(
                bind,
                f"SELECT *, code::text AS code_text FROM {P}_relates_to "
                f"WHERE {P}_pk = :v ORDER BY id",
                v=pk,
            )
        ],
        "description": r["description"],
        "securityLabel": [
            _concept(
                _rows_of(
                    bind,
                    f"{P}_security_label_coding",
                    f"{P}_security_label_id",
                    s["id"],
                ),
                s["text"],
            )
            for s in _rows_of(bind, f"{P}_security_label", f"{P}_pk", pk)
        ],
        "content": [
            _content_entry(c) for c in _rows_of(bind, f"{P}_content", f"{P}_pk", pk)
        ],
        "context": {
            "encounter": [
                _ref(e, "reference")
                for e in _rows_of(bind, f"{P}_context_encounter", f"{P}_pk", pk)
            ],
            "event": [
                _concept(
                    _rows_of(
                        bind,
                        f"{P}_context_event_coding",
                        f"{P}_context_event_id",
                        e["id"],
                    ),
                    e["text"],
                )
                for e in _rows_of(bind, f"{P}_context_event", f"{P}_pk", pk)
            ],
            "period": _period(r["context_period_start"], r["context_period_end"]),
            "facilityType": _concept(
                _rows_of(bind, f"{P}_context_facility_type_coding", f"{P}_pk", pk),
                r["context_facility_type_text"],
            ),
            "practiceSetting": _concept(
                _rows_of(bind, f"{P}_context_practice_setting_coding", f"{P}_pk", pk),
                r["context_practice_setting_text"],
            ),
            "sourcePatientInfo": _ref(r, "context_source_patient_info"),
            "related": [
                _ref(x, "reference")
                for x in _rows_of(bind, f"{P}_context_related", f"{P}_pk", pk)
            ],
        },
    }
    return _prune(content)


def _backfill_content(bind):
    # `status` / `doc_status` are enums: cast them to text so the driver returns the label.
    for r in _rows(
        bind,
        f"SELECT *, status::text AS status_text, doc_status::text AS doc_status_text FROM {P}",
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
_SUBJECT_TYPES = ("Patient", "Practitioner", "Group", "Device")
_AUTHENTICATOR_TYPES = ("Practitioner", "Organization", "PractitionerRole")
_CUSTODIAN_TYPES = ("Organization",)
_AUTHOR_TYPES = (
    "Practitioner",
    "PractitionerRole",
    "Organization",
    "Device",
    "Patient",
    "RelatedPerson",
)
_ENCOUNTER_TYPES = ("Encounter", "EpisodeOfCare")
_RELATES_TO_TYPES = ("DocumentReference",)


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


def _insert_relates_to(bind, pk, entry):
    entry = entry or {}
    code = entry.get("code")
    target = entry.get("target") or {}
    reference = target.get("reference")
    identifier = target.get("identifier") or {}
    if not (code or reference or identifier.get("value")):
        return
    rtype, rid = _typed(reference, _RELATES_TO_TYPES)
    bind.execute(
        sa.text(
            f"INSERT INTO {P}_relates_to ({P}_pk, code, target_reference, target_type, "
            "target_id, target_identifier_system, target_identifier_value) VALUES "
            "(:pk, CAST(:code AS document_relationship_type), :r, :t, :i, :s, :v)"
        ),
        {
            "pk": pk,
            "code": code if code in _RELATION else None,
            "r": reference,
            "t": rtype,
            "i": rid,
            "s": identifier.get("system"),
            "v": identifier.get("value"),
        },
    )


def _insert_content(bind, pk, entry):
    entry = entry or {}
    attachment = entry.get("attachment") or {}
    fmt = entry.get("format") or {}
    values = {
        "ct": attachment.get("contentType"),
        "lang": attachment.get("language"),
        "url": attachment.get("url"),
        "fs": fmt.get("system"),
        "fc": fmt.get("code"),
        "fd": _norm(fmt.get("display")),
    }
    if not any(values.values()):
        return
    bind.execute(
        sa.text(
            f"INSERT INTO {P}_content ({P}_pk, content_type, language, url, format_system, "
            "format_code, format_display_norm) VALUES (:pk, :ct, :lang, :url, :fs, :fc, :fd)"
        ),
        {"pk": pk, **values},
    )


def _rebuild_index(bind):
    for row in _rows(bind, f"SELECT id, content FROM {P}"):
        pk, doc = row["id"], _json(row["content"])
        context = doc.get("context") or {}
        start, end = _period_bounds(context.get("period"))
        status = doc.get("status")
        description = doc.get("description")
        columns = {
            "date": _instant(doc.get("date")),
            "description": description,
            "description_norm": _norm(description) if description else None,
            "context_period_start": start,
            "context_period_end": end,
            **_ref_params("subject", doc.get("subject"), _SUBJECT_TYPES),
            **_ref_params(
                "authenticator", doc.get("authenticator"), _AUTHENTICATOR_TYPES
            ),
            **_ref_params("custodian", doc.get("custodian"), _CUSTODIAN_TYPES),
        }
        sets = ", ".join(f"{k} = :{k}" for k in columns)
        bind.execute(
            sa.text(
                f"UPDATE {P} SET status = CAST(:status AS document_reference_status), {sets} "
                "WHERE id = :pk"
            ),
            {**columns, "status": status if status in _STATUS else None, "pk": pk},
        )

        for i in [doc.get("masterIdentifier"), *(doc.get("identifier") or [])]:
            if i:
                _insert_identifier(bind, pk, i)
        for param, values in (
            ("type", [doc.get("type")]),
            ("category", doc.get("category") or []),
            ("security-label", doc.get("securityLabel") or []),
            ("event", context.get("event") or []),
            ("facility", [context.get("facilityType")]),
            ("setting", [context.get("practiceSetting")]),
        ):
            for concept in values:
                _insert_token(bind, pk, param, concept)
        for ref in doc.get("author") or []:
            _insert_reference(bind, pk, "author", ref, _AUTHOR_TYPES)
        for ref in context.get("encounter") or []:
            _insert_reference(bind, pk, "encounter", ref, _ENCOUNTER_TYPES)
        for ref in context.get("related") or []:
            _insert_reference(bind, pk, "related", ref, None)
        for entry in doc.get("relatesTo") or []:
            _insert_relates_to(bind, pk, entry)
        for entry in doc.get("content") or []:
            _insert_content(bind, pk, entry)


# Every old DocumentReference table. The new index tables (identifier, relates_to, content) are
# dropped with them and recreated below; dropped with CASCADE, so order does not matter.
_OLD_TABLES = (
    "document_reference_identifier_type_coding",
    "document_reference_identifier",
    "document_reference_master_identifier_type_coding",
    "document_reference_type_coding",
    "document_reference_category_coding",
    "document_reference_category",
    "document_reference_author",
    "document_reference_relates_to",
    "document_reference_security_label_coding",
    "document_reference_security_label",
    "document_reference_content",
    "document_reference_context_encounter",
    "document_reference_context_event_coding",
    "document_reference_context_event",
    "document_reference_context_related",
    "document_reference_context_facility_type_coding",
    "document_reference_context_practice_setting_coding",
)

# Main-table columns that survive unchanged: the id, the audit/tenant columns, status, date,
# description, the context period and the subject / authenticator / custodian index columns
# (their reference-type enums become plain strings).
_KEEP = {
    "id",
    "document_reference_id",
    "tenant_id",
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
    "content",
    "status",
    "date",
    "description",
    "context_period_start",
    "context_period_end",
    *(
        f"{ref}_{part}"
        for ref in ("subject", "authenticator", "custodian")
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

    # The subject / authenticator / custodian types were enums; they are plain strings now.
    for column in ("subject_type", "authenticator_type", "custodian_type"):
        op.alter_column(
            P,
            column,
            type_=sa.String(),
            nullable=True,
            postgresql_using=f"{column}::text",
        )
    # The per-field `document_reference_*` enums of the old schema (every one except the status,
    # which stays: it already held the real FHIR codes). `document_relationship_type` does not
    # start with this prefix and stays too.
    for name in [
        r[0]
        for r in bind.execute(
            sa.text(
                "SELECT typname FROM pg_type WHERE typtype = 'e' "
                "AND typname LIKE 'document\\_reference\\_%' "
                "AND typname <> 'document_reference_status'"
            )
        )
    ]:
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # Documents are searched by subject: one index on the pair instead of the lone id.
    op.execute(f"DROP INDEX IF EXISTS ix_{P}_subject_id")
    # The public id's sequence is now its server default.
    op.execute(
        f"ALTER TABLE {P} ALTER COLUMN document_reference_id "
        "SET DEFAULT nextval('document_reference_pub_seq')"
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
        f"ALTER TABLE {P} DROP CONSTRAINT IF EXISTS document_reference_document_reference_id_key"
    )
    for column in ("tenant_id", "created_at", "updated_at"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)

    # status: the enum stays; the column is an index now.
    op.alter_column(
        P,
        "status",
        existing_type=postgresql.ENUM(
            *_STATUS, name="document_reference_status", create_type=False
        ),
        nullable=True,
    )
    op.add_column(P, sa.Column("description_norm", sa.String(), nullable=True))
    op.create_index(
        "ix_document_reference_context_period",
        P,
        ["context_period_start", "context_period_end"],
    )
    op.create_index(
        "ix_document_reference_subject_type_id", P, ["subject_type", "subject_id"]
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
        "ix_document_reference_token_param_code", f"{P}_token", ["param", "code"]
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
        "ix_document_reference_reference_param_type_id",
        f"{P}_reference",
        ["param", "reference_type", "reference_id"],
    )

    op.create_table(
        f"{P}_relates_to",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column(
            "code",
            postgresql.ENUM(
                *_RELATION, name="document_relationship_type", create_type=False
            ),
            nullable=True,
        ),
        sa.Column("target_reference", sa.String(), nullable=True),
        sa.Column("target_type", sa.String(), nullable=True),
        sa.Column("target_id", sa.BigInteger(), nullable=True),
        sa.Column("target_identifier_system", sa.String(), nullable=True),
        sa.Column("target_identifier_value", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(f"{P}_relates_to", f"{P}_pk")
    op.create_index(
        "ix_document_reference_relates_to_target",
        f"{P}_relates_to",
        ["target_type", "target_id"],
    )

    op.create_table(
        f"{P}_content",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column("content_type", sa.String(), nullable=True),
        sa.Column("language", sa.String(), nullable=True),
        sa.Column("url", sa.String(), nullable=True),
        sa.Column("format_system", sa.String(), nullable=True),
        sa.Column("format_code", sa.String(), nullable=True),
        sa.Column("format_display_norm", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(f"{P}_content", f"{P}_pk")
    _index(f"{P}_content", "content_type")

    _rebuild_index(bind)
    for column in ("id", "authenticator_id", "custodian_id", "status"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)
    op.create_index(
        f"ix_{P}_document_reference_id",
        P,
        ["document_reference_id"],
        unique=True,
        if_not_exists=True,
    )
    op.alter_column(P, "content", nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "document_reference content/index migration is one-way: its old normalized tables are "
        "not rebuilt from `content`. Restore from a backup taken before upgrading."
    )
