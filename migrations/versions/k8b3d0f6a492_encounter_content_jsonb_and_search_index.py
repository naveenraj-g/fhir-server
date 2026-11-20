"""encounter: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: k8b3d0f6a492
Revises: j7a2c9e5f381
Create Date: 2026-11-27 10:00:00.000000

Medplum-style storage for Encounter (see EncounterModel's docstring), same as
the other resources already moved (Organization 5b1969c2ec19, Location
8c41d2e7a9b3, Practitioner a7d3f19c2b64, HealthcareService c9f5b2d7e813,
Endpoint d1a6c3e8f924, PractitionerRole e2b7d4f9a035, Schedule f3c8e5a1b947,
Slot g4d9f6b2c058, Patient h5e0a7c3d169, Appointment i6f1b8d4e27a,
AppointmentResponse j7a2c9e5f381). The whole FHIR resource moves into
`encounter.content`; every column/table that survives is a search index for one
of the FHIR R4 Encounter search parameters (or `_id`/`_lastUpdated`), derived
from `content`:

  encounter: status (rebuilt as a Postgres enum holding the real FHIR codes),
      class_system/class_code/class_display_norm, period_start/period_end,
      length_value/_system/_code/_unit, subject_*, part_of_*, service_provider_*
      (`*_type` becomes a plain string); new: content
  encounter_identifier: rebuilt, one row per identifier x type.coding
  encounter_token: `type`, `reason-code`, `special-arrangement`,
      `participant-type`, one row per coding
  encounter_reference: `account`, `appointment`, `based-on`, `diagnosis`,
      `episode-of-care`, `reason-reference`
  encounter_participant: rebuilt, one row per participant individual
  encounter_location: rebuilt, one row per location (reference + period)
  dropped: every other old child table (status/class history, type, reason,
      diagnosis, hospitalization, ...) and the main-table columns with no search
      parameter (serviceType/priority text, length comparator, extension, the
      reference displays and logical-identifier details no search reads), plus
      the enums only the old tables used.

`status`: the old `encounter_status` enum stored Python member names
(`in_progress`, `entered_in_error`), not the FHIR code. It is dropped and
recreated with the real codes (`in-progress`, ...), and every row's status is
rebuilt from `content`.

upgrade: (1) builds `content` for every existing row from the old columns and
tables — a frozen copy of the old to_fhir_encounter() logic (but keeping a
reference's raw string, so an absolute URL is not lost), so this migration never
depends on application code that has since changed; (2) drops the old child
tables/columns and creates the index tables; (3) rebuilds the index from
`content`.

downgrade: not supported. Everything the old schema held is preserved in
`content`, but rebuilding the old normalized tables from it is not implemented —
restore from a backup taken before upgrading.
"""
import json
import re
import unicodedata
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'k8b3d0f6a492'
down_revision: Union[str, None] = 'j7a2c9e5f381'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STATUS = ('planned', 'arrived', 'triaged', 'in-progress', 'onleave', 'finished', 'cancelled',
           'entered-in-error', 'unknown')
_COMPARATOR = {'lt': '<', 'le': '<=', 'ge': '>=', 'gt': '>'}


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


def _hyphenate(old):
    """The old enums stored member names (`in_progress`); FHIR codes are hyphenated."""
    return str(old).replace("_", "-") if old is not None else None


def _number(value):
    if value is None:
        return None
    value = Decimal(value)
    return int(value) if value == value.to_integral_value() else float(value)


# ── upgrade: old columns/tables -> content (frozen copy of the old mapper) ───

def _coding(c):
    return {"system": c["system"], "version": c["version"], "code": c["code"],
            "display": c["display"], "userSelected": c["user_selected"]}


def _cc(bind, table, fk, fk_id, text):
    codings = _rows(bind, f"SELECT * FROM {table} WHERE {fk} = :id ORDER BY id", id=fk_id)
    return {"coding": [_coding(c) for c in codings], "text": text}


