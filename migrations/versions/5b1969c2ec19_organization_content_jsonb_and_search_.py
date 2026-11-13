"""organization: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: 5b1969c2ec19
Revises: 633f7e50edb8
Create Date: 2026-11-10 20:34:30.637497

Medplum-style storage for Organization (see OrganizationModel's docstring).
The whole FHIR resource moves into `organization.content`; every other
column/table that survives is a search index for one of the FHIR R4
Organization search parameters (or `_id`/`_lastUpdated`), derived from
`content`:

  organization: active, name, alias[] (kept); partof_reference/_type/_id,
      partof_identifier_system/_value (kept, now feed `partof` and
      `partof:identifier`); new: content, name_norm, alias_norm[],
      name_phonetic
  organization_identifier: system, value (kept); new: one row per
      Identifier.type.coding with type_system, type_code, type_text_norm,
      type_display_norm (for `:of-type` / `:text`)
  organization_type: one row per type.coding: system, code, display_norm,
      text_norm (replacing the CodeableConcept row + organization_type_coding)
  organization_address: use, text, line[], city, district, state,
      postal_code, country (kept) + a normalized `*_norm` twin of each
  organization_endpoint: reference_reference/_type/_id,
      reference_identifier_system/_value (kept)
  dropped: organization_telecom, organization_contact(+_telecom,
      +_purpose_coding), organization_identifier_type_coding,
      organization_type_coding, and every non-searched column (extension,
      partOf display / identifier use-type-period, identifier
      use/type/period/assigner, address type/period, endpoint display /
      identifier use-type-period, and the per-row audit columns on index
      tables)

`*_norm` columns hold the value with accents stripped and case folded —
FHIR string search is case- and accent-insensitive by default; the raw
column answers `:exact`.

upgrade: (1) builds `content` for every existing row from the old columns
and tables — a frozen copy of the old to_fhir_organization() logic, so this
migration never depends on application code that has since changed;
(2) reshapes the schema; (3) rebuilds every index row from `content`.

downgrade: restores the old schema and repopulates it from `content`.
Lossless for everything the old schema could hold.

Hand-assembled from `alembic revision --autogenerate`, restricted to the
organization tables: autogenerate also reported unrelated model/DB drift on
other resources (specimen, terminology, ...), deliberately left out here.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

import json
import re
import unicodedata
from datetime import datetime

# revision identifiers, used by Alembic.
revision: str = '5b1969c2ec19'
down_revision: Union[str, None] = '633f7e50edb8'
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


def _iso(dt):
    return dt.isoformat() if isinstance(dt, datetime) else dt


def _dt(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def _period(start, end):
    return {"start": _iso(start), "end": _iso(end)}


def _json(value):
    """A raw text() query over asyncpg can hand JSONB back as a string."""
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


# ── upgrade: old columns/tables -> content ───────────────────────────────────

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


def _old_reference(row, prefix, raw_col):
    raw = row[raw_col]
    if not raw and row[f"{prefix}_type"] and row[f"{prefix}_id"]:
        raw = f"{row[prefix + '_type']}/{row[prefix + '_id']}"
    return {
        "reference": raw,
        "display": row[f"{prefix}_display"],
        "identifier": _fallback_identifier(row, prefix),
    }


def _coding(c):
    return {"system": c["system"], "version": c["version"], "code": c["code"],
            "display": c["display"], "userSelected": c["user_selected"]}


def _contact_point(t):
    return {"system": t["system"], "value": t["value"], "use": t["use"],
            "rank": t["rank"], "period": _period(t["period_start"], t["period_end"])}


def _build_content(bind, org):
    pk = org["id"]
    identifiers = []
    for i in _rows(bind, "SELECT * FROM organization_identifier WHERE organization_pk = :pk ORDER BY id", pk=pk):
        codings = _rows(bind, "SELECT * FROM organization_identifier_type_coding WHERE organization_identifier_id = :id ORDER BY id", id=i["id"])
        identifiers.append({
            "use": i["use"],
            "type": {"coding": [_coding(c) for c in codings], "text": i["type_text"]},
            "system": i["system"], "value": i["value"],
            "period": _period(i["period_start"], i["period_end"]),
            "assigner": _old_reference(i, "assigner", "assigner_reference"),
        })
    types = []
    for t in _rows(bind, "SELECT * FROM organization_type WHERE organization_pk = :pk ORDER BY id", pk=pk):
        codings = _rows(bind, "SELECT * FROM organization_type_coding WHERE organization_type_id = :id ORDER BY id", id=t["id"])
        types.append({"coding": [_coding(c) for c in codings], "text": t["text"]})
    telecoms = [_contact_point(t) for t in _rows(bind, "SELECT * FROM organization_telecom WHERE organization_pk = :pk ORDER BY id", pk=pk)]
    addresses = [{
        "use": a["use"], "type": a["type"], "text": a["text"], "line": a["line"],
        "city": a["city"], "district": a["district"], "state": a["state"],
        "postalCode": a["postal_code"], "country": a["country"],
        "period": _period(a["period_start"], a["period_end"]),
    } for a in _rows(bind, "SELECT * FROM organization_address WHERE organization_pk = :pk ORDER BY id", pk=pk)]
    contacts = []
    for c in _rows(bind, "SELECT * FROM organization_contact WHERE organization_pk = :pk ORDER BY id", pk=pk):
        purpose = _rows(bind, "SELECT * FROM organization_contact_purpose_coding WHERE contact_id = :id ORDER BY id", id=c["id"])
        ctel = _rows(bind, "SELECT * FROM organization_contact_telecom WHERE contact_id = :id ORDER BY id", id=c["id"])
        contacts.append({
            "purpose": {"coding": [_coding(x) for x in purpose], "text": c["purpose_text"]},
            "name": {"use": c["name_use"], "text": c["name_text"], "family": c["name_family"],
                     "given": c["name_given"], "prefix": c["name_prefix"], "suffix": c["name_suffix"],
                     "period": _period(c["name_period_start"], c["name_period_end"])},
            "telecom": [_contact_point(t) for t in ctel],
            "address": {"use": c["address_use"], "type": c["address_type"], "text": c["address_text"],
                        "line": c["address_line"], "city": c["address_city"],
                        "district": c["address_district"], "state": c["address_state"],
                        "postalCode": c["address_postal_code"], "country": c["address_country"],
                        "period": _period(c["address_period_start"], c["address_period_end"])},
        })
    endpoints = [_old_reference(e, "reference", "reference_reference")
                 for e in _rows(bind, "SELECT * FROM organization_endpoint WHERE organization_pk = :pk ORDER BY id", pk=pk)]
    return _prune({
        "extension": _json(org["extension"]),
        "identifier": identifiers,
        "active": org["active"],
        "type": types,
        "name": org["name"],
        "alias": org["alias"],
        "telecom": telecoms,
        "address": addresses,
        "partOf": _old_reference(org, "partof", "partof_reference"),
        "contact": contacts,
        "endpoint": endpoints,
    })


def _backfill_content(bind):
    for org in _rows(bind, "SELECT * FROM organization"):
        bind.execute(
            sa.text("UPDATE organization SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, org)), "id": org["id"]},
        )


# ── upgrade: content -> search index (frozen copy of _indexer.py) ────────────

def _relative(ref, resource_type):
    return ref if ref and ref.startswith(f"{resource_type}/") else None


def _rebuild_index(bind):
    for org in _rows(bind, "SELECT id, content FROM organization"):
        pk, doc = org["id"], _json(org["content"])
        partof = doc.get("partOf") or {}
        local = _relative(partof.get("reference"), "Organization")
        pident = partof.get("identifier") or {}
        aliases = [a for a in doc.get("alias") or [] if a] or None
        bind.execute(sa.text(
            "UPDATE organization SET name_norm = :nn, alias = :al, alias_norm = :aln, name_phonetic = :p, "
            "partof_reference = :pr, partof_type = CAST(:t AS organization_reference_type), partof_id = :i, "
            "partof_identifier_system = :pis, partof_identifier_value = :piv WHERE id = :pk"),
            {"nn": _norm(doc.get("name")), "al": aliases, "aln": _norms(aliases),
             "p": _phonetic_key(doc.get("name")), "pr": partof.get("reference"),
             "t": "Organization" if local else None,
             "i": int(local.split("/", 1)[1]) if local else None,
             "pis": pident.get("system"), "piv": pident.get("value"), "pk": pk})
        for i in doc.get("identifier") or []:
            if not (i.get("system") or i.get("value")):
                continue
            itype = i.get("type") or {}
            for c in itype.get("coding") or [{}]:
                bind.execute(sa.text(
                    "INSERT INTO organization_identifier (organization_pk, system, value, type_system, type_code, "
                    "type_text_norm, type_display_norm) VALUES (:pk, :s, :v, :ts, :tc, :tt, :td)"),
                    {"pk": pk, "s": i.get("system"), "v": i.get("value"), "ts": c.get("system"),
                     "tc": c.get("code"), "tt": _norm(itype.get("text")), "td": _norm(c.get("display"))})
        for cc in doc.get("type") or []:
            text = _norm(cc.get("text"))
            codings = [c for c in cc.get("coding") or [] if c.get("system") or c.get("code") or c.get("display")]
            for c in codings or ([{}] if text else []):
                bind.execute(sa.text(
                    "INSERT INTO organization_type (organization_pk, system, code, display_norm, text_norm) "
                    "VALUES (:pk, :s, :c, :d, :t)"),
                    {"pk": pk, "s": c.get("system"), "c": c.get("code"), "d": _norm(c.get("display")), "t": text})
        for a in doc.get("address") or []:
            lines = [x for x in a.get("line") or [] if x] or None
            bind.execute(sa.text(
                "INSERT INTO organization_address (organization_pk, use, text, text_norm, line, line_norm, "
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
        for e in doc.get("endpoint") or []:
            ident = e.get("identifier") or {}
            if not (e.get("reference") or ident.get("value")):
                continue
            local = _relative(e.get("reference"), "Endpoint")
            bind.execute(sa.text(
                "INSERT INTO organization_endpoint (organization_pk, reference_reference, reference_type, "
                "reference_id, reference_identifier_system, reference_identifier_value) "
                "VALUES (:pk, :r, CAST(:t AS organization_endpoint_ref_type), :i, :is_, :iv)"),
                {"pk": pk, "r": e.get("reference"), "t": "Endpoint" if local else None,
                 "i": int(local.split("/", 1)[1]) if local else None,
                 "is_": ident.get("system"), "iv": ident.get("value")})


_OLD_CHILD_TABLES_IN_DELETE_ORDER = (
    "organization_contact_telecom", "organization_contact_purpose_coding", "organization_contact",
    "organization_telecom", "organization_identifier_type_coding", "organization_identifier",
    "organization_type_coding", "organization_type", "organization_address", "organization_endpoint",
)


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column('organization', sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    _backfill_content(bind)

    # Every old child row is now represented in `content`; index rows are
    # rebuilt from it below, so clear them all before reshaping.
    for table in _OLD_CHILD_TABLES_IN_DELETE_ORDER:
        op.execute(f"DELETE FROM {table}")
    for table in ("organization_contact_telecom", "organization_contact_purpose_coding",
                  "organization_contact", "organization_telecom",
                  "organization_identifier_type_coding", "organization_type_coding"):
        op.drop_table(table)

    # ── reshape (organization tables only) ──
    # organization
    op.add_column('organization', sa.Column('name_norm', sa.String(), nullable=True))
    op.add_column('organization', sa.Column('name_phonetic', sa.String(), nullable=True))
    op.add_column('organization', sa.Column('alias_norm', postgresql.ARRAY(sa.String()), nullable=True))
    op.create_index('ix_organization_name_norm', 'organization', ['name_norm'], unique=False, postgresql_ops={'name_norm': 'text_pattern_ops'})
    op.drop_column('organization', 'extension')
    op.drop_column('organization', 'partof_display')
    op.drop_column('organization', 'partof_identifier_use')
    op.drop_column('organization', 'partof_identifier_type_system')
    op.drop_column('organization', 'partof_identifier_type_version')
    op.drop_column('organization', 'partof_identifier_type_code')
    op.drop_column('organization', 'partof_identifier_type_display')
    op.drop_column('organization', 'partof_identifier_type_user_selected')
    op.drop_column('organization', 'partof_identifier_type_text')
    op.drop_column('organization', 'partof_identifier_period_start')
    op.drop_column('organization', 'partof_identifier_period_end')
    # organization_identifier
    op.drop_index(op.f('ix_organization_identifier_assigner_id'), table_name='organization_identifier')
    op.drop_index(op.f('ix_organization_identifier_created_at'), table_name='organization_identifier')
    op.drop_index(op.f('ix_organization_identifier_tenant_id'), table_name='organization_identifier')
    op.drop_index(op.f('ix_organization_identifier_updated_at'), table_name='organization_identifier')
    op.drop_column('organization_identifier', 'created_at')
    op.drop_column('organization_identifier', 'created_by')
    op.drop_column('organization_identifier', 'tenant_id')
    op.drop_column('organization_identifier', 'updated_at')
    op.drop_column('organization_identifier', 'updated_by')
    op.drop_column('organization_identifier', 'use')
    op.drop_column('organization_identifier', 'type_text')
    op.drop_column('organization_identifier', 'period_start')
    op.drop_column('organization_identifier', 'period_end')
    op.drop_column('organization_identifier', 'assigner_reference')
    op.drop_column('organization_identifier', 'assigner_type')
    op.drop_column('organization_identifier', 'assigner_id')
    op.drop_column('organization_identifier', 'assigner_display')
    op.drop_column('organization_identifier', 'assigner_identifier_use')
    op.drop_column('organization_identifier', 'assigner_identifier_type_system')
    op.drop_column('organization_identifier', 'assigner_identifier_type_version')
    op.drop_column('organization_identifier', 'assigner_identifier_type_code')
    op.drop_column('organization_identifier', 'assigner_identifier_type_display')
    op.drop_column('organization_identifier', 'assigner_identifier_type_user_selected')
    op.drop_column('organization_identifier', 'assigner_identifier_type_text')
    op.drop_column('organization_identifier', 'assigner_identifier_period_start')
    op.drop_column('organization_identifier', 'assigner_identifier_period_end')
    op.drop_column('organization_identifier', 'assigner_identifier_system')
    op.drop_column('organization_identifier', 'assigner_identifier_value')
    op.add_column('organization_identifier', sa.Column('type_system', sa.String(), nullable=True))
    op.add_column('organization_identifier', sa.Column('type_code', sa.String(), nullable=True))
    op.add_column('organization_identifier', sa.Column('type_text_norm', sa.String(), nullable=True))
    op.add_column('organization_identifier', sa.Column('type_display_norm', sa.String(), nullable=True))
    op.create_index(op.f('ix_organization_identifier_value'), 'organization_identifier', ['value'], unique=False)
    # organization_type
    op.drop_index(op.f('ix_organization_type_created_at'), table_name='organization_type')
    op.drop_index(op.f('ix_organization_type_tenant_id'), table_name='organization_type')
    op.drop_index(op.f('ix_organization_type_updated_at'), table_name='organization_type')
    op.drop_column('organization_type', 'created_at')
    op.drop_column('organization_type', 'created_by')
    op.drop_column('organization_type', 'tenant_id')
    op.drop_column('organization_type', 'updated_at')
    op.drop_column('organization_type', 'updated_by')
    op.drop_column('organization_type', 'text')
    op.add_column('organization_type', sa.Column('system', sa.String(), nullable=True))
    op.add_column('organization_type', sa.Column('code', sa.String(), nullable=True))
    op.add_column('organization_type', sa.Column('display_norm', sa.String(), nullable=True))
    op.add_column('organization_type', sa.Column('text_norm', sa.String(), nullable=True))
    op.create_index(op.f('ix_organization_type_code'), 'organization_type', ['code'], unique=False)
    # organization_address
    op.drop_index(op.f('ix_organization_address_created_at'), table_name='organization_address')
    op.drop_index(op.f('ix_organization_address_tenant_id'), table_name='organization_address')
    op.drop_index(op.f('ix_organization_address_updated_at'), table_name='organization_address')
    op.drop_column('organization_address', 'created_at')
    op.drop_column('organization_address', 'created_by')
    op.drop_column('organization_address', 'tenant_id')
    op.drop_column('organization_address', 'updated_at')
    op.drop_column('organization_address', 'updated_by')
    op.drop_column('organization_address', 'type')
    op.drop_column('organization_address', 'period_start')
    op.drop_column('organization_address', 'period_end')
    op.add_column('organization_address', sa.Column('text_norm', sa.String(), nullable=True))
    op.add_column('organization_address', sa.Column('city_norm', sa.String(), nullable=True))
    op.add_column('organization_address', sa.Column('district_norm', sa.String(), nullable=True))
    op.add_column('organization_address', sa.Column('state_norm', sa.String(), nullable=True))
    op.add_column('organization_address', sa.Column('postal_code_norm', sa.String(), nullable=True))
    op.add_column('organization_address', sa.Column('country_norm', sa.String(), nullable=True))
    op.add_column('organization_address', sa.Column('line_norm', postgresql.ARRAY(sa.String()), nullable=True))
    # organization_endpoint
    op.drop_index(op.f('ix_organization_endpoint_created_at'), table_name='organization_endpoint')
    op.drop_index(op.f('ix_organization_endpoint_tenant_id'), table_name='organization_endpoint')
    op.drop_index(op.f('ix_organization_endpoint_updated_at'), table_name='organization_endpoint')
    op.drop_column('organization_endpoint', 'created_at')
    op.drop_column('organization_endpoint', 'created_by')
    op.drop_column('organization_endpoint', 'tenant_id')
    op.drop_column('organization_endpoint', 'updated_at')
    op.drop_column('organization_endpoint', 'updated_by')
    op.drop_column('organization_endpoint', 'reference_display')
    op.drop_column('organization_endpoint', 'reference_identifier_use')
    op.drop_column('organization_endpoint', 'reference_identifier_type_system')
    op.drop_column('organization_endpoint', 'reference_identifier_type_version')
    op.drop_column('organization_endpoint', 'reference_identifier_type_code')
    op.drop_column('organization_endpoint', 'reference_identifier_type_display')
    op.drop_column('organization_endpoint', 'reference_identifier_type_user_selected')
    op.drop_column('organization_endpoint', 'reference_identifier_type_text')
    op.drop_column('organization_endpoint', 'reference_identifier_period_start')
    op.drop_column('organization_endpoint', 'reference_identifier_period_end')

    _rebuild_index(bind)
    op.alter_column('organization', 'content', nullable=False)


# ── downgrade: content -> old columns/tables ─────────────────────────────────

def _fallback_columns(prefix, ident):
    i = ident or {}
    t = i.get("type") or {}
    c = (t.get("coding") or [{}])[0]
    p = i.get("period") or {}
    q = f"{prefix}_identifier_"
    return {q + "use": i.get("use"), q + "type_system": c.get("system"),
            q + "type_version": c.get("version"), q + "type_code": c.get("code"),
            q + "type_display": c.get("display"), q + "type_user_selected": c.get("userSelected"),
            q + "type_text": t.get("text"), q + "system": i.get("system"), q + "value": i.get("value"),
            q + "period_start": _dt(p.get("start")), q + "period_end": _dt(p.get("end"))}


def _ref_columns(prefix, raw_col, ref, resource_type):
    r = ref or {}
    local = _relative(r.get("reference"), resource_type)
    return {raw_col: r.get("reference"),
            f"{prefix}_type": resource_type if local else None,
            f"{prefix}_id": int(local.split("/", 1)[1]) if local else None,
            f"{prefix}_display": r.get("display"),
            **_fallback_columns(prefix, r.get("identifier"))}


_CASTS = {"use": "identifier_use", "partof_identifier_use": "identifier_use",
          "assigner_identifier_use": "identifier_use", "reference_identifier_use": "identifier_use",
          "partof_type": "organization_reference_type", "assigner_type": "organization_reference_type",
          "reference_type": "organization_endpoint_ref_type"}


def _insert(bind, table, values, casts=None, returning=False):
    casts = {**_CASTS, **(casts or {})}
    cols = list(values)
    params = ", ".join(f"CAST(:{c} AS {casts[c]})" if c in casts else f":{c}" for c in cols)
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({params})" + (" RETURNING id" if returning else "")
    result = bind.execute(sa.text(sql), {k: (json.dumps(v) if isinstance(v, (dict,)) else v) for k, v in values.items()})
    return result.scalar() if returning else None


def _restore_old(bind):
    for org in _rows(bind, "SELECT * FROM organization"):
        pk, doc = org["id"], _json(org["content"]) or {}
        audit = {"tenant_id": org["tenant_id"], "created_by": org["created_by"]}
        main = {"alias": doc.get("alias"), "extension": json.dumps(doc.get("extension") or []),
                **_ref_columns("partof", "partof_reference", doc.get("partOf"), "Organization")}
        sets = ", ".join(
            f"{k} = CAST(:{k} AS {_CASTS[k]})" if k in _CASTS else (f"{k} = CAST(:{k} AS jsonb)" if k == "extension" else f"{k} = :{k}")
            for k in main)
        bind.execute(sa.text(f"UPDATE organization SET {sets} WHERE id = :pk"), {**main, "pk": pk})

        for i in doc.get("identifier") or []:
            t = i.get("type") or {}
            p = i.get("period") or {}
            iid = _insert(bind, "organization_identifier", {
                "organization_pk": pk, "use": i.get("use"), "type_text": t.get("text"),
                "system": i.get("system"), "value": i.get("value"),
                "period_start": _dt(p.get("start")), "period_end": _dt(p.get("end")),
                **_ref_columns("assigner", "assigner_reference", i.get("assigner"), "Organization"),
                **audit}, returning=True)
            for c in t.get("coding") or []:
                _insert(bind, "organization_identifier_type_coding", {
                    "organization_identifier_id": iid, "system": c.get("system"), "version": c.get("version"),
                    "code": c.get("code"), "display": c.get("display"), "user_selected": c.get("userSelected"), **audit})
        for cc in doc.get("type") or []:
            tid = _insert(bind, "organization_type", {"organization_pk": pk, "text": cc.get("text"), **audit}, returning=True)
            for c in cc.get("coding") or []:
                _insert(bind, "organization_type_coding", {
                    "organization_type_id": tid, "system": c.get("system"), "version": c.get("version"),
                    "code": c.get("code"), "display": c.get("display"), "user_selected": c.get("userSelected"), **audit})
        cp_casts = {"system": "contact_point_system", "use": "contact_point_use"}
        for t in doc.get("telecom") or []:
            p = t.get("period") or {}
            _insert(bind, "organization_telecom", {
                "organization_pk": pk, "system": t.get("system"), "value": t.get("value"), "use": t.get("use"),
                "rank": t.get("rank"), "period_start": _dt(p.get("start")), "period_end": _dt(p.get("end")), **audit},
                casts=cp_casts)
        for a in doc.get("address") or []:
            p = a.get("period") or {}
            _insert(bind, "organization_address", {
                "organization_pk": pk, "use": a.get("use"), "type": a.get("type"), "text": a.get("text"),
                "line": a.get("line"), "city": a.get("city"), "district": a.get("district"),
                "state": a.get("state"), "postal_code": a.get("postalCode"), "country": a.get("country"),
                "period_start": _dt(p.get("start")), "period_end": _dt(p.get("end")), **audit},
                casts={"use": "address_use", "type": "address_type"})
        for c in doc.get("contact") or []:
            n, a, pu = c.get("name") or {}, c.get("address") or {}, c.get("purpose") or {}
            np_, ap = n.get("period") or {}, a.get("period") or {}
            cid = _insert(bind, "organization_contact", {
                "organization_pk": pk, "purpose_text": pu.get("text"),
                "name_use": n.get("use"), "name_text": n.get("text"), "name_family": n.get("family"),
                "name_given": n.get("given"), "name_prefix": n.get("prefix"), "name_suffix": n.get("suffix"),
                "name_period_start": _dt(np_.get("start")), "name_period_end": _dt(np_.get("end")),
                "address_use": a.get("use"), "address_type": a.get("type"), "address_text": a.get("text"),
                "address_line": a.get("line"), "address_city": a.get("city"), "address_district": a.get("district"),
                "address_state": a.get("state"), "address_postal_code": a.get("postalCode"),
                "address_country": a.get("country"),
                "address_period_start": _dt(ap.get("start")), "address_period_end": _dt(ap.get("end")), **audit},
                casts={"name_use": "human_name_use", "address_use": "address_use", "address_type": "address_type"},
                returning=True)
            for x in pu.get("coding") or []:
                _insert(bind, "organization_contact_purpose_coding", {
                    "contact_id": cid, "system": x.get("system"), "version": x.get("version"), "code": x.get("code"),
                    "display": x.get("display"), "user_selected": x.get("userSelected"), **audit})
            for t in c.get("telecom") or []:
                p = t.get("period") or {}
                _insert(bind, "organization_contact_telecom", {
                    "contact_id": cid, "system": t.get("system"), "value": t.get("value"), "use": t.get("use"),
                    "rank": t.get("rank"), "period_start": _dt(p.get("start")), "period_end": _dt(p.get("end")), **audit},
                    casts=cp_casts)
        for e in doc.get("endpoint") or []:
            _insert(bind, "organization_endpoint", {
                "organization_pk": pk, **_ref_columns("reference", "reference_reference", e, "Endpoint"), **audit})


def downgrade() -> None:
    bind = op.get_bind()
    # Index rows are rebuilt (in the old shape) from `content` below.
    for table in ("organization_identifier", "organization_type",
                  "organization_address", "organization_endpoint"):
        op.execute(f"DELETE FROM {table}")
    # ── reverse reshape ──
    # organization_endpoint
    op.add_column('organization_endpoint', sa.Column('tenant_id', sa.VARCHAR(), nullable=False))
    op.add_column('organization_endpoint', sa.Column('created_by', sa.VARCHAR(), nullable=False))
    op.add_column('organization_endpoint', sa.Column('updated_by', sa.VARCHAR(), nullable=True))
    op.add_column('organization_endpoint', sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.add_column('organization_endpoint', sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.create_index(op.f('ix_organization_endpoint_created_at'), 'organization_endpoint', ['created_at'], unique=False)
    op.create_index(op.f('ix_organization_endpoint_tenant_id'), 'organization_endpoint', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_organization_endpoint_updated_at'), 'organization_endpoint', ['updated_at'], unique=False)
    op.add_column('organization_endpoint', sa.Column('reference_display', sa.VARCHAR(), nullable=True))
    op.add_column('organization_endpoint', sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('organization_endpoint', sa.Column('reference_identifier_type_system', sa.VARCHAR(), nullable=True))
    op.add_column('organization_endpoint', sa.Column('reference_identifier_type_version', sa.VARCHAR(), nullable=True))
    op.add_column('organization_endpoint', sa.Column('reference_identifier_type_code', sa.VARCHAR(), nullable=True))
    op.add_column('organization_endpoint', sa.Column('reference_identifier_type_display', sa.VARCHAR(), nullable=True))
    op.add_column('organization_endpoint', sa.Column('reference_identifier_type_text', sa.VARCHAR(), nullable=True))
    op.add_column('organization_endpoint', sa.Column('reference_identifier_type_user_selected', sa.BOOLEAN(), nullable=True))
    op.add_column('organization_endpoint', sa.Column('reference_identifier_period_start', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('organization_endpoint', sa.Column('reference_identifier_period_end', postgresql.TIMESTAMP(timezone=True), nullable=True))
    # organization_address
    op.drop_column('organization_address', 'text_norm')
    op.drop_column('organization_address', 'line_norm')
    op.drop_column('organization_address', 'city_norm')
    op.drop_column('organization_address', 'district_norm')
    op.drop_column('organization_address', 'state_norm')
    op.drop_column('organization_address', 'postal_code_norm')
    op.drop_column('organization_address', 'country_norm')
    op.add_column('organization_address', sa.Column('tenant_id', sa.VARCHAR(), nullable=False))
    op.add_column('organization_address', sa.Column('created_by', sa.VARCHAR(), nullable=False))
    op.add_column('organization_address', sa.Column('updated_by', sa.VARCHAR(), nullable=True))
    op.add_column('organization_address', sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.add_column('organization_address', sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.create_index(op.f('ix_organization_address_created_at'), 'organization_address', ['created_at'], unique=False)
    op.create_index(op.f('ix_organization_address_tenant_id'), 'organization_address', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_organization_address_updated_at'), 'organization_address', ['updated_at'], unique=False)
    op.add_column('organization_address', sa.Column('type', postgresql.ENUM('postal', 'physical', 'both', name='address_type', create_type=False), nullable=True))
    op.add_column('organization_address', sa.Column('period_start', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('organization_address', sa.Column('period_end', postgresql.TIMESTAMP(timezone=True), nullable=True))
    # organization_type (system/code dropped after _restore_old)
    op.drop_column('organization_type', 'display_norm')
    op.drop_column('organization_type', 'text_norm')
    op.add_column('organization_type', sa.Column('tenant_id', sa.VARCHAR(), nullable=False))
    op.add_column('organization_type', sa.Column('created_by', sa.VARCHAR(), nullable=False))
    op.add_column('organization_type', sa.Column('updated_by', sa.VARCHAR(), nullable=True))
    op.add_column('organization_type', sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.add_column('organization_type', sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.create_index(op.f('ix_organization_type_created_at'), 'organization_type', ['created_at'], unique=False)
    op.create_index(op.f('ix_organization_type_tenant_id'), 'organization_type', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_organization_type_updated_at'), 'organization_type', ['updated_at'], unique=False)
    op.add_column('organization_type', sa.Column('text', sa.VARCHAR(), nullable=True))
    # organization_identifier
    op.drop_index(op.f('ix_organization_identifier_value'), table_name='organization_identifier')
    op.drop_column('organization_identifier', 'type_system')
    op.drop_column('organization_identifier', 'type_code')
    op.drop_column('organization_identifier', 'type_text_norm')
    op.drop_column('organization_identifier', 'type_display_norm')
    op.add_column('organization_identifier', sa.Column('tenant_id', sa.VARCHAR(), nullable=False))
    op.add_column('organization_identifier', sa.Column('created_by', sa.VARCHAR(), nullable=False))
    op.add_column('organization_identifier', sa.Column('updated_by', sa.VARCHAR(), nullable=True))
    op.add_column('organization_identifier', sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True))
    op.add_column('organization_identifier', sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.create_index(op.f('ix_organization_identifier_created_at'), 'organization_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_organization_identifier_tenant_id'), 'organization_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_organization_identifier_updated_at'), 'organization_identifier', ['updated_at'], unique=False)
    op.add_column('organization_identifier', sa.Column('use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('organization_identifier', sa.Column('type_text', sa.VARCHAR(), nullable=True))
    op.add_column('organization_identifier', sa.Column('period_start', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('organization_identifier', sa.Column('period_end', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('organization_identifier', sa.Column('assigner_reference', sa.VARCHAR(), nullable=True))
    op.add_column('organization_identifier', sa.Column('assigner_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True))
    op.add_column('organization_identifier', sa.Column('assigner_id', sa.BIGINT(), nullable=True))
    op.add_column('organization_identifier', sa.Column('assigner_display', sa.VARCHAR(), nullable=True))
    op.add_column('organization_identifier', sa.Column('assigner_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('organization_identifier', sa.Column('assigner_identifier_type_system', sa.VARCHAR(), nullable=True))
    op.add_column('organization_identifier', sa.Column('assigner_identifier_type_version', sa.VARCHAR(), nullable=True))
    op.add_column('organization_identifier', sa.Column('assigner_identifier_type_code', sa.VARCHAR(), nullable=True))
    op.add_column('organization_identifier', sa.Column('assigner_identifier_type_display', sa.VARCHAR(), nullable=True))
    op.add_column('organization_identifier', sa.Column('assigner_identifier_type_text', sa.VARCHAR(), nullable=True))
    op.add_column('organization_identifier', sa.Column('assigner_identifier_type_user_selected', sa.BOOLEAN(), nullable=True))
    op.add_column('organization_identifier', sa.Column('assigner_identifier_period_start', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('organization_identifier', sa.Column('assigner_identifier_period_end', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('organization_identifier', sa.Column('assigner_identifier_system', sa.VARCHAR(), nullable=True))
    op.add_column('organization_identifier', sa.Column('assigner_identifier_value', sa.VARCHAR(), nullable=True))
    op.create_index(op.f('ix_organization_identifier_assigner_id'), 'organization_identifier', ['assigner_id'], unique=False)
    # organization (content/name_phonetic dropped after _restore_old)
    op.drop_index('ix_organization_name_norm', table_name='organization')
    op.drop_column('organization', 'name_norm')
    op.drop_column('organization', 'alias_norm')
    op.add_column('organization', sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False))
    op.add_column('organization', sa.Column('partof_display', sa.VARCHAR(), nullable=True))
    op.add_column('organization', sa.Column('partof_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('organization', sa.Column('partof_identifier_type_system', sa.VARCHAR(), nullable=True))
    op.add_column('organization', sa.Column('partof_identifier_type_version', sa.VARCHAR(), nullable=True))
    op.add_column('organization', sa.Column('partof_identifier_type_code', sa.VARCHAR(), nullable=True))
    op.add_column('organization', sa.Column('partof_identifier_type_display', sa.VARCHAR(), nullable=True))
    op.add_column('organization', sa.Column('partof_identifier_type_text', sa.VARCHAR(), nullable=True))
    op.add_column('organization', sa.Column('partof_identifier_type_user_selected', sa.BOOLEAN(), nullable=True))
    op.add_column('organization', sa.Column('partof_identifier_period_start', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('organization', sa.Column('partof_identifier_period_end', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.create_table('organization_contact',
    sa.Column('id', sa.BIGINT(), autoincrement=True, nullable=False),
    sa.Column('organization_pk', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('purpose_text', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('name_use', postgresql.ENUM('usual', 'official', 'temp', 'nickname', 'anonymous', 'old', 'maiden', name='human_name_use', create_type=False), autoincrement=False, nullable=True),
    sa.Column('name_text', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('name_family', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('name_given', postgresql.ARRAY(sa.VARCHAR()), autoincrement=False, nullable=True),
    sa.Column('name_prefix', postgresql.ARRAY(sa.VARCHAR()), autoincrement=False, nullable=True),
    sa.Column('name_suffix', postgresql.ARRAY(sa.VARCHAR()), autoincrement=False, nullable=True),
    sa.Column('name_period_start', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('name_period_end', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('address_use', postgresql.ENUM('home', 'work', 'temp', 'old', 'billing', name='address_use', create_type=False), autoincrement=False, nullable=True),
    sa.Column('address_type', postgresql.ENUM('postal', 'physical', 'both', name='address_type', create_type=False), autoincrement=False, nullable=True),
    sa.Column('address_text', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('address_line', postgresql.ARRAY(sa.VARCHAR()), autoincrement=False, nullable=True),
    sa.Column('address_city', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('address_district', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('address_state', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('address_postal_code', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('address_country', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('address_period_start', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('address_period_end', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('tenant_id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('created_by', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('updated_by', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['organization_pk'], ['organization.id'], name=op.f('organization_contact_organization_pk_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('organization_contact_pkey'))
    )
    op.create_index(op.f('ix_organization_contact_updated_at'), 'organization_contact', ['updated_at'], unique=False)
    op.create_index(op.f('ix_organization_contact_tenant_id'), 'organization_contact', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_organization_contact_organization_pk'), 'organization_contact', ['organization_pk'], unique=False)
    op.create_index(op.f('ix_organization_contact_created_at'), 'organization_contact', ['created_at'], unique=False)
    op.create_table('organization_contact_telecom',
    sa.Column('id', sa.BIGINT(), autoincrement=True, nullable=False),
    sa.Column('contact_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('system', postgresql.ENUM('phone', 'fax', 'email', 'pager', 'url', 'sms', 'other', name='contact_point_system', create_type=False), autoincrement=False, nullable=True),
    sa.Column('value', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('use', postgresql.ENUM('home', 'work', 'temp', 'old', 'mobile', name='contact_point_use', create_type=False), autoincrement=False, nullable=True),
    sa.Column('rank', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('period_start', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('period_end', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('tenant_id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('created_by', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('updated_by', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['contact_id'], ['organization_contact.id'], name=op.f('organization_contact_telecom_contact_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('organization_contact_telecom_pkey'))
    )
    op.create_index(op.f('ix_organization_contact_telecom_updated_at'), 'organization_contact_telecom', ['updated_at'], unique=False)
    op.create_index(op.f('ix_organization_contact_telecom_tenant_id'), 'organization_contact_telecom', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_organization_contact_telecom_created_at'), 'organization_contact_telecom', ['created_at'], unique=False)
    op.create_index(op.f('ix_organization_contact_telecom_contact_id'), 'organization_contact_telecom', ['contact_id'], unique=False)
    op.create_table('organization_contact_purpose_coding',
    sa.Column('id', sa.BIGINT(), autoincrement=True, nullable=False),
    sa.Column('contact_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('system', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('version', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('code', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('display', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('user_selected', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('tenant_id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('created_by', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('updated_by', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['contact_id'], ['organization_contact.id'], name=op.f('organization_contact_purpose_coding_contact_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('organization_contact_purpose_coding_pkey'))
    )
    op.create_index(op.f('ix_organization_contact_purpose_coding_updated_at'), 'organization_contact_purpose_coding', ['updated_at'], unique=False)
    op.create_index(op.f('ix_organization_contact_purpose_coding_tenant_id'), 'organization_contact_purpose_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_organization_contact_purpose_coding_created_at'), 'organization_contact_purpose_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_organization_contact_purpose_coding_contact_id'), 'organization_contact_purpose_coding', ['contact_id'], unique=False)
    op.create_table('organization_telecom',
    sa.Column('id', sa.BIGINT(), autoincrement=True, nullable=False),
    sa.Column('organization_pk', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('system', postgresql.ENUM('phone', 'fax', 'email', 'pager', 'url', 'sms', 'other', name='contact_point_system', create_type=False), autoincrement=False, nullable=True),
    sa.Column('value', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('use', postgresql.ENUM('home', 'work', 'temp', 'old', 'mobile', name='contact_point_use', create_type=False), autoincrement=False, nullable=True),
    sa.Column('rank', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('period_start', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('period_end', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.Column('tenant_id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('created_by', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('updated_by', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['organization_pk'], ['organization.id'], name=op.f('organization_telecom_organization_pk_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('organization_telecom_pkey'))
    )
    op.create_index(op.f('ix_organization_telecom_updated_at'), 'organization_telecom', ['updated_at'], unique=False)
    op.create_index(op.f('ix_organization_telecom_tenant_id'), 'organization_telecom', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_organization_telecom_organization_pk'), 'organization_telecom', ['organization_pk'], unique=False)
    op.create_index(op.f('ix_organization_telecom_created_at'), 'organization_telecom', ['created_at'], unique=False)
    op.create_table('organization_identifier_type_coding',
    sa.Column('id', sa.BIGINT(), autoincrement=True, nullable=False),
    sa.Column('organization_identifier_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('system', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('version', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('code', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('display', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('user_selected', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('tenant_id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('created_by', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('updated_by', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['organization_identifier_id'], ['organization_identifier.id'], name=op.f('organization_identifier_type_co_organization_identifier_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('organization_identifier_type_coding_pkey'))
    )
    op.create_index(op.f('ix_organization_identifier_type_coding_organization_ide_b574'), 'organization_identifier_type_coding', ['organization_identifier_id'], unique=False)

    op.create_index(op.f('ix_organization_identifier_type_coding_updated_at'), 'organization_identifier_type_coding', ['updated_at'], unique=False)
    op.create_index(op.f('ix_organization_identifier_type_coding_tenant_id'), 'organization_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_organization_identifier_type_coding_created_at'), 'organization_identifier_type_coding', ['created_at'], unique=False)
    op.create_table('organization_type_coding',
    sa.Column('id', sa.BIGINT(), autoincrement=True, nullable=False),
    sa.Column('organization_type_id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('system', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('version', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('code', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('display', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('user_selected', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('tenant_id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('created_by', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('updated_by', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['organization_type_id'], ['organization_type.id'], name=op.f('organization_type_coding_organization_type_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('organization_type_coding_pkey'))
    )
    op.create_index(op.f('ix_organization_type_coding_updated_at'), 'organization_type_coding', ['updated_at'], unique=False)
    op.create_index(op.f('ix_organization_type_coding_tenant_id'), 'organization_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_organization_type_coding_organization_type_id'), 'organization_type_coding', ['organization_type_id'], unique=False)
    op.create_index(op.f('ix_organization_type_coding_created_at'), 'organization_type_coding', ['created_at'], unique=False)

    _restore_old(bind)
    op.drop_index(op.f('ix_organization_type_code'), table_name='organization_type')
    op.drop_column('organization_type', 'code')
    op.drop_column('organization_type', 'system')
    op.drop_column('organization', 'name_phonetic')
    op.drop_column('organization', 'content')
