"""related_person: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: l9c4e1a7b503
Revises: k8b3d0f6a492
Create Date: 2026-11-28 10:00:00.000000

Medplum-style storage for RelatedPerson (see RelatedPersonModel's docstring),
same as the other resources already moved (Organization 5b1969c2ec19, Location
8c41d2e7a9b3, Practitioner a7d3f19c2b64, HealthcareService c9f5b2d7e813,
Endpoint d1a6c3e8f924, PractitionerRole e2b7d4f9a035, Schedule f3c8e5a1b947,
Slot g4d9f6b2c058, Patient h5e0a7c3d169, Appointment i6f1b8d4e27a,
AppointmentResponse j7a2c9e5f381, Encounter k8b3d0f6a492). The whole FHIR
resource moves into `related_person.content`; every column/table that survives
is a search index for one of the FHIR R4 RelatedPerson search parameters (or
`_id`/`_lastUpdated`), derived from `content`:

  related_person: active, gender, birth_date_start/_end (the date as the range it
      covers, replacing the old `birth_date` date), patient_reference/_type/_id/
      _identifier_system/_value (`patient_type` becomes a plain string); the
      public id gets its sequence as a server default; new: content
  related_person_identifier / _name / _telecom / _address: rebuilt as index tables
  related_person_relationship: rebuilt, one row per relationship coding
  dropped: the photo and communication tables and every main-table column with no
      search parameter (period, extension, patient display and logical-identifier
      details), the old identifier/name/telecom/address/relationship tables, and
      the `related_person_patient_reference_type` enum.

upgrade: (1) builds `content` for every existing row from the old columns and
tables - a frozen copy of the old to_fhir_related_person() logic (but keeping a
reference's raw string, so an absolute URL is not lost), so this migration never
depends on application code that has since changed; (2) drops the old child
tables/columns and creates the index tables; (3) rebuilds the index from
`content`.

downgrade: not supported. Everything the old schema held is preserved in
`content`, but rebuilding the old normalized tables from it is not implemented -
restore from a backup taken before upgrading.
"""
import base64
import json
import re
import unicodedata
from datetime import UTC, date, datetime, timedelta, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'l9c4e1a7b503'
down_revision: Union[str, None] = 'k8b3d0f6a492'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


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


def _b64(value):
    return base64.b64encode(bytes(value)).decode("ascii") if value is not None else None


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


_DATE_RE = re.compile(
    r"^(?P<y>\d{4})(?:-(?P<m>\d{2})(?:-(?P<d>\d{2})(?:T(?P<H>\d{2}):(?P<M>\d{2})"
    r"(?::(?P<S>\d{2})(?P<f>\.\d+)?)?(?P<tz>Z|[+-]\d{2}:\d{2})?)?)?)?$"
)