def _cc_list(bind, parent_table, parent_fk, parent_id, coding_table, coding_fk):
    """A 0..* CodeableConcept held as a text-only parent table + a coding child table."""
    return [
        _cc(bind, coding_table, coding_fk, p["id"], p["text"])
        for p in _rows(bind, f"SELECT * FROM {parent_table} WHERE {parent_fk} = :id ORDER BY id", id=parent_id)
    ]


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
    """Keeps the raw reference string when there is one (an absolute URL to
    another server lives only there), else Type/id from the resolved columns."""
    raw = row[f"{prefix}_reference"]
    if not raw and row[f"{prefix}_type"] and row[f"{prefix}_id"]:
        raw = f"{row[prefix + '_type']}/{row[prefix + '_id']}"
    return {
        "reference": raw,
        "display": row[f"{prefix}_display"],
        "identifier": _fallback_identifier(row, prefix),
    }


def _identifiers(bind, pk):
    out = []
    for i in _rows(bind, "SELECT * FROM encounter_identifier WHERE encounter_pk = :pk ORDER BY id", pk=pk):
        out.append({
            "use": i["use"],
            "type": _cc(bind, "encounter_identifier_type_coding", "encounter_identifier_id", i["id"], i["type_text"]),
            "system": i["system"], "value": i["value"],
            "period": _period(i["period_start"], i["period_end"]),
            "assigner": _old_reference(i, "assigner"),
        })
    return out


def _references(bind, table, pk):
    return [_old_reference(r, "reference")
            for r in _rows(bind, f"SELECT * FROM {table} WHERE encounter_pk = :pk ORDER BY id", pk=pk)]


def _participants(bind, pk):
    out = []
    for p in _rows(bind, "SELECT * FROM encounter_participant WHERE encounter_pk = :pk ORDER BY id", pk=pk):
        out.append({
            "type": _cc_list(bind, "encounter_participant_type", "encounter_participant_id", p["id"],
                             "encounter_participant_type_coding", "encounter_participant_type_id"),
            "period": _period(p["period_start"], p["period_end"]),
            "individual": _old_reference(p, "individual"),
        })
    return out


def _diagnoses(bind, pk):
    out = []
    for d in _rows(bind, "SELECT * FROM encounter_diagnosis WHERE encounter_pk = :pk ORDER BY id", pk=pk):
        out.append({
            "condition": _old_reference(d, "condition"),
            "use": _cc(bind, "encounter_diagnosis_use_coding", "encounter_diagnosis_id", d["id"], d["use_text"]),
            "rank": d["rank"],
        })
    return out


def _locations(bind, pk):
    out = []
    for loc in _rows(bind, "SELECT * FROM encounter_location WHERE encounter_pk = :pk ORDER BY id", pk=pk):
        out.append({
            "location": _old_reference(loc, "location"),
            "status": loc["status"],
            "physicalType": _cc(bind, "encounter_location_physical_type_coding", "encounter_location_id",
                                loc["id"], loc["physical_type_text"]),
            "period": _period(loc["period_start"], loc["period_end"]),
        })
    return out


def _hospitalization(bind, pk):
    rows = _rows(bind, "SELECT * FROM encounter_hospitalization WHERE encounter_pk = :pk ORDER BY id LIMIT 1", pk=pk)
    if not rows:
        return None
    h = rows[0]
    hid = h["id"]
    pre = "pre_admission_identifier"

    def cc(table, text):
        return _cc(bind, f"encounter_hospitalization_{table}_coding", "encounter_hospitalization_id", hid, text)

    def cc_list(table):
        return _cc_list(bind, f"encounter_hospitalization_{table}", "encounter_hospitalization_id", hid,
                        f"encounter_hospitalization_{table}_coding", f"encounter_hospitalization_{table}_id")

    return {
        "preAdmissionIdentifier": {
            "use": h[f"{pre}_use"],
            "type": cc("pre_admission_identifier_type", h[f"{pre}_type_text"]),
            "system": h[f"{pre}_system"], "value": h[f"{pre}_value"],
            "period": _period(h[f"{pre}_period_start"], h[f"{pre}_period_end"]),
            "assigner": _old_reference(h, f"{pre}_assigner"),
        },
        "origin": _old_reference(h, "origin"),
        "admitSource": cc("admit_source", h["admit_source_text"]),
        "reAdmission": cc("re_admission", h["re_admission_text"]),
        "dietPreference": cc_list("diet_preference"),
        "specialCourtesy": cc_list("special_courtesy"),
        "specialArrangement": cc_list("special_arrangement"),
        "destination": _old_reference(h, "destination"),
        "dischargeDisposition": cc("discharge_disposition", h["discharge_disposition_text"]),
    }


