"""location: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: 8c41d2e7a9b3
Revises: 5b1969c2ec19
Create Date: 2026-11-11 10:00:00.000000

Medplum-style storage for Location — the same move Organization made in
5b1969c2ec19 (see LocationModel's docstring). The whole FHIR resource moves
into `location.content`; every column/table that survives is a search index
for a FHIR R4 Location search parameter (or `_id`/`_lastUpdated`), derived
from `content`:

  location: status, name, alias[], operational_status_system/_code,
      address_use/_text/_line[]/_city/_district/_state/_postal_code/_country,
      managing_organization_reference/_type/_id/_identifier_system/_value,
      part_of_reference/_type/_id/_identifier_system/_value,
      position_latitude/_longitude (kept); new: content, name_norm,
      alias_norm[], operational_status_display_norm, and a `*_norm` twin of
      each searched address part
  location_identifier: system, value (kept); new: one row per
      Identifier.type.coding with type_system, type_code, type_text_norm,
      type_display_norm
  location_type: one row per type.coding: system, code, display_norm,
      text_norm (replacing the CodeableConcept row + location_type_coding)
  location_endpoint: reference_reference/_type/_id,
      reference_identifier_system/_value (kept)
  dropped: location_telecom, location_hours_of_operation,
      location_physical_type_coding, location_identifier_type_coding,
      location_type_coding, and every non-searched column (extension,
      description, mode, physicalType text, availabilityExceptions,
      position altitude, operationalStatus version/display/userSelected,
      address type/period, reference display / identifier use-type-period,
      identifier use/type/period/assigner, and the per-row audit columns on
      index tables)

The Postgres enum types only the dropped columns used (location_mode,
location_day_of_week) are kept, so downgrade can use them again.

upgrade: (1) builds `content` for every existing row from the old columns
and tables — a frozen copy of the old to_fhir_location() logic, so this
migration never depends on application code that has since changed;
(2) reshapes the schema; (3) rebuilds every index row from `content`.

downgrade: restores the old schema and repopulates it from `content`.
Lossless for everything the old schema could hold.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

import json
import unicodedata
from datetime import datetime, time
from decimal import Decimal

# revision identifiers, used by Alembic.
revision: str = '8c41d2e7a9b3'
down_revision: Union[str, None] = '5b1969c2ec19'
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
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()
    return value


def _dt(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")) if value else None


def _period(start, end):
    return {"start": _iso(start), "end": _iso(end)}


def _num(value):
    """A NUMERIC column as a JSON number (int when it's whole)."""
    if value is None:
        return None
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    return value


def _json(value):
    """A raw text() query over asyncpg can hand JSONB back as a string."""
    return json.loads(value) if isinstance(value, str) else value


def _rows(bind, sql, **params):
    return bind.execute(sa.text(sql), params).mappings().all()


def _norm(text):
    """Frozen copy of app.fhir.search.values.normalize."""
    if text is None:
        return None
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def _norms(values):
    return [_norm(v) for v in values] if values else None


def _relative(ref, resource_type):
    return ref if ref and ref.startswith(f"{resource_type}/") else None


# ── upgrade: old columns/tables -> content (frozen old to_fhir_location) ────

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


def _build_content(bind, loc):
    pk = loc["id"]
    identifiers = []
    for i in _rows(bind, "SELECT * FROM location_identifier WHERE location_pk = :pk ORDER BY id", pk=pk):
        codings = _rows(bind, "SELECT * FROM location_identifier_type_coding WHERE location_identifier_id = :id ORDER BY id", id=i["id"])
        identifiers.append({
            "use": i["use"],
            "type": {"coding": [_coding(c) for c in codings], "text": i["type_text"]},
            "system": i["system"], "value": i["value"],
            "period": _period(i["period_start"], i["period_end"]),
            "assigner": _old_reference(i, "assigner", "assigner_reference"),
        })
    types = []
    for t in _rows(bind, "SELECT * FROM location_type WHERE location_pk = :pk ORDER BY id", pk=pk):
        codings = _rows(bind, "SELECT * FROM location_type_coding WHERE location_type_id = :id ORDER BY id", id=t["id"])
        types.append({"coding": [_coding(c) for c in codings], "text": t["text"]})
    telecoms = [{
        "system": t["system"], "value": t["value"], "use": t["use"], "rank": t["rank"],
        "period": _period(t["period_start"], t["period_end"]),
    } for t in _rows(bind, "SELECT * FROM location_telecom WHERE location_pk = :pk ORDER BY id", pk=pk)]
    physical = _rows(bind, "SELECT * FROM location_physical_type_coding WHERE location_pk = :pk ORDER BY id", pk=pk)
    hours = [{
        "daysOfWeek": h["days"], "allDay": h["all_day"],
        "openingTime": _iso(h["opening_time"]), "closingTime": _iso(h["closing_time"]),
    } for h in _rows(bind, "SELECT days_of_week::text[] AS days, all_day, opening_time, closing_time "
                           "FROM location_hours_of_operation WHERE location_pk = :pk ORDER BY id", pk=pk)]
    endpoints = [_old_reference(e, "reference", "reference_reference")
                 for e in _rows(bind, "SELECT * FROM location_endpoint WHERE location_pk = :pk ORDER BY id", pk=pk)]
    position = None
    if loc["position_longitude"] is not None and loc["position_latitude"] is not None:
        position = {"longitude": _num(loc["position_longitude"]), "latitude": _num(loc["position_latitude"]),
                    "altitude": _num(loc["position_altitude"])}
    return _prune({
        "extension": _json(loc["extension"]),
        "identifier": identifiers,
        "status": loc["status"],
        "operationalStatus": {
            "system": loc["operational_status_system"], "version": loc["operational_status_version"],
            "code": loc["operational_status_code"], "display": loc["operational_status_display"],
            "userSelected": loc["operational_status_user_selected"],
        },
        "name": loc["name"],
        "alias": loc["alias"],
        "description": loc["description"],
        "mode": loc["mode"],
        "type": types,
        "telecom": telecoms,
        "address": {
            "use": loc["address_use"], "type": loc["address_type"], "text": loc["address_text"],
            "line": loc["address_line"], "city": loc["address_city"], "district": loc["address_district"],
            "state": loc["address_state"], "postalCode": loc["address_postal_code"],
            "country": loc["address_country"],
            "period": _period(loc["address_period_start"], loc["address_period_end"]),
        },
        "physicalType": {"coding": [_coding(c) for c in physical], "text": loc["physical_type_text"]},
        "position": position,
        "managingOrganization": _old_reference(loc, "managing_organization", "managing_organization_reference"),
        "partOf": _old_reference(loc, "part_of", "part_of_reference"),
        "hoursOfOperation": hours,
        "availabilityExceptions": loc["availability_exceptions"],
        "endpoint": endpoints,
    })


def _backfill_content(bind):
    for loc in _rows(bind, "SELECT * FROM location"):
        bind.execute(
            sa.text("UPDATE location SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, loc)), "id": loc["id"]},
        )


# ── upgrade: content -> search index (frozen copy of location/_indexer.py) ───

def _ref_index(prefix, ref, resource_type):
    ref = ref or {}
    local = _relative(ref.get("reference"), resource_type)
    ident = ref.get("identifier") or {}
    return {
        f"{prefix}_reference": ref.get("reference"),
        f"{prefix}_type": resource_type if local else None,
        f"{prefix}_id": int(local.split("/", 1)[1]) if local else None,
        f"{prefix}_identifier_system": ident.get("system"),
        f"{prefix}_identifier_value": ident.get("value"),
    }


_INDEX_CASTS = {"status": "location_status", "address_use": "address_use",
                "managing_organization_type": "organization_reference_type",
                "part_of_type": "location_part_of_reference_type"}


def _rebuild_index(bind):
    for loc in _rows(bind, "SELECT id, content FROM location"):
        pk, doc = loc["id"], _json(loc["content"])
        op_status = doc.get("operationalStatus") or {}
        address = doc.get("address") or {}
        lines = [x for x in address.get("line") or [] if x] or None
        aliases = [a for a in doc.get("alias") or [] if a] or None
        position = doc.get("position") or {}
        cols = {
            "status": doc.get("status"),
            "operational_status_system": op_status.get("system"),
            "operational_status_code": op_status.get("code"),
            "operational_status_display_norm": _norm(op_status.get("display")),
            "name": doc.get("name"), "name_norm": _norm(doc.get("name")),
            "alias": aliases, "alias_norm": _norms(aliases),
            "address_use": address.get("use"),
            "address_text": address.get("text"), "address_text_norm": _norm(address.get("text")),
            "address_line": lines, "address_line_norm": _norms(lines),
            "address_city": address.get("city"), "address_city_norm": _norm(address.get("city")),
            "address_district": address.get("district"), "address_district_norm": _norm(address.get("district")),
            "address_state": address.get("state"), "address_state_norm": _norm(address.get("state")),
            "address_postal_code": address.get("postalCode"),
            "address_postal_code_norm": _norm(address.get("postalCode")),
            "address_country": address.get("country"), "address_country_norm": _norm(address.get("country")),
            **_ref_index("managing_organization", doc.get("managingOrganization"), "Organization"),
            **_ref_index("part_of", doc.get("partOf"), "Location"),
            "position_latitude": position.get("latitude"),
            "position_longitude": position.get("longitude"),
        }
        sets = ", ".join(f"{k} = CAST(:{k} AS {_INDEX_CASTS[k]})" if k in _INDEX_CASTS else f"{k} = :{k}"
                         for k in cols)
        bind.execute(sa.text(f"UPDATE location SET {sets} WHERE id = :pk"), {**cols, "pk": pk})

        for i in doc.get("identifier") or []:
            if not (i.get("system") or i.get("value")):
                continue
            itype = i.get("type") or {}
            for c in itype.get("coding") or [{}]:
                bind.execute(sa.text(
                    "INSERT INTO location_identifier (location_pk, system, value, type_system, type_code, "
                    "type_text_norm, type_display_norm) VALUES (:pk, :s, :v, :ts, :tc, :tt, :td)"),
                    {"pk": pk, "s": i.get("system"), "v": i.get("value"), "ts": c.get("system"),
                     "tc": c.get("code"), "tt": _norm(itype.get("text")), "td": _norm(c.get("display"))})
        for cc in doc.get("type") or []:
            text = _norm(cc.get("text"))
            codings = [c for c in cc.get("coding") or [] if c.get("system") or c.get("code") or c.get("display")]
            for c in codings or ([{}] if text else []):
                bind.execute(sa.text(
                    "INSERT INTO location_type (location_pk, system, code, display_norm, text_norm) "
                    "VALUES (:pk, :s, :c, :d, :t)"),
                    {"pk": pk, "s": c.get("system"), "c": c.get("code"), "d": _norm(c.get("display")), "t": text})
        for e in doc.get("endpoint") or []:
            ident = e.get("identifier") or {}
            if not (e.get("reference") or ident.get("value")):
                continue
            local = _relative(e.get("reference"), "Endpoint")
            bind.execute(sa.text(
                "INSERT INTO location_endpoint (location_pk, reference_reference, reference_type, reference_id, "
                "reference_identifier_system, reference_identifier_value) "
                "VALUES (:pk, :r, CAST(:t AS location_endpoint_reference_type), :i, :is_, :iv)"),
                {"pk": pk, "r": e.get("reference"), "t": "Endpoint" if local else None,
                 "i": int(local.split("/", 1)[1]) if local else None,
                 "is_": ident.get("system"), "iv": ident.get("value")})


_OLD_CHILD_TABLES_IN_DELETE_ORDER = (
    "location_identifier_type_coding", "location_identifier", "location_type_coding", "location_type",
    "location_telecom", "location_hours_of_operation", "location_endpoint", "location_physical_type_coding",
)
_AUDIT = ("created_at", "created_by", "tenant_id", "updated_at", "updated_by")
_REF_FALLBACK = ("use", "type_system", "type_version", "type_code", "type_display", "type_text",
                 "type_user_selected", "period_start", "period_end")


def _drop_audit(table):
    for col in ("created_at", "tenant_id", "updated_at"):
        op.drop_index(op.f(f"ix_{table}_{col}"), table_name=table)
    for col in _AUDIT:
        op.drop_column(table, col)


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column('location', sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    _backfill_content(bind)

    # Every old child row is now represented in `content`; index rows are
    # rebuilt from it below, so clear them all before reshaping.
    for table in _OLD_CHILD_TABLES_IN_DELETE_ORDER:
        op.execute(f"DELETE FROM {table}")
    for table in ("location_identifier_type_coding", "location_type_coding", "location_telecom",
                  "location_hours_of_operation", "location_physical_type_coding"):
        op.drop_table(table)

    # ── location ──
    for col in ("operational_status_version", "operational_status_display", "operational_status_user_selected",
                "description", "mode", "physical_type_text", "managing_organization_display", "part_of_display",
                "availability_exceptions", "position_altitude", "extension", "address_type",
                "address_period_start", "address_period_end"):
        op.drop_column('location', col)
    for prefix in ("managing_organization_identifier_", "part_of_identifier_"):
        for col in _REF_FALLBACK:
            op.drop_column('location', prefix + col)
    for col in ("operational_status_display_norm", "name_norm", "address_text_norm", "address_city_norm",
                "address_district_norm", "address_state_norm", "address_postal_code_norm", "address_country_norm"):
        op.add_column('location', sa.Column(col, sa.String(), nullable=True))
    for col in ("alias_norm", "address_line_norm"):
        op.add_column('location', sa.Column(col, postgresql.ARRAY(sa.String()), nullable=True))
    op.create_index('ix_location_name_norm', 'location', ['name_norm'], unique=False,
                    postgresql_ops={'name_norm': 'text_pattern_ops'})

    # ── location_identifier ──
    op.drop_index(op.f('ix_location_identifier_assigner_id'), table_name='location_identifier')
    _drop_audit('location_identifier')
    for col in ("use", "type_text", "period_start", "period_end", "assigner_reference", "assigner_type",
                "assigner_id", "assigner_display", "assigner_identifier_system", "assigner_identifier_value"):
        op.drop_column('location_identifier', col)
    for col in _REF_FALLBACK:
        op.drop_column('location_identifier', "assigner_identifier_" + col)
    for col in ("type_system", "type_code", "type_text_norm", "type_display_norm"):
        op.add_column('location_identifier', sa.Column(col, sa.String(), nullable=True))
    op.create_index(op.f('ix_location_identifier_value'), 'location_identifier', ['value'], unique=False)

    # ── location_type ──
    _drop_audit('location_type')
    op.drop_column('location_type', 'text')
    for col in ("system", "code", "display_norm", "text_norm"):
        op.add_column('location_type', sa.Column(col, sa.String(), nullable=True))
    op.create_index(op.f('ix_location_type_code'), 'location_type', ['code'], unique=False)

    # ── location_endpoint ──
    _drop_audit('location_endpoint')
    op.drop_column('location_endpoint', 'reference_display')
    for col in _REF_FALLBACK:
        op.drop_column('location_endpoint', "reference_identifier_" + col)

    _rebuild_index(bind)
    op.alter_column('location', 'content', nullable=False)


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


_CASTS = {
    "use": "identifier_use", "assigner_identifier_use": "identifier_use",
    "managing_organization_identifier_use": "identifier_use", "part_of_identifier_use": "identifier_use",
    "reference_identifier_use": "identifier_use",
    "assigner_type": "organization_reference_type", "managing_organization_type": "organization_reference_type",
    "part_of_type": "location_part_of_reference_type", "reference_type": "location_endpoint_reference_type",
    "status": "location_status", "mode": "location_mode", "address_use": "address_use",
    "address_type": "address_type",
}


def _insert(bind, table, values, casts=None, returning=False):
    casts = {**_CASTS, **(casts or {})}
    cols = list(values)
    params = ", ".join(f"CAST(:{c} AS {casts[c]})" if c in casts else f":{c}" for c in cols)
    sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({params})" + (" RETURNING id" if returning else "")
    result = bind.execute(sa.text(sql), values)
    return result.scalar() if returning else None


def _restore_old(bind):
    for loc in _rows(bind, "SELECT id, tenant_id, created_by, content FROM location"):
        pk, doc = loc["id"], _json(loc["content"]) or {}
        audit = {"tenant_id": loc["tenant_id"], "created_by": loc["created_by"]}
        op_status = doc.get("operationalStatus") or {}
        address = doc.get("address") or {}
        a_period = address.get("period") or {}
        position = doc.get("position") or {}
        main = {
            "extension": json.dumps(doc.get("extension") or []),
            "operational_status_version": op_status.get("version"),
            "operational_status_display": op_status.get("display"),
            "operational_status_user_selected": op_status.get("userSelected"),
            "description": doc.get("description"), "mode": doc.get("mode"),
            "physical_type_text": (doc.get("physicalType") or {}).get("text"),
            "availability_exceptions": doc.get("availabilityExceptions"),
            "position_altitude": position.get("altitude"),
            "address_type": address.get("type"),
            "address_period_start": _dt(a_period.get("start")), "address_period_end": _dt(a_period.get("end")),
            **_ref_columns("managing_organization", "managing_organization_reference",
                           doc.get("managingOrganization"), "Organization"),
            **_ref_columns("part_of", "part_of_reference", doc.get("partOf"), "Location"),
        }
        sets = ", ".join(
            f"{k} = CAST(:{k} AS {_CASTS[k]})" if k in _CASTS
            else (f"{k} = CAST(:{k} AS jsonb)" if k == "extension" else f"{k} = :{k}")
            for k in main)
        bind.execute(sa.text(f"UPDATE location SET {sets} WHERE id = :pk"), {**main, "pk": pk})

        for c in (doc.get("physicalType") or {}).get("coding") or []:
            _insert(bind, "location_physical_type_coding", {
                "location_pk": pk, "system": c.get("system"), "version": c.get("version"),
                "code": c.get("code"), "display": c.get("display"), "user_selected": c.get("userSelected"), **audit})
        for i in doc.get("identifier") or []:
            t = i.get("type") or {}
            p = i.get("period") or {}
            iid = _insert(bind, "location_identifier", {
                "location_pk": pk, "use": i.get("use"), "type_text": t.get("text"),
                "system": i.get("system"), "value": i.get("value"),
                "period_start": _dt(p.get("start")), "period_end": _dt(p.get("end")),
                **_ref_columns("assigner", "assigner_reference", i.get("assigner"), "Organization"),
                **audit}, returning=True)
            for c in t.get("coding") or []:
                _insert(bind, "location_identifier_type_coding", {
                    "location_identifier_id": iid, "system": c.get("system"), "version": c.get("version"),
                    "code": c.get("code"), "display": c.get("display"), "user_selected": c.get("userSelected"),
                    **audit})
        for cc in doc.get("type") or []:
            tid = _insert(bind, "location_type", {"location_pk": pk, "text": cc.get("text"), **audit}, returning=True)
            for c in cc.get("coding") or []:
                _insert(bind, "location_type_coding", {
                    "location_type_id": tid, "system": c.get("system"), "version": c.get("version"),
                    "code": c.get("code"), "display": c.get("display"), "user_selected": c.get("userSelected"),
                    **audit})
        for t in doc.get("telecom") or []:
            p = t.get("period") or {}
            _insert(bind, "location_telecom", {
                "location_pk": pk, "system": t.get("system"), "value": t.get("value"), "use": t.get("use"),
                "rank": t.get("rank"), "period_start": _dt(p.get("start")), "period_end": _dt(p.get("end")), **audit},
                casts={"system": "contact_point_system", "use": "contact_point_use"})
        for h in doc.get("hoursOfOperation") or []:
            _insert(bind, "location_hours_of_operation", {
                "location_pk": pk, "days_of_week": h.get("daysOfWeek"), "all_day": h.get("allDay"),
                "opening_time": time.fromisoformat(h["openingTime"]) if h.get("openingTime") else None,
                "closing_time": time.fromisoformat(h["closingTime"]) if h.get("closingTime") else None,
                **audit}, casts={"days_of_week": "location_day_of_week[]"})
        for e in doc.get("endpoint") or []:
            _insert(bind, "location_endpoint", {
                "location_pk": pk, **_ref_columns("reference", "reference_reference", e, "Endpoint"), **audit})


def _audit_columns():
    return [
        sa.Column('tenant_id', sa.VARCHAR(), nullable=False),
        sa.Column('created_by', sa.VARCHAR(), nullable=False),
        sa.Column('updated_by', sa.VARCHAR(), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
    ]


def _add_audit(table):
    for column in _audit_columns():
        op.add_column(table, column)
    for col in ("created_at", "tenant_id", "updated_at"):
        op.create_index(op.f(f"ix_{table}_{col}"), table, [col], unique=False)


def _ref_fallback_columns(prefix):
    iu = postgresql.ENUM(name='identifier_use', create_type=False)
    cols = [sa.Column(f"{prefix}use", iu, nullable=True)]
    cols += [sa.Column(f"{prefix}{c}", sa.VARCHAR(), nullable=True)
             for c in ("type_system", "type_version", "type_code", "type_display", "type_text")]
    cols += [sa.Column(f"{prefix}type_user_selected", sa.BOOLEAN(), nullable=True)]
    cols += [sa.Column(f"{prefix}{c}", postgresql.TIMESTAMP(timezone=True), nullable=True)
             for c in ("period_start", "period_end")]
    return cols


def _coding_table(name, fk_col, fk_target):
    op.create_table(
        name,
        sa.Column('id', sa.BIGINT(), autoincrement=True, nullable=False),
        sa.Column(fk_col, sa.BIGINT(), nullable=False),
        sa.Column('system', sa.VARCHAR(), nullable=True),
        sa.Column('version', sa.VARCHAR(), nullable=True),
        sa.Column('code', sa.VARCHAR(), nullable=True),
        sa.Column('display', sa.VARCHAR(), nullable=True),
        sa.Column('user_selected', sa.BOOLEAN(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint([fk_col], [fk_target], name=op.f(f'{name}_{fk_col}_fkey')),
        sa.PrimaryKeyConstraint('id', name=op.f(f'{name}_pkey')),
    )
    for col in (fk_col, "created_at", "tenant_id", "updated_at"):
        op.create_index(op.f(f"ix_{name}_{col}"), name, [col], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    # Index rows are rebuilt (in the old shape) from `content` below.
    for table in ("location_identifier", "location_type", "location_endpoint"):
        op.execute(f"DELETE FROM {table}")

    # ── location_endpoint ──
    _add_audit('location_endpoint')
    op.add_column('location_endpoint', sa.Column('reference_display', sa.VARCHAR(), nullable=True))
    for column in _ref_fallback_columns("reference_identifier_"):
        op.add_column('location_endpoint', column)

    # ── location_type (system/code dropped after _restore_old) ──
    op.drop_column('location_type', 'display_norm')
    op.drop_column('location_type', 'text_norm')
    _add_audit('location_type')
    op.add_column('location_type', sa.Column('text', sa.VARCHAR(), nullable=True))

    # ── location_identifier ──
    op.drop_index(op.f('ix_location_identifier_value'), table_name='location_identifier')
    for col in ("type_system", "type_code", "type_text_norm", "type_display_norm"):
        op.drop_column('location_identifier', col)
    _add_audit('location_identifier')
    iu = postgresql.ENUM(name='identifier_use', create_type=False)
    op.add_column('location_identifier', sa.Column('use', iu, nullable=True))
    op.add_column('location_identifier', sa.Column('type_text', sa.VARCHAR(), nullable=True))
    op.add_column('location_identifier', sa.Column('period_start', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('location_identifier', sa.Column('period_end', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('location_identifier', sa.Column('assigner_reference', sa.VARCHAR(), nullable=True))
    op.add_column('location_identifier', sa.Column(
        'assigner_type', postgresql.ENUM(name='organization_reference_type', create_type=False), nullable=True))
    op.add_column('location_identifier', sa.Column('assigner_id', sa.BIGINT(), nullable=True))
    op.add_column('location_identifier', sa.Column('assigner_display', sa.VARCHAR(), nullable=True))
    for column in _ref_fallback_columns("assigner_identifier_"):
        op.add_column('location_identifier', column)
    op.add_column('location_identifier', sa.Column('assigner_identifier_system', sa.VARCHAR(), nullable=True))
    op.add_column('location_identifier', sa.Column('assigner_identifier_value', sa.VARCHAR(), nullable=True))
    op.create_index(op.f('ix_location_identifier_assigner_id'), 'location_identifier', ['assigner_id'], unique=False)

    # ── location (content dropped after _restore_old) ──
    op.drop_index('ix_location_name_norm', table_name='location')
    for col in ("operational_status_display_norm", "name_norm", "alias_norm", "address_text_norm",
                "address_line_norm", "address_city_norm", "address_district_norm", "address_state_norm",
                "address_postal_code_norm", "address_country_norm"):
        op.drop_column('location', col)
    op.add_column('location', sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()),
                                        server_default=sa.text("'[]'::jsonb"), nullable=False))
    op.add_column('location', sa.Column('operational_status_version', sa.VARCHAR(), nullable=True))
    op.add_column('location', sa.Column('operational_status_display', sa.VARCHAR(), nullable=True))
    op.add_column('location', sa.Column('operational_status_user_selected', sa.BOOLEAN(), nullable=True))
    op.add_column('location', sa.Column('description', sa.TEXT(), nullable=True))
    op.add_column('location', sa.Column('mode', postgresql.ENUM(name='location_mode', create_type=False), nullable=True))
    op.add_column('location', sa.Column('physical_type_text', sa.VARCHAR(), nullable=True))
    op.add_column('location', sa.Column('availability_exceptions', sa.TEXT(), nullable=True))
    op.add_column('location', sa.Column('position_altitude', sa.Numeric(18, 8), nullable=True))
    op.add_column('location', sa.Column('address_type', postgresql.ENUM(name='address_type', create_type=False), nullable=True))
    op.add_column('location', sa.Column('address_period_start', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('location', sa.Column('address_period_end', postgresql.TIMESTAMP(timezone=True), nullable=True))
    op.add_column('location', sa.Column('managing_organization_display', sa.VARCHAR(), nullable=True))
    op.add_column('location', sa.Column('part_of_display', sa.VARCHAR(), nullable=True))
    for prefix in ("managing_organization_identifier_", "part_of_identifier_"):
        for column in _ref_fallback_columns(prefix):
            op.add_column('location', column)

    # ── dropped tables, recreated in FK order ──
    _coding_table('location_physical_type_coding', 'location_pk', 'location.id')
    _coding_table('location_identifier_type_coding', 'location_identifier_id', 'location_identifier.id')
    _coding_table('location_type_coding', 'location_type_id', 'location_type.id')
    op.create_table(
        'location_telecom',
        sa.Column('id', sa.BIGINT(), autoincrement=True, nullable=False),
        sa.Column('location_pk', sa.BIGINT(), nullable=False),
        sa.Column('system', postgresql.ENUM(name='contact_point_system', create_type=False), nullable=True),
        sa.Column('value', sa.VARCHAR(), nullable=True),
        sa.Column('use', postgresql.ENUM(name='contact_point_use', create_type=False), nullable=True),
        sa.Column('rank', sa.INTEGER(), nullable=True),
        sa.Column('period_start', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('period_end', postgresql.TIMESTAMP(timezone=True), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(['location_pk'], ['location.id'], name=op.f('location_telecom_location_pk_fkey')),
        sa.PrimaryKeyConstraint('id', name=op.f('location_telecom_pkey')),
    )
    for col in ("location_pk", "created_at", "tenant_id", "updated_at"):
        op.create_index(op.f(f"ix_location_telecom_{col}"), 'location_telecom', [col], unique=False)
    op.create_table(
        'location_hours_of_operation',
        sa.Column('id', sa.BIGINT(), autoincrement=True, nullable=False),
        sa.Column('location_pk', sa.BIGINT(), nullable=False),
        sa.Column('days_of_week', postgresql.ARRAY(postgresql.ENUM(name='location_day_of_week', create_type=False)),
                  nullable=True),
        sa.Column('all_day', sa.BOOLEAN(), nullable=True),
        sa.Column('opening_time', sa.TIME(), nullable=True),
        sa.Column('closing_time', sa.TIME(), nullable=True),
        *_audit_columns(),
        sa.ForeignKeyConstraint(['location_pk'], ['location.id'],
                                name=op.f('location_hours_of_operation_location_pk_fkey')),
        sa.PrimaryKeyConstraint('id', name=op.f('location_hours_of_operation_pkey')),
    )
    for col in ("location_pk", "created_at", "tenant_id", "updated_at"):
        op.create_index(op.f(f"ix_location_hours_of_operation_{col}"), 'location_hours_of_operation', [col],
                        unique=False)

    _restore_old(bind)
    op.drop_index(op.f('ix_location_type_code'), table_name='location_type')
    op.drop_column('location_type', 'code')
    op.drop_column('location_type', 'system')
    op.drop_column('location', 'content')