def _bounds(value):
    """(start, end) instants of a FHIR date/dateTime at its written
    precision — the half-open range it covers (frozen copy of
    app.fhir.search.values.parse_date / period_bounds). (None, None) if absent
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
        tz = timezone(sign * timedelta(hours=int(g["tz"][1:3]), minutes=int(g["tz"][4:6])))
    try:
        low = datetime(int(g["y"]), int(g["m"] or 1), int(g["d"] or 1), int(g["H"] or 0), int(g["M"] or 0),
                       int(g["S"] or 0), int(((g["f"] or ".0")[1:] + "000000")[:6]), tzinfo=tz)
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


def _human_name(n, prefix=""):
    return {
        "use": n[prefix + "use"], "text": n[prefix + "text"], "family": n[prefix + "family"],
        "given": n[prefix + "given"], "prefix": n[prefix + "prefix"], "suffix": n[prefix + "suffix"],
        "period": _period(n[prefix + "period_start"], n[prefix + "period_end"]),
    }


def _telecom(t):
    return {"system": t["system"], "value": t["value"], "use": t["use"], "rank": t["rank"],
            "period": _period(t["period_start"], t["period_end"])}


def _build_content(bind, r):
    pk = r["id"]
    identifiers = []
    for i in _rows(bind, "SELECT * FROM related_person_identifier WHERE related_person_pk = :pk ORDER BY id", pk=pk):
        codings = _rows(bind, "SELECT * FROM related_person_identifier_type_coding "
                              "WHERE related_person_identifier_id = :id ORDER BY id", id=i["id"])
        identifiers.append({
            "use": i["use"],
            "type": {"coding": [_coding(c) for c in codings], "text": i["type_text"]},
            "system": i["system"], "value": i["value"],
            "period": _period(i["period_start"], i["period_end"]),
            "assigner": _old_reference(i, "assigner"),
        })
    relationships = []
    for rel in _rows(bind, "SELECT * FROM related_person_relationship WHERE related_person_pk = :pk ORDER BY id", pk=pk):
        codings = _rows(bind, "SELECT * FROM related_person_relationship_coding "
                              "WHERE related_person_relationship_id = :id ORDER BY id", id=rel["id"])
        relationships.append({"coding": [_coding(c) for c in codings], "text": rel["text"]})
    names = [_human_name(n) for n in _rows(
        bind, "SELECT * FROM related_person_name WHERE related_person_pk = :pk ORDER BY id", pk=pk)]
    telecoms = [_telecom(t) for t in _rows(
        bind, "SELECT * FROM related_person_telecom WHERE related_person_pk = :pk ORDER BY id", pk=pk)]
    addresses = [{
        "use": a["use"], "type": a["type"], "text": a["text"], "line": a["line"],
        "city": a["city"], "district": a["district"], "state": a["state"],
        "postalCode": a["postal_code"], "country": a["country"],
        "period": _period(a["period_start"], a["period_end"]),
    } for a in _rows(bind, "SELECT * FROM related_person_address WHERE related_person_pk = :pk ORDER BY id", pk=pk)]
    photos = [{
        "contentType": ph["content_type"], "language": ph["language"], "data": _b64(ph["data"]),
        "url": ph["url"], "size": ph["size"], "hash": _b64(ph["hash"]), "title": ph["title"],
        "creation": _iso(ph["creation"]),
    } for ph in _rows(bind, "SELECT * FROM related_person_photo WHERE related_person_pk = :pk ORDER BY id", pk=pk)]
    communications = []
    for c in _rows(bind, "SELECT * FROM related_person_communication WHERE related_person_pk = :pk ORDER BY id", pk=pk):
        codings = _rows(bind, "SELECT * FROM related_person_communication_language_coding "
                              "WHERE related_person_communication_id = :id ORDER BY id", id=c["id"])
        communications.append({
            "language": {"coding": [_coding(x) for x in codings], "text": c["language_text"]},
            "preferred": c["preferred"],
        })
    return _prune({
        "extension": list(_json(r["extension"]) or []),
        "identifier": identifiers,
        "active": r["active"],
        "patient": _old_reference(r, "patient"),
        "relationship": relationships,
        "name": names,
        "telecom": telecoms,
        "gender": r["gender"],
        "birthDate": _iso(r["birth_date"]),
        "address": addresses,
        "photo": photos,
        "period": _period(r["period_start"], r["period_end"]),
        "communication": communications,
    })


def _backfill_content(bind):
    for r in _rows(bind, "SELECT * FROM related_person"):
        bind.execute(
            sa.text("UPDATE related_person SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, r)), "id": r["id"]},
        )


# ── upgrade: content -> search index (frozen copy of _indexer.py) ────────────

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")


def _rebuild_index(bind):
    for row in _rows(bind, "SELECT id, content FROM related_person"):
        pk, doc = row["id"], _json(row["content"])

        birth_start, birth_end = _bounds(doc.get("birthDate"))
        patient = doc.get("patient") or {}
        reference = patient.get("reference")
        identifier = patient.get("identifier") or {}
        match = _REF.match(reference or "")
        ptype, pid = ("Patient", int(match["id"])) if match and match["type"] == "Patient" else (None, None)
        bind.execute(sa.text(
            "UPDATE related_person SET birth_date_start = :bs, birth_date_end = :be, patient_reference = :pr, "
            "patient_type = :pt, patient_id = :pid, patient_identifier_system = :psys, "
            "patient_identifier_value = :pval WHERE id = :pk"),
            {"bs": birth_start, "be": birth_end, "pr": reference, "pt": ptype, "pid": pid,
             "psys": identifier.get("system"), "pval": identifier.get("value"), "pk": pk})

        for i in doc.get("identifier") or []:
            if not (i.get("system") or i.get("value")):
                continue
            itype = i.get("type") or {}
            for c in itype.get("coding") or [{}]:
                bind.execute(sa.text(
                    "INSERT INTO related_person_identifier (related_person_pk, system, value, type_system, "
                    "type_code, type_text_norm, type_display_norm) VALUES (:pk, :s, :v, :ts, :tc, :tt, :td)"),
                    {"pk": pk, "s": i.get("system"), "v": i.get("value"), "ts": c.get("system"),
                     "tc": c.get("code"), "tt": _norm(itype.get("text")), "td": _norm(c.get("display"))})
        for n in doc.get("name") or []:
            given, prefix, suffix = _strings(n.get("given")), _strings(n.get("prefix")), _strings(n.get("suffix"))
            phonetic = _phonetic_key(" ".join([n.get("family") or "", *(given or [])]).strip())
            bind.execute(sa.text(
                "INSERT INTO related_person_name (related_person_pk, text, text_norm, family, family_norm, given, "
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
                "INSERT INTO related_person_telecom (related_person_pk, system, value, use) "
                "VALUES (:pk, :s, :v, :u)"),
                {"pk": pk, "s": t.get("system"), "v": t["value"], "u": t.get("use")})
        for a in doc.get("address") or []:
            lines = _strings(a.get("line"))
            bind.execute(sa.text(
                "INSERT INTO related_person_address (related_person_pk, use, text, text_norm, line, line_norm, "
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
        for concept in doc.get("relationship") or []:
            text = _norm(concept.get("text"))
            codings = [c for c in concept.get("coding") or [] if c.get("system") or c.get("code") or c.get("display")]
            for c in codings or ([{}] if text else []):
                bind.execute(sa.text(
                    "INSERT INTO related_person_relationship (related_person_pk, system, code, display_norm, "
                    "text_norm) VALUES (:pk, :s, :c, :d, :t)"),
                    {"pk": pk, "s": c.get("system"), "c": c.get("code"), "d": _norm(c.get("display")), "t": text})


# Children first (grandchildren before their parents).
_OLD_CHILD_TABLES = (
    "related_person_communication_language_coding", "related_person_communication",
    "related_person_relationship_coding", "related_person_relationship",
    "related_person_identifier_type_coding", "related_person_identifier",
    "related_person_photo", "related_person_telecom", "related_person_address", "related_person_name",
)

_IDENTIFIER_PARTS = ("use", "type_system", "type_version", "type_code", "type_display", "type_text",
                     "type_user_selected", "period_start", "period_end")

_OLD_MAIN_COLUMNS = (
    "extension", "birth_date", "period_start", "period_end", "patient_display",
    *(f"patient_identifier_{p}" for p in _IDENTIFIER_PARTS),
)


def _fk():
    return sa.Column("related_person_pk", sa.BigInteger(), sa.ForeignKey("related_person.id"), nullable=False)


def _index(table, *columns):
    op.create_index(op.f("ix_" + table + "_" + columns[0]), table, list(columns))


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column('related_person', sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    _backfill_content(bind)

    # Every old child row is now represented in `content`; the index rows are
    # rebuilt from it below.
    for table in _OLD_CHILD_TABLES:
        op.drop_table(table)
    for column in _OLD_MAIN_COLUMNS:
        op.drop_column('related_person', column)

    # patient_type was an enum; it is a plain string now.
    op.alter_column('related_person', 'patient_type', type_=sa.String(), nullable=True,
                    postgresql_using='patient_type::text')
    op.execute("DROP TYPE IF EXISTS related_person_patient_reference_type")
    # The public id's sequence is now its server default.
    op.execute("ALTER TABLE related_person ALTER COLUMN related_person_id "
               "SET DEFAULT nextval('related_person_pub_seq')")

    op.add_column('related_person', sa.Column('birth_date_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('related_person', sa.Column('birth_date_end', sa.DateTime(timezone=True), nullable=True))
    op.create_index('ix_related_person_birth_date', 'related_person', ['birth_date_start', 'birth_date_end'])

    address_use = postgresql.ENUM(name='address_use', create_type=False)

    op.create_table(
        'related_person_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_text_norm', sa.String(), nullable=True),
        sa.Column('type_display_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    _index('related_person_identifier', 'related_person_pk')
    _index('related_person_identifier', 'value')

    op.create_table(
        'related_person_name',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
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
    _index('related_person_name', 'related_person_pk')
    _index('related_person_name', 'family_norm')

    op.create_table(
        'related_person_telecom',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('use', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    _index('related_person_telecom', 'related_person_pk')
    _index('related_person_telecom', 'value')

    op.create_table(
        'related_person_address',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
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
    _index('related_person_address', 'related_person_pk')

    op.create_table(
        'related_person_relationship',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display_norm', sa.String(), nullable=True),
        sa.Column('text_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    _index('related_person_relationship', 'related_person_pk')
    _index('related_person_relationship', 'code')

    _rebuild_index(bind)
    op.alter_column('related_person', 'content', nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "related_person content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