def _build_content(bind, r):
    pk = r["id"]
    status_history = [
        {"status": _hyphenate(s["status"]), "period": _period(s["period_start"], s["period_end"])}
        for s in _rows(bind, "SELECT * FROM encounter_status_history WHERE encounter_pk = :pk ORDER BY id", pk=pk)
    ]
    class_history = [
        {"class": _coding({"system": c["class_system"], "version": c["class_version"], "code": c["class_code"],
                           "display": c["class_display"], "user_selected": c["class_user_selected"]}),
         "period": _period(c["period_start"], c["period_end"])}
        for c in _rows(bind, "SELECT * FROM encounter_class_history WHERE encounter_pk = :pk ORDER BY id", pk=pk)
    ]
    length = {
        "value": _number(r["length_value"]),
        "comparator": _COMPARATOR.get(r["length_comparator"], r["length_comparator"]),
        "unit": r["length_unit"], "system": r["length_system"], "code": r["length_code"],
    }
    return _prune({
        "extension": _json(r["extension"]),
        "identifier": _identifiers(bind, pk),
        "status": _hyphenate(r["status"]),
        "statusHistory": status_history,
        "class": _coding({"system": r["class_system"], "version": r["class_version"], "code": r["class_code"],
                          "display": r["class_display"], "user_selected": r["class_user_selected"]}),
        "classHistory": class_history,
        "type": _cc_list(bind, "encounter_type", "encounter_pk", pk, "encounter_type_coding", "encounter_type_id"),
        "serviceType": _cc(bind, "encounter_service_type_coding", "encounter_pk", pk, r["service_type_text"]),
        "priority": _cc(bind, "encounter_priority_coding", "encounter_pk", pk, r["priority_text"]),
        "subject": _old_reference(r, "subject"),
        "episodeOfCare": _references(bind, "encounter_episode_of_care", pk),
        "basedOn": _references(bind, "encounter_based_on", pk),
        "participant": _participants(bind, pk),
        "appointment": _references(bind, "encounter_appointment", pk),
        "period": _period(r["period_start"], r["period_end"]),
        "length": length,
        "reasonCode": _cc_list(bind, "encounter_reason_code", "encounter_pk", pk,
                               "encounter_reason_code_coding", "encounter_reason_code_id"),
        "reasonReference": _references(bind, "encounter_reason_reference", pk),
        "diagnosis": _diagnoses(bind, pk),
        "account": _references(bind, "encounter_account", pk),
        "hospitalization": _hospitalization(bind, pk),
        "location": _locations(bind, pk),
        "serviceProvider": _old_reference(r, "service_provider"),
        "partOf": _old_reference(r, "part_of"),
    })


def _backfill_content(bind):
    for row in _rows(bind, "SELECT * FROM encounter"):
        bind.execute(
            sa.text("UPDATE encounter SET content = CAST(:c AS jsonb) WHERE id = :id"),
            {"c": json.dumps(_build_content(bind, row)), "id": row["id"]},
        )


# ── upgrade: content -> search index (frozen copy of _indexer.py) ────────────

