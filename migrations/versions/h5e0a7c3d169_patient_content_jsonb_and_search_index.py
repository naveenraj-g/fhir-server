"""patient: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: h5e0a7c3d169
Revises: g4d9f6b2c058
Create Date: 2026-11-24 10:00:00.000000

Medplum-style storage for Patient (see PatientModel's docstring), same as the
other resources already moved (Organization 5b1969c2ec19, Location
8c41d2e7a9b3, Practitioner a7d3f19c2b64, HealthcareService c9f5b2d7e813,
Endpoint d1a6c3e8f924, PractitionerRole e2b7d4f9a035, Schedule f3c8e5a1b947,
Slot g4d9f6b2c058). The whole FHIR resource moves into `patient.content`;
every column/table that survives is a search index for one of the FHIR R4
Patient search parameters (or `_id`/`_lastUpdated`), derived from `content`:

  patient: active, gender, user_id (kept), managing_organization_reference/
      _type/_id/_identifier_system/_value (kept; feed `organization`); new:
      content, birth_date_start/_end, death_date_start/_end, deceased
  patient_identifier: one row per identifier x type.coding
  patient_name: one row per HumanName, raw + `*_norm` + phonetic
  patient_telecom: system, value, use
  patient_address: use, text, line[], city, district, state, postal_code,
      country + a normalized `*_norm` twin of each
  patient_communication: one row per communication.language.coding
  patient_reference (new): one row per generalPractitioner and per link.other,
      told apart by `param`
  dropped: patient.extension, birth_date, deceased_boolean, deceased_date_time,
      marital_status_text, multiple_birth_boolean/_integer and the
      managingOrganization display / identifier-detail columns (all live in
      `content` now); patient_photo, patient_marital_status_coding,
      patient_contact (+ _relationship, _relationship_coding, _telecom),
      patient_communication_language_coding, patient_general_practitioner,
      patient_link, patient_identifier_type_coding; and every per-row audit
      column on the index tables

`user_id` is not a FHIR element: it stays a column (the link to the end-user,
which scopes `/me`) and is never put into `content`.

upgrade: (1) builds `content` for every existing row from the old columns and
tables — a frozen copy of the old to_fhir_patient() logic (but keeping a
reference's raw string, so an absolute URL is not lost), so this migration
never depends on application code that has since changed; (2) drops the old
child tables and recreates the index tables; (3) rebuilds the index from
`content`.

downgrade: not supported. Everything the old schema held is preserved in
`content`, but rebuilding the fifteen old normalized tables from it is not
implemented — restore from a backup taken before upgrading.
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
revision: str = 'h5e0a7c3d169'
down_revision: Union[str, None] = 'g4d9f6b2c058'
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


def _build_content(bind, p):
    pk = p["id"]
    identifiers = []
    for i in _rows(bind, "SELECT * FROM patient_identifier WHERE patient_pk = :pk ORDER BY id", pk=pk):
        codings = _rows(bind, "SELECT * FROM patient_identifier_type_coding "
                              "WHERE patient_identifier_id = :id ORDER BY id", id=i["id"])
        identifiers.append({
            "use": i["use"],
            "type": {"coding": [_coding(c) for c in codings], "text": i["type_text"]},
            "system": i["system"], "value": i["value"],
            "period": _period(i["period_start"], i["period_end"]),
            "assigner": _old_reference(i, "assigner"),
        })
    names = [_human_name(n) for n in _rows(bind, "SELECT * FROM patient_name WHERE patient_pk = :pk ORDER BY id", pk=pk)]
    telecoms = [_telecom(t) for t in _rows(bind, "SELECT * FROM patient_telecom WHERE patient_pk = :pk ORDER BY id", pk=pk)]
    addresses = [{
        "use": a["use"], "type": a["type"], "text": a["text"], "line": a["line"],
        "city": a["city"], "district": a["district"], "state": a["state"],
        "postalCode": a["postal_code"], "country": a["country"],
        "period": _period(a["period_start"], a["period_end"]),
    } for a in _rows(bind, "SELECT * FROM patient_address WHERE patient_pk = :pk ORDER BY id", pk=pk)]
    photos = [{
        "contentType": ph["content_type"], "language": ph["language"], "data": _b64(ph["data"]),
        "url": ph["url"], "size": ph["size"], "hash": _b64(ph["hash"]), "title": ph["title"],
        "creation": _iso(ph["creation"]),
    } for ph in _rows(bind, "SELECT * FROM patient_photo WHERE patient_pk = :pk ORDER BY id", pk=pk)]

    marital_codings = _rows(bind, "SELECT * FROM patient_marital_status_coding WHERE patient_pk = :pk ORDER BY id", pk=pk)
    marital_status = {"coding": [_coding(c) for c in marital_codings], "text": p["marital_status_text"]}

    contacts = []
    for c in _rows(bind, "SELECT * FROM patient_contact WHERE patient_pk = :pk ORDER BY id", pk=pk):
        relationships = []
        for r in _rows(bind, "SELECT * FROM patient_contact_relationship WHERE contact_id = :id ORDER BY id", id=c["id"]):
            codings = _rows(bind, "SELECT * FROM patient_contact_relationship_coding "
                                  "WHERE relationship_id = :id ORDER BY id", id=r["id"])
            relationships.append({"coding": [_coding(x) for x in codings], "text": r["text"]})
        contacts.append({
            "relationship": relationships,
            "name": _human_name(c, "name_"),
            "telecom": [_telecom(t) for t in _rows(
                bind, "SELECT * FROM patient_contact_telecom WHERE contact_id = :id ORDER BY id", id=c["id"])],
            "address": {
                "use": c["address_use"], "type": c["address_type"], "text": c["address_text"],
                "line": c["address_line"], "city": c["address_city"], "district": c["address_district"],
                "state": c["address_state"], "postalCode": c["address_postal_code"],
                "country": c["address_country"],
            },
            "gender": c["gender"],
            "organization": _old_reference(c, "organization"),
            "period": _period(c["period_start"], c["period_end"]),
        })

    communications = []
    for c in _rows(bind, "SELECT * FROM patient_communication WHERE patient_pk = :pk ORDER BY id", pk=pk):
        codings = _rows(bind, "SELECT * FROM patient_communication_language_coding "
                              "WHERE patient_communication_id = :id ORDER BY id", id=c["id"])
        communications.append({
            "language": {"coding": [_coding(x) for x in codings], "text": c["language_text"]},
            "preferred": c["preferred"],
        })

    general_practitioners = [
        _old_reference(g, "reference")
        for g in _rows(bind, "SELECT * FROM patient_general_practitioner WHERE patient_pk = :pk ORDER BY id", pk=pk)
    ]
    links = [{
        "other": _old_reference(l, "other"),
        "type": l["type"].replace("_", "-") if l["type"] else None,
    } for l in _rows(bind, "SELECT * FROM patient_link WHERE patient_pk = :pk ORDER BY id", pk=pk)]

    return _prune({
        "extension": list(_json(p["extension"]) or []),
        "identifier": identifiers,
        "active": p["active"],
        "name": names,
        "telecom": telecoms,
        "gender": p["gender"],
        "birthDate": _iso(p["birth_date"]),
        "deceasedBoolean": p["deceased_boolean"],
        "deceasedDateTime": _iso(p["deceased_date_time"]),
        "address": addresses,
        "maritalStatus": marital_status,
        "multipleBirthBoolean": p["multiple_birth_boolean"],
        "multipleBirthInteger": p["multiple_birth_integer"],
        "photo": photos,
        "contact": contacts,
        "communication": communications,
        "generalPractitioner": general_practitioners,
        "managingOrganization": _old_reference(p, "managing_organization"),
        "link": links,
    })


def _backfill_content(bind):
    for p in _rows(bind, "SELECT * FROM patient"):
        bind.execute(
            sa.text("UPDATE patient SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, p)), "id": p["id"]},
        )


# ── upgrade: content -> search index (frozen copy of _indexer.py) ────────────

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")
_REFERENCE_TYPES = {
    "general-practitioner": ("Organization", "Practitioner", "PractitionerRole"),
    "link": ("Patient", "RelatedPerson"),
}


def _reference_row(bind, pk, param, ref):
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return
    match = _REF.match(reference or "")
    ref_type, ref_id = (None, None)
    if match and match["type"] in _REFERENCE_TYPES[param]:
        ref_type, ref_id = match["type"], int(match["id"])
    bind.execute(sa.text(
        "INSERT INTO patient_reference (patient_pk, param, reference_reference, reference_type, reference_id, "
        "reference_identifier_system, reference_identifier_value) VALUES (:pk, :p, :r, :t, :i, :s, :v)"),
        {"pk": pk, "p": param, "r": reference, "t": ref_type, "i": ref_id,
         "s": identifier.get("system"), "v": identifier.get("value")})


def _rebuild_index(bind):
    for row in _rows(bind, "SELECT id, content FROM patient"):
        pk, doc = row["id"], _json(row["content"])

        # Columns on the patient row itself.
        birth = doc.get("birthDate")
        death = doc.get("deceasedDateTime")
        birth_start, birth_end = _bounds(birth)
        death_start, death_end = _bounds(death)
        flag = doc.get("deceasedBoolean")
        deceased = True if death else (flag if isinstance(flag, bool) else None)
        org = doc.get("managingOrganization") or {}
        org_ref = org.get("reference")
        org_identifier = org.get("identifier") or {}
        match = _REF.match(org_ref or "")
        org_type, org_id = ("Organization", int(match["id"])) if match and match["type"] == "Organization" else (None, None)
        bind.execute(sa.text(
            "UPDATE patient SET birth_date_start = :bs, birth_date_end = :be, death_date_start = :ds, "
            "death_date_end = :de, deceased = :dec, managing_organization_reference = :orf, "
            "managing_organization_type = CAST(:ot AS organization_reference_type), managing_organization_id = :oid, "
            "managing_organization_identifier_system = :osys, managing_organization_identifier_value = :oval "
            "WHERE id = :pk"),
            {"bs": birth_start, "be": birth_end, "ds": death_start, "de": death_end, "dec": deceased,
             "orf": org_ref, "ot": org_type, "oid": org_id, "osys": org_identifier.get("system"),
             "oval": org_identifier.get("value"), "pk": pk})

        for i in doc.get("identifier") or []:
            if not (i.get("system") or i.get("value")):
                continue
            itype = i.get("type") or {}
            for c in itype.get("coding") or [{}]:
                bind.execute(sa.text(
                    "INSERT INTO patient_identifier (patient_pk, system, value, type_system, type_code, "
                    "type_text_norm, type_display_norm) VALUES (:pk, :s, :v, :ts, :tc, :tt, :td)"),
                    {"pk": pk, "s": i.get("system"), "v": i.get("value"), "ts": c.get("system"),
                     "tc": c.get("code"), "tt": _norm(itype.get("text")), "td": _norm(c.get("display"))})
        for n in doc.get("name") or []:
            given, prefix, suffix = _strings(n.get("given")), _strings(n.get("prefix")), _strings(n.get("suffix"))
            phonetic = _phonetic_key(" ".join([n.get("family") or "", *(given or [])]).strip())
            bind.execute(sa.text(
                "INSERT INTO patient_name (patient_pk, text, text_norm, family, family_norm, given, "
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
                "INSERT INTO patient_telecom (patient_pk, system, value, use) VALUES (:pk, :s, :v, :u)"),
                {"pk": pk, "s": t.get("system"), "v": t["value"], "u": t.get("use")})
        for a in doc.get("address") or []:
            lines = _strings(a.get("line"))
            bind.execute(sa.text(
                "INSERT INTO patient_address (patient_pk, use, text, text_norm, line, line_norm, "
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
        for comm in doc.get("communication") or []:
            language = comm.get("language")
            if not language:
                continue
            text = _norm(language.get("text"))
            codings = [c for c in language.get("coding") or [] if c.get("system") or c.get("code") or c.get("display")]
            for c in codings or ([{}] if text else []):
                bind.execute(sa.text(
                    "INSERT INTO patient_communication (patient_pk, system, code, display_norm, text_norm) "
                    "VALUES (:pk, :s, :c, :d, :t)"),
                    {"pk": pk, "s": c.get("system"), "c": c.get("code"), "d": _norm(c.get("display")), "t": text})
        for gp in doc.get("generalPractitioner") or []:
            _reference_row(bind, pk, "general-practitioner", gp)
        for link in doc.get("link") or []:
            _reference_row(bind, pk, "link", link.get("other"))


# Children first.
_OLD_CHILD_TABLES = (
    "patient_contact_telecom",
    "patient_contact_relationship_coding",
    "patient_contact_relationship",
    "patient_contact",
    "patient_communication_language_coding",
    "patient_communication",
    "patient_identifier_type_coding",
    "patient_identifier",
    "patient_general_practitioner",
    "patient_link",
    "patient_marital_status_coding",
    "patient_photo",
    "patient_telecom",
    "patient_address",
    "patient_name",
)

_OLD_MAIN_COLUMNS = (
    "extension",
    "birth_date",
    "deceased_boolean",
    "deceased_date_time",
    "marital_status_text",
    "multiple_birth_boolean",
    "multiple_birth_integer",
    "managing_organization_display",
    "managing_organization_identifier_use",
    "managing_organization_identifier_type_system",
    "managing_organization_identifier_type_version",
    "managing_organization_identifier_type_code",
    "managing_organization_identifier_type_display",
    "managing_organization_identifier_type_user_selected",
    "managing_organization_identifier_type_text",
    "managing_organization_identifier_period_start",
    "managing_organization_identifier_period_end",
)

_OLD_ENUMS = ("patient_link_type", "patient_link_other_type", "patient_general_practitioner_reference_type")


def _fk():
    return sa.Column("patient_pk", sa.BigInteger(), sa.ForeignKey("patient.id"), nullable=False)


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column('patient', sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    _backfill_content(bind)

    # Every old child row is now represented in `content`; the index rows are
    # rebuilt from it below.
    for table in _OLD_CHILD_TABLES:
        op.drop_table(table)
    for column in _OLD_MAIN_COLUMNS:
        op.drop_column('patient', column)
    for enum in _OLD_ENUMS:
        op.execute(f"DROP TYPE IF EXISTS {enum}")

    op.add_column('patient', sa.Column('birth_date_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('patient', sa.Column('birth_date_end', sa.DateTime(timezone=True), nullable=True))
    op.add_column('patient', sa.Column('death_date_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('patient', sa.Column('death_date_end', sa.DateTime(timezone=True), nullable=True))
    op.add_column('patient', sa.Column('deceased', sa.Boolean(), nullable=True))
    op.create_index('ix_patient_birth_date', 'patient', ['birth_date_start', 'birth_date_end'], unique=False)
    op.create_index('ix_patient_death_date', 'patient', ['death_date_start', 'death_date_end'], unique=False)

    address_use = postgresql.ENUM(name='address_use', create_type=False)

    op.create_table(
        'patient_identifier',
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
    op.create_index(op.f('ix_patient_identifier_patient_pk'), 'patient_identifier', ['patient_pk'], unique=False)
    op.create_index(op.f('ix_patient_identifier_value'), 'patient_identifier', ['value'], unique=False)

    op.create_table(
        'patient_name',
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
    op.create_index(op.f('ix_patient_name_patient_pk'), 'patient_name', ['patient_pk'], unique=False)
    op.create_index(op.f('ix_patient_name_family_norm'), 'patient_name', ['family_norm'], unique=False)

    op.create_table(
        'patient_telecom',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('use', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_patient_telecom_patient_pk'), 'patient_telecom', ['patient_pk'], unique=False)
    op.create_index(op.f('ix_patient_telecom_value'), 'patient_telecom', ['value'], unique=False)

    op.create_table(
        'patient_address',
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
    op.create_index(op.f('ix_patient_address_patient_pk'), 'patient_address', ['patient_pk'], unique=False)

    op.create_table(
        'patient_communication',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display_norm', sa.String(), nullable=True),
        sa.Column('text_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_patient_communication_patient_pk'), 'patient_communication', ['patient_pk'], unique=False)
    op.create_index(op.f('ix_patient_communication_code'), 'patient_communication', ['code'], unique=False)

    op.create_table(
        'patient_reference',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column('param', sa.String(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_identifier_system', sa.String(), nullable=True),
        sa.Column('reference_identifier_value', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_patient_reference_patient_pk'), 'patient_reference', ['patient_pk'], unique=False)
    op.create_index('ix_patient_reference_param_type_id', 'patient_reference',
                    ['param', 'reference_type', 'reference_id'], unique=False)

    _rebuild_index(bind)
    op.alter_column('patient', 'content', nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "patient content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
