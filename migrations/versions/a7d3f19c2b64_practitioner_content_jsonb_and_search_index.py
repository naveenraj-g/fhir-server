"""practitioner: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: a7d3f19c2b64
Revises: 8c41d2e7a9b3
Create Date: 2026-11-18 12:00:00.000000

Medplum-style storage for Practitioner (see PractitionerModel's docstring),
same as Organization (5b1969c2ec19) and Location (8c41d2e7a9b3). The whole
FHIR resource moves into `practitioner.content`; every column/table that
survives is a search index for one of the FHIR R4 Practitioner search
parameters (or `_id`/`_lastUpdated`), derived from `content`:

  practitioner: active, gender, user_id (kept); new: content
  practitioner_identifier: system, value; one row per Identifier.type.coding
      with type_system, type_code, type_text_norm, type_display_norm
  practitioner_name: one row per HumanName: text, family, given[], prefix[],
      suffix[] + a normalized `*_norm` twin of each + phonetic
  practitioner_telecom: system, value, use
  practitioner_address: use, text, line[], city, district, state,
      postal_code, country + a normalized `*_norm` twin of each
  practitioner_communication: one row per communication.coding: system, code,
      display_norm, text_norm
  dropped: practitioner.extension and practitioner.birth_date (both live in
      `content` now), practitioner_photo, practitioner_qualification (+
      _code_coding, _identifier, _identifier_type_coding),
      practitioner_identifier_type_coding, practitioner_communication_coding,
      and every non-searched column and per-row audit column on the index
      tables

`user_id` is not a FHIR element: it moves into `content` as the
https://fhir-server.dev/fhir/StructureDefinition/user-id extension
(valueString), and the column is kept as its index (it scopes `/me`).

upgrade: (1) builds `content` for every existing row from the old columns and
tables — a frozen copy of the old to_fhir_practitioner() logic, so this
migration never depends on application code that has since changed;
(2) drops the old child tables and creates the index tables; (3) rebuilds
every index row from `content`.

downgrade: not supported. Everything the old schema held is preserved in
`content`, but rebuilding the ten old normalized tables from it is not
implemented — restore from a backup taken before upgrading.
"""
import json
import re
import unicodedata
from datetime import date, datetime
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a7d3f19c2b64'
down_revision: Union[str, None] = '8c41d2e7a9b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

USER_ID_EXTENSION_URL = "https://fhir-server.dev/fhir/StructureDefinition/user-id"


# ── shared helpers (frozen — never import application code here) ────────────

def _prune(value):
    if isinstance(value, dict):
        out = {k: _prune(v) for k, v in value.items()}
        return {k: v for k, v in out.items() if v is not None and v != [] and v != {}}
    if isinstance(value, list):
        out = [_prune(v) for v in value]
        return [v for v in out if v is not None and v != [] and v != {}]
    return value