SUBJECT_TYPES = ("Patient", "Group")
PARTICIPANT_TYPES = ("Practitioner", "PractitionerRole", "RelatedPerson")
REFERENCE_PARAMS = {
    "account": ("account", ("Account",)),
    "appointment": ("appointment", ("Appointment",)),
    "based-on": ("basedOn", ("ServiceRequest",)),
    "diagnosis": ("diagnosis.condition", ("Condition", "Procedure")),
    "episode-of-care": ("episodeOfCare", ("EpisodeOfCare",)),
    "reason-reference": ("reasonReference", ("Condition", "Observation", "Procedure", "ImmunizationRecommendation")),
}
TOKEN_PATHS = {
    "type": "type",
    "reason-code": "reasonCode",
    "special-arrangement": "hospitalization.specialArrangement",
    "participant-type": "participant.type",
}

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")


def _typed(reference, allowed):
    """('Patient', 10001) for a relative Type/<id> of an allowed type."""
    match = _REF.match(reference or "")
    if match and match["type"] in allowed:
        return match["type"], int(match["id"])
    return None


def _elements(document, path):
    values = [document]
    for key in path.split("."):
        nxt = []
        for v in values:
            item = v.get(key) if isinstance(v, dict) else None
            nxt.extend(item if isinstance(item, list) else [item])
        values = nxt
    return [v for v in values if v is not None]