def _iso(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value


def _period(start, end):
    return {"start": _iso(start), "end": _iso(end)}


def _json(value):
    """A raw text() query can hand JSONB back as a string."""
    return json.loads(value) if isinstance(value, str) else value


def _rows(bind, sql, **params):
    return bind.execute(sa.text(sql), params).mappings().all()


_SOUNDEX = {**dict.fromkeys("BFPV", "1"), **dict.fromkeys("CGJKQSXZ", "2"),
            **dict.fromkeys("DT", "3"), "L": "4", **dict.fromkeys("MN", "5"), "R": "6"}


def _soundex(word):
    letters = re.sub(r"[^A-Z]", "", word.upper())
    if not letters:
        return None
    digits, prev = [], _SOUNDEX.get(letters[0], "")
    for ch in letters[1:]:
        code = _SOUNDEX.get(ch, "")
        if code and code != prev:
            digits.append(code)
        if ch not in "HW":
            prev = code
    return (letters[0] + "".join(digits) + "000")[:4]


def _phonetic_key(text):
    codes = []
    for word in re.split(r"\s+", text or ""):
        code = _soundex(word)
        if code and code not in codes:
            codes.append(code)
    return f" {' '.join(codes)} " if codes else None


def _norm(text):
    """Frozen copy of app.fhir.search.values.normalize."""
    if text is None:
        return None
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def _norms(values):
    return [_norm(v) for v in values] if values else None


def _strings(values):
    return [v for v in values or [] if v] or None


# ── upgrade: old columns/tables -> content (frozen copy of the old mapper) ───

def _coding(c):
    return {"system": c["system"], "version": c["version"], "code": c["code"],
            "display": c["display"], "userSelected": c["user_selected"]}


def _fallback_identifier(row, prefix):
    p = f"{prefix}_identifier_"
    return {
        "use": row[p + "use"],
        "type": {
            "coding": [{
                "system": row[p + "type_system"], "version": row[p + "type_version"],
                "code": row[p + "type_code"], "display": row[p + "type_display"],
                "userSelected": row[p + "type_user_selected"],
            }],
            "text": row[p + "type_text"],
        },
        "system": row[p + "system"],
        "value": row[p + "value"],
        "period": _period(row[p + "period_start"], row[p + "period_end"]),
    }


def _old_reference(row, prefix):
    raw = row[f"{prefix}_reference"]
    if not raw and row[f"{prefix}_type"] and row[f"{prefix}_id"]:
        raw = f"{row[prefix + '_type']}/{row[prefix + '_id']}"
    return {
        "reference": raw,
        "display": row[f"{prefix}_display"],
        "identifier": _fallback_identifier(row, prefix),
    }


def _identifier(bind, i, coding_table, fk):
    codings = _rows(bind, f"SELECT * FROM {coding_table} WHERE {fk} = :id ORDER BY id", id=i["id"])
    return {
        "use": i["use"],
        "type": {"coding": [_coding(c) for c in codings], "text": i["type_text"]},
        "system": i["system"], "value": i["value"],
        "period": _period(i["period_start"], i["period_end"]),
        "assigner": _old_reference(i, "assigner"),
    }


def _build_content(bind, p):
    pk = p["id"]
    identifiers = [
        _identifier(bind, i, "practitioner_identifier_type_coding", "practitioner_identifier_id")
        for i in _rows(bind, "SELECT * FROM practitioner_identifier WHERE practitioner_pk = :pk ORDER BY id", pk=pk)
    ]
    names = [{
        "use": n["use"], "text": n["text"], "family": n["family"], "given": n["given"],
        "prefix": n["prefix"], "suffix": n["suffix"], "period": _period(n["period_start"], n["period_end"]),
    } for n in _rows(bind, "SELECT * FROM practitioner_name WHERE practitioner_pk = :pk ORDER BY id", pk=pk)]
    telecoms = [{
        "system": t["system"], "value": t["value"], "use": t["use"], "rank": t["rank"],
        "period": _period(t["period_start"], t["period_end"]),
    } for t in _rows(bind, "SELECT * FROM practitioner_telecom WHERE practitioner_pk = :pk ORDER BY id", pk=pk)]
    addresses = [{
        "use": a["use"], "type": a["type"], "text": a["text"], "line": a["line"],
        "city": a["city"], "district": a["district"], "state": a["state"],
        "postalCode": a["postal_code"], "country": a["country"],
        "period": _period(a["period_start"], a["period_end"]),
    } for a in _rows(bind, "SELECT * FROM practitioner_address WHERE practitioner_pk = :pk ORDER BY id", pk=pk)]
    photos = [{
        "contentType": ph["content_type"], "language": ph["language"], "data": ph["data"],
        "url": ph["url"], "size": ph["size"], "hash": ph["hash"], "title": ph["title"],
        "creation": _iso(ph["creation"]),
    } for ph in _rows(bind, "SELECT * FROM practitioner_photo WHERE practitioner_pk = :pk ORDER BY id", pk=pk)]
    qualifications = []
    for q in _rows(bind, "SELECT * FROM practitioner_qualification WHERE practitioner_pk = :pk ORDER BY id", pk=pk):
        code_codings = _rows(bind, "SELECT * FROM practitioner_qualification_code_coding "
                                   "WHERE practitioner_qualification_id = :id ORDER BY id", id=q["id"])
        q_identifiers = [
            _identifier(bind, i, "practitioner_qualification_identifier_type_coding",
                        "practitioner_qualification_identifier_id")
            for i in _rows(bind, "SELECT * FROM practitioner_qualification_identifier "
                                 "WHERE practitioner_qualification_id = :id ORDER BY id", id=q["id"])
        ]
        qualifications.append({
            "identifier": q_identifiers,
            "code": {"coding": [_coding(c) for c in code_codings], "text": q["code_text"]},
            "period": _period(q["period_start"], q["period_end"]),
            "issuer": _old_reference(q, "issuer"),
        })
    communications = []
    for c in _rows(bind, "SELECT * FROM practitioner_communication WHERE practitioner_pk = :pk ORDER BY id", pk=pk):
        codings = _rows(bind, "SELECT * FROM practitioner_communication_coding "
                              "WHERE practitioner_communication_id = :id ORDER BY id", id=c["id"])
        communications.append({"coding": [_coding(x) for x in codings], "text": c["text"]})

    extensions = list(_json(p["extension"]) or [])
    if p["user_id"]:
        extensions.append({"url": USER_ID_EXTENSION_URL, "valueString": p["user_id"]})
    return _prune({
        "extension": extensions,
        "identifier": identifiers,
        "active": p["active"],
        "name": names,
        "telecom": telecoms,
        "address": addresses,
        "gender": p["gender"],
        "birthDate": _iso(p["birth_date"]),
        "photo": photos,
        "qualification": qualifications,
        "communication": communications,
    })


def _backfill_content(bind):
    for p in _rows(bind, "SELECT * FROM practitioner"):
        bind.execute(
            sa.text("UPDATE practitioner SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, p)), "id": p["id"]},
        )


# ── upgrade: content -> search index (frozen copy of _indexer.py) ────────────

def _rebuild_index(bind):
    for row in _rows(bind, "SELECT id, content FROM practitioner"):
        pk, doc = row["id"], _json(row["content"])
        for i in doc.get("identifier") or []:
            if not (i.get("system") or i.get("value")):
                continue
            itype = i.get("type") or {}
            for c in itype.get("coding") or [{}]:
                bind.execute(sa.text(
                    "INSERT INTO practitioner_identifier (practitioner_pk, system, value, type_system, type_code, "
                    "type_text_norm, type_display_norm) VALUES (:pk, :s, :v, :ts, :tc, :tt, :td)"),
                    {"pk": pk, "s": i.get("system"), "v": i.get("value"), "ts": c.get("system"),
                     "tc": c.get("code"), "tt": _norm(itype.get("text")), "td": _norm(c.get("display"))})
        for n in doc.get("name") or []:
            given, prefix, suffix = _strings(n.get("given")), _strings(n.get("prefix")), _strings(n.get("suffix"))
            phonetic = _phonetic_key(" ".join([n.get("family") or "", *(given or [])]).strip())
            bind.execute(sa.text(
                "INSERT INTO practitioner_name (practitioner_pk, text, text_norm, family, family_norm, given, "
                "given_norm, prefix, prefix_norm, suffix, suffix_norm, phonetic) VALUES (:pk, :text, :text_n, "
                ":family, :family_n, :given, :given_n, :prefix, :prefix_n, :suffix, :suffix_n, :phonetic)"),
                {"pk": pk, "text": n.get("text"), "text_n": _norm(n.get("text")),
                 "family": n.get("family"), "family_n": _norm(n.get("family")),
                 "given": given, "given_n": _norms(given), "prefix": prefix, "prefix_n": _norms(prefix),
                 "suffix": suffix, "suffix_n": _norms(suffix), "phonetic": phonetic})
        for t in doc.get("telecom") or []:
            if not t.get("value"):
                continue
            bind.execute(sa.text(
                "INSERT INTO practitioner_telecom (practitioner_pk, system, value, use) VALUES (:pk, :s, :v, :u)"),
                {"pk": pk, "s": t.get("system"), "v": t["value"], "u": t.get("use")})
        for a in doc.get("address") or []:
            lines = _strings(a.get("line"))
            bind.execute(sa.text(
                "INSERT INTO practitioner_address (practitioner_pk, use, text, text_norm, line, line_norm, "
                "city, city_norm, district, district_norm, state, state_norm, postal_code, postal_code_norm, "
                "country, country_norm) VALUES (:pk, CAST(:use AS address_use), :text, :text_n, :line, :line_n, "
                ":city, :city_n, :district, :district_n, :state, :state_n, :pc, :pc_n, :country, :country_n)"),
                {"pk": pk, "use": a.get("use"), "text": a.get("text"), "text_n": _norm(a.get("text")),
                 "line": lines, "line_n": _norms(lines),
                 "city": a.get("city"), "city_n": _norm(a.get("city")),
                 "district": a.get("district"), "district_n": _norm(a.get("district")),
                 "state": a.get("state"), "state_n": _norm(a.get("state")),
                 "pc": a.get("postalCode"), "pc_n": _norm(a.get("postalCode")),
                 "country": a.get("country"), "country_n": _norm(a.get("country"))})
        for cc in doc.get("communication") or []:
            text = _norm(cc.get("text"))
            codings = [c for c in cc.get("coding") or [] if c.get("system") or c.get("code") or c.get("display")]
            for c in codings or ([{}] if text else []):
                bind.execute(sa.text(
                    "INSERT INTO practitioner_communication (practitioner_pk, system, code, display_norm, text_norm) "
                    "VALUES (:pk, :s, :c, :d, :t)"),
                    {"pk": pk, "s": c.get("system"), "c": c.get("code"), "d": _norm(c.get("display")), "t": text})


# Children first.
_OLD_CHILD_TABLES = (
    "practitioner_qualification_identifier_type_coding",
    "practitioner_qualification_identifier",
    "practitioner_qualification_code_coding",
    "practitioner_qualification",
    "practitioner_identifier_type_coding",
    "practitioner_identifier",
    "practitioner_communication_coding",
    "practitioner_communication",
    "practitioner_photo",
    "practitioner_telecom",
    "practitioner_address",
    "practitioner_name",
)


def _pk_fk(table):
    return sa.Column("practitioner_pk", sa.BigInteger(), sa.ForeignKey("practitioner.id"), nullable=False)


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column('practitioner', sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    _backfill_content(bind)

    # Every old child row is now represented in `content`; the index rows are
    # rebuilt from it below.
    for table in _OLD_CHILD_TABLES:
        op.drop_table(table)
    op.drop_column('practitioner', 'extension')
    op.drop_column('practitioner', 'birth_date')

    address_use = postgresql.ENUM(name='address_use', create_type=False)

    op.create_table(
        'practitioner_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _pk_fk('practitioner_identifier'),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_text_norm', sa.String(), nullable=True),
        sa.Column('type_display_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_practitioner_identifier_practitioner_pk'), 'practitioner_identifier', ['practitioner_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_identifier_value'), 'practitioner_identifier', ['value'], unique=False)

    op.create_table(
        'practitioner_name',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _pk_fk('practitioner_name'),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('text_norm', sa.String(), nullable=True),
        sa.Column('family', sa.String(), nullable=True),
        sa.Column('family_norm', sa.String(), nullable=True),
        sa.Column('given', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('given_norm', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('prefix', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('prefix_norm', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('suffix', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('suffix_norm', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('phonetic', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_practitioner_name_practitioner_pk'), 'practitioner_name', ['practitioner_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_name_family_norm'), 'practitioner_name', ['family_norm'], unique=False)

    op.create_table(
        'practitioner_telecom',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _pk_fk('practitioner_telecom'),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('use', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_practitioner_telecom_practitioner_pk'), 'practitioner_telecom', ['practitioner_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_telecom_value'), 'practitioner_telecom', ['value'], unique=False)

    op.create_table(
        'practitioner_address',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _pk_fk('practitioner_address'),
        sa.Column('use', address_use, nullable=True),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('text_norm', sa.String(), nullable=True),
        sa.Column('line', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('line_norm', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('city', sa.String(), nullable=True),
        sa.Column('city_norm', sa.String(), nullable=True),
        sa.Column('district', sa.String(), nullable=True),
        sa.Column('district_norm', sa.String(), nullable=True),
        sa.Column('state', sa.String(), nullable=True),
        sa.Column('state_norm', sa.String(), nullable=True),
        sa.Column('postal_code', sa.String(), nullable=True),
        sa.Column('postal_code_norm', sa.String(), nullable=True),
        sa.Column('country', sa.String(), nullable=True),
        sa.Column('country_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_practitioner_address_practitioner_pk'), 'practitioner_address', ['practitioner_pk'], unique=False)

    op.create_table(
        'practitioner_communication',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _pk_fk('practitioner_communication'),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display_norm', sa.String(), nullable=True),
        sa.Column('text_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_practitioner_communication_practitioner_pk'), 'practitioner_communication', ['practitioner_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_communication_code'), 'practitioner_communication', ['code'], unique=False)

    _rebuild_index(bind)
    op.alter_column('practitioner', 'content', nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "practitioner content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