def _bound(value, which):
    """Frozen period_bounds(): the first instant of a Period bound (`low`) or the
    first instant after it (`high`), in UTC. Stored values are full datetimes
    written by this migration's content builder."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    dt = dt.astimezone(UTC)
    if which == "low":
        return dt
    return dt + (timedelta(microseconds=1) if dt.microsecond else timedelta(seconds=1))


def _ref_params(prefix, ref, allowed):
    ref = ref or {}
    reference = ref.get("reference")
    ident = ref.get("identifier") or {}
    parsed = _typed(reference, allowed)
    return {f"{prefix}_reference": reference, f"{prefix}_type": parsed[0] if parsed else None,
            f"{prefix}_id": parsed[1] if parsed else None,
            f"{prefix}_identifier_system": ident.get("system"), f"{prefix}_identifier_value": ident.get("value")}


def _insert(bind, table, **cols):
    names = ", ".join(cols)
    values = ", ".join(f":{c}" for c in cols)
    bind.execute(sa.text(f"INSERT INTO {table} ({names}) VALUES ({values})"), cols)


def _child_ref_cols(ref, allowed):
    ref = ref or {}
    reference = ref.get("reference")
    ident = ref.get("identifier") or {}
    parsed = _typed(reference, allowed)
    return {"reference_reference": reference, "reference_type": parsed[0] if parsed else None,
            "reference_id": parsed[1] if parsed else None,
            "reference_identifier_system": ident.get("system"), "reference_identifier_value": ident.get("value")}


def _has_ref(ref):
    ref = ref or {}
    return bool(ref.get("reference") or (ref.get("identifier") or {}).get("value"))


def _rebuild_index(bind):
    for row in _rows(bind, "SELECT id, content FROM encounter"):
        pk, doc = row["id"], _json(row["content"])
        status = doc.get("status")
        cls = doc.get("class") or {}
        period = doc.get("period") or {}
        length = doc.get("length") or {}
        params = {
            "pk": pk, "status": status if status in _STATUS else None,
            "cs": cls.get("system"), "cc": cls.get("code"), "cd": _norm(cls.get("display")),
            "ps": _bound(period.get("start"), "low"), "pe": _bound(period.get("end"), "high"),
            "lv": Decimal(str(length["value"])) if length.get("value") is not None else None,
            "ls": length.get("system"), "lc": length.get("code"), "lu": length.get("unit"),
            **{f"s_{k}": v for k, v in _ref_params("subject", doc.get("subject"), SUBJECT_TYPES).items()},
            **{f"p_{k}": v for k, v in _ref_params("part_of", doc.get("partOf"), ("Encounter",)).items()},
            **{f"o_{k}": v for k, v in
               _ref_params("service_provider", doc.get("serviceProvider"), ("Organization",)).items()},
        }
        sets = ["status = CAST(:status AS encounter_status)", "class_system = :cs", "class_code = :cc",
                "class_display_norm = :cd", "period_start = :ps", "period_end = :pe", "length_value = :lv",
                "length_system = :ls", "length_code = :lc", "length_unit = :lu"]
        for prefix, tag in (("subject", "s"), ("part_of", "p"), ("service_provider", "o")):
            for suffix in ("reference", "type", "id", "identifier_system", "identifier_value"):
                sets.append(f"{prefix}_{suffix} = :{tag}_{prefix}_{suffix}")
        bind.execute(sa.text(f"UPDATE encounter SET {', '.join(sets)} WHERE id = :pk"), params)

        for i in doc.get("identifier") or []:
            if not (i.get("system") or i.get("value")):
                continue
            itype = i.get("type") or {}
            for c in itype.get("coding") or [{}]:
                _insert(bind, "encounter_identifier", encounter_pk=pk, system=i.get("system"), value=i.get("value"),
                        type_system=c.get("system"), type_code=c.get("code"),
                        type_text_norm=_norm(itype.get("text")), type_display_norm=_norm(c.get("display")))

        for param, path in TOKEN_PATHS.items():
            for concept in _elements(doc, path):
                text = _norm(concept.get("text"))
                coded = [c for c in concept.get("coding") or [] if c.get("system") or c.get("code") or c.get("display")]
                for c in coded:
                    _insert(bind, "encounter_token", encounter_pk=pk, param=param, system=c.get("system"),
                            code=c.get("code"), display_norm=_norm(c.get("display")), text_norm=text)
                if not coded and text:
                    _insert(bind, "encounter_token", encounter_pk=pk, param=param, system=None, code=None,
                            display_norm=None, text_norm=text)

        for param, (path, allowed) in REFERENCE_PARAMS.items():
            for ref in _elements(doc, path):
                if _has_ref(ref):
                    _insert(bind, "encounter_reference", encounter_pk=pk, param=param, **_child_ref_cols(ref, allowed))

        for p in doc.get("participant") or []:
            if _has_ref(p.get("individual")):
                _insert(bind, "encounter_participant", encounter_pk=pk,
                        **_child_ref_cols(p.get("individual"), PARTICIPANT_TYPES))

        for loc in doc.get("location") or []:
            lp = loc.get("period") or {}
            start, end = _bound(lp.get("start"), "low"), _bound(lp.get("end"), "high")
            if _has_ref(loc.get("location")) or start or end:
                _insert(bind, "encounter_location", encounter_pk=pk, period_start=start, period_end=end,
                        **_child_ref_cols(loc.get("location"), ("Location",)))


# Children first (grandchildren before their parents).
_OLD_CHILD_TABLES = (
    "encounter_hospitalization_special_arrangement_coding", "encounter_hospitalization_special_arrangement",
    "encounter_hospitalization_special_courtesy_coding", "encounter_hospitalization_special_courtesy",
    "encounter_hospitalization_diet_preference_coding", "encounter_hospitalization_diet_preference",
    "encounter_hospitalization_discharge_disposition_coding", "encounter_hospitalization_re_admission_coding",
    "encounter_hospitalization_admit_source_coding",
    "encounter_hospitalization_pre_admission_identifier_type_coding", "encounter_hospitalization",
    "encounter_location_physical_type_coding", "encounter_location",
    "encounter_participant_type_coding", "encounter_participant_type", "encounter_participant",
    "encounter_reason_code_coding", "encounter_reason_code", "encounter_reason_reference",
    "encounter_diagnosis_use_coding", "encounter_diagnosis",
    "encounter_account", "encounter_appointment", "encounter_based_on", "encounter_episode_of_care",
    "encounter_class_history", "encounter_status_history",
    "encounter_type_coding", "encounter_type",
    "encounter_identifier_type_coding", "encounter_identifier",
    "encounter_priority_coding", "encounter_service_type_coding",
)

_IDENTIFIER_PARTS = ("use", "type_system", "type_version", "type_code", "type_display", "type_text",
                     "type_user_selected", "period_start", "period_end")

_OLD_MAIN_COLUMNS = (
    "status", "extension", "service_type_text", "priority_text", "length_comparator",
    "class_version", "class_display", "class_user_selected",
    "subject_display", *(f"subject_identifier_{p}" for p in _IDENTIFIER_PARTS),
    "service_provider_display", *(f"service_provider_identifier_{p}" for p in _IDENTIFIER_PARTS),
    "part_of_display", *(f"part_of_identifier_{p}" for p in _IDENTIFIER_PARTS),
)

# Enums only the old tables used (`subject_reference_type`, `organization_reference_type`,
# `encounter_reference_type`, `appointment_reference_type` and `identifier_use` are shared and stay).
_OLD_ENUMS = (
    "encounter_status", "encounter_length_comparator", "encounter_location_status",
    "encounter_account_reference_type", "encounter_based_on_reference_type",
    "encounter_condition_or_procedure_reference_type", "encounter_episode_of_care_reference_type",
    "encounter_reason_reference_type", "encounter_hospitalization_reference_type",
    "encounter_location_reference_type", "encounter_participant_individual_reference_type",
)


def _reference_columns():
    return [
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_identifier_system', sa.String(), nullable=True),
        sa.Column('reference_identifier_value', sa.String(), nullable=True),
    ]


def _child_table(name, *columns):
    op.create_table(
        name,
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('encounter_pk', sa.BigInteger(), sa.ForeignKey('encounter.id'), nullable=False),
        *columns,
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f(f'ix_{name}_encounter_pk'), name, ['encounter_pk'])


def upgrade() -> None:
    bind = op.get_bind()
    op.add_column('encounter', sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    _backfill_content(bind)

    # Every old child row is now represented in `content`; the index rows are
    # rebuilt from it below.
    for table in _OLD_CHILD_TABLES:
        op.drop_table(table)
    for column in _OLD_MAIN_COLUMNS:
        op.drop_column('encounter', column)

    # The three reference-type columns were enums; they are plain strings now.
    for column in ('subject_type', 'part_of_type', 'service_provider_type'):
        op.alter_column('encounter', column, type_=sa.String(), nullable=True, postgresql_using=f'{column}::text')
    for enum in _OLD_ENUMS:
        op.execute(f"DROP TYPE IF EXISTS {enum}")

    # status: recreated as an enum holding the real FHIR codes.
    postgresql.ENUM(*_STATUS, name='encounter_status').create(bind, checkfirst=True)
    op.add_column('encounter', sa.Column(
        'status', postgresql.ENUM(*_STATUS, name='encounter_status', create_type=False), nullable=True))
    op.add_column('encounter', sa.Column('class_display_norm', sa.String(), nullable=True))
    for column in ('class_code', 'period_start', 'subject_id', 'part_of_id', 'service_provider_id'):
        op.execute(f"CREATE INDEX IF NOT EXISTS ix_encounter_{column} ON encounter ({column})")

    op.create_table(
        'encounter_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('encounter_pk', sa.BigInteger(), sa.ForeignKey('encounter.id'), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_text_norm', sa.String(), nullable=True),
        sa.Column('type_display_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_encounter_identifier_encounter_pk'), 'encounter_identifier', ['encounter_pk'])
    op.create_index(op.f('ix_encounter_identifier_value'), 'encounter_identifier', ['value'])

    _child_table(
        'encounter_token',
        sa.Column('param', sa.String(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display_norm', sa.String(), nullable=True),
        sa.Column('text_norm', sa.String(), nullable=True),
    )
    op.create_index('ix_encounter_token_param_code', 'encounter_token', ['param', 'code'])

    _child_table('encounter_reference', sa.Column('param', sa.String(), nullable=False), *_reference_columns())
    op.create_index('ix_encounter_reference_param_type_id', 'encounter_reference',
                    ['param', 'reference_type', 'reference_id'])

    _child_table('encounter_participant', *_reference_columns())
    op.create_index('ix_encounter_participant_type_id', 'encounter_participant', ['reference_type', 'reference_id'])

    _child_table(
        'encounter_location', *_reference_columns(),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_encounter_location_type_id', 'encounter_location', ['reference_type', 'reference_id'])

    _rebuild_index(bind)
    op.alter_column('encounter', 'content', nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "encounter content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
