"""care_team: store the whole resource in `content` JSONB; keep only search-index columns

Revision ID: d7c2e9a5b361
Revises: c6b1d8f4a250
Create Date: 2026-12-13 10:00:00.000000

Medplum-style storage for CareTeam (see CareTeamModel's docstring), same as the other resources
already moved (Organization 5b1969c2ec19 ... Specimen y2d7f4b0c816, ServiceRequest z3e8a5c1d927,
Medication a4f9b6d2e038, MedicationRequest b5a0c7e3f149, Group c6b1d8f4a250). The whole FHIR
resource moves into `care_team.content`; every column/table that survives is a search index for
one of the FHIR R4 CareTeam search parameters (or `_id` / `_lastUpdated`), derived from `content`:

  care_team: status (recreated as an enum holding the real FHIR codes - the old one stored
      `entered_in_error`), period_start/_end (`period`, the half-open range it covers; the old
      columns held the raw instants, so they are recomputed), the subject_* and encounter_*
      columns (`*_type` become plain strings); the public id gets its sequence as a server
      default; new: content.
  care_team_identifier: rebuilt as an index table
  care_team_token: new - category
  care_team_participant: rebuilt as an index table - one row per participant.member
  dropped: every old child table (identifier + its type coding, category + codings, participant
      + role + role codings, reasonCode + codings, reasonReference, managingOrganization,
      telecom, note), every main-table column with no search parameter (name, extension and the
      display / logical-identifier details of every reference) and the per-field `care_team_*`
      reference-type enums.

upgrade: (1) builds `content` for every existing row from the old columns and tables - a frozen
copy of the old to_fhir_care_team() logic (but keeping a reference's raw string, so an absolute
URL is not lost), so this migration never depends on application code that has since changed;
(2) drops the old child tables/columns and creates the index tables; (3) rebuilds the index from
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
revision: str = "d7c2e9a5b361"
down_revision: Union[str, None] = "c6b1d8f4a250"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

P = "care_team"

_STATUS = ("proposed", "active", "suspended", "inactive", "entered-in-error")


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
    """The FHIR code for an old status label (`entered_in_error` becomes `entered-in-error`)."""
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


# -- upgrade: old columns/tables -> content (frozen copy of the old mapper) -----------------

_TYPE_NAMES = {
    t.upper(): t
    for t in (
        "Patient",
        "Group",
        "Encounter",
        "Practitioner",
        "PractitionerRole",
        "RelatedPerson",
        "Organization",
        "CareTeam",
        "Condition",
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
    """The logical identifier of a Reference. Some old tables carry only part of these columns,
    so every one is read tolerantly."""
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
            _rows_of(bind, f"{P}_identifier_type_coding", "identifier_id", i["id"]),
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
        author = _prune(_ref(n, "author_reference"))
        if author:
            note["authorReference"] = author
    return note


def _participant(bind, p):
    return {
        "role": [
            _concept(
                _rows_of(bind, f"{P}_participant_role_coding", "role_id", r["id"]),
                r["text"],
            )
            for r in _rows_of(bind, f"{P}_participant_role", "participant_id", p["id"])
        ],
        "member": _ref(p, "member"),
        "onBehalfOf": _ref(p, "on_behalf_of"),
        "period": _period(p["period_start"], p["period_end"]),
    }


def _telecom(t):
    return {
        "system": t["system"],
        "value": t["value"],
        "use": t["use"],
        "rank": t["rank"],
        "period": _period(t["period_start"], t["period_end"]),
    }


def _build_content(bind, r):
    pk = r["id"]
    content = {
        "extension": list(_json(r["extension"]) or []),
        "identifier": [
            _identifier(bind, i) for i in _rows_of(bind, f"{P}_identifier", f"{P}_pk", pk)
        ],
        "status": _hyphenate(r["status_text"]),
        "category": [
            _concept(
                _rows_of(bind, f"{P}_category_coding", "category_id", c["id"]),
                c["text"],
            )
            for c in _rows_of(bind, f"{P}_category", f"{P}_pk", pk)
        ],
        "name": r["name"],
        "subject": _ref(r, "subject"),
        "encounter": _ref(r, "encounter"),
        "period": _period(r["period_start"], r["period_end"]),
        "participant": [
            _participant(bind, p)
            for p in _rows_of(bind, f"{P}_participant", f"{P}_pk", pk)
        ],
        "reasonCode": [
            _concept(
                _rows_of(bind, f"{P}_reason_code_coding", "reason_code_id", c["id"]),
                c["text"],
            )
            for c in _rows_of(bind, f"{P}_reason_code", f"{P}_pk", pk)
        ],
        "reasonReference": [
            _ref(x, "reference")
            for x in _rows_of(bind, f"{P}_reason_reference", f"{P}_pk", pk)
        ],
        "managingOrganization": [
            _ref(x, "reference")
            for x in _rows_of(bind, f"{P}_managing_organization", f"{P}_pk", pk)
        ],
        "telecom": [
            _telecom(t) for t in _rows_of(bind, f"{P}_telecom", f"{P}_pk", pk)
        ],
        "note": [_note(n) for n in _rows_of(bind, f"{P}_note", f"{P}_pk", pk)],
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
_SUBJECT_TYPES = ("Patient", "Group")
_ENCOUNTER_TYPES = ("Encounter",)
_PARTICIPANT_TYPES = (
    "Practitioner",
    "PractitionerRole",
    "RelatedPerson",
    "Patient",
    "Organization",
    "CareTeam",
)


def _typed(reference, allowed):
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


def _insert_participant(bind, pk, member):
    member = member or {}
    reference = member.get("reference")
    identifier = member.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return
    rtype, rid = _typed(reference, _PARTICIPANT_TYPES)
    bind.execute(
        sa.text(
            f"INSERT INTO {P}_participant ({P}_pk, reference_reference, reference_type, "
            "reference_id, reference_identifier_system, reference_identifier_value) "
            "VALUES (:pk, :r, :t, :i, :s, :v)"
        ),
        {
            "pk": pk,
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
        start, end = _period_bounds(doc.get("period"))
        status = doc.get("status")
        columns = {
            "period_start": start,
            "period_end": end,
            **_ref_params("subject", doc.get("subject"), _SUBJECT_TYPES),
            **_ref_params("encounter", doc.get("encounter"), _ENCOUNTER_TYPES),
        }
        sets = ", ".join(f"{k} = :{k}" for k in columns)
        bind.execute(
            sa.text(
                f"UPDATE {P} SET status = CAST(:status AS care_team_status), {sets} "
                "WHERE id = :pk"
            ),
            {**columns, "status": status if status in _STATUS else None, "pk": pk},
        )

        for i in doc.get("identifier") or []:
            _insert_identifier(bind, pk, i)
        for category in doc.get("category") or []:
            _insert_token(bind, pk, "category", category)
        for participant in doc.get("participant") or []:
            _insert_participant(bind, pk, (participant or {}).get("member"))


# Every old CareTeam table. The new index tables (identifier, participant) are dropped with them
# and recreated below; dropped with CASCADE, so order does not matter.
_OLD_TABLES = (
    "care_team_identifier_type_coding",
    "care_team_identifier",
    "care_team_category_coding",
    "care_team_category",
    "care_team_participant_role_coding",
    "care_team_participant_role",
    "care_team_participant",
    "care_team_reason_code_coding",
    "care_team_reason_code",
    "care_team_reason_reference",
    "care_team_managing_organization",
    "care_team_telecom",
    "care_team_note",
)

# The per-field enums of the old schema (the shared `identifier_use`, `contact_point_*` enums
# stay). `care_team_status` is recreated below with the real FHIR codes.
_OLD_ENUMS = (
    "care_team_status",
    "care_team_subject_reference_type",
    "care_team_encounter_reference_type",
    "care_team_participant_member_reference_type",
    "care_team_participant_on_behalf_of_reference_type",
    "care_team_reason_reference_type",
    "care_team_managing_organization_reference_type",
    "care_team_assigner_reference_type",
    "care_team_note_author_reference_type",
)

# Main-table columns that survive unchanged: the id, the audit/tenant columns and the subject /
# encounter index columns (their reference-type enums become plain strings).
_KEEP = {
    "id",
    "care_team_id",
    "tenant_id",
    "created_by",
    "updated_by",
    "created_at",
    "updated_at",
    "content",
    "period_start",
    "period_end",
    *(
        f"{ref}_{part}"
        for ref in ("subject", "encounter")
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

    # The subject / encounter types were enums; they are plain strings now.
    for column in ("subject_type", "encounter_type"):
        op.alter_column(
            P,
            column,
            type_=sa.String(),
            nullable=True,
            postgresql_using=f"{column}::text",
        )
    for name in _OLD_ENUMS:
        op.execute(f'DROP TYPE IF EXISTS "{name}"')
    # Care teams are searched by subject: one index on the pair instead of the lone id.
    op.execute(f"DROP INDEX IF EXISTS ix_{P}_subject_id")
    # The public id's sequence is now its server default.
    op.execute(
        f"ALTER TABLE {P} ALTER COLUMN care_team_id SET DEFAULT nextval('care_team_pub_seq')"
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
    op.execute(f"ALTER TABLE {P} DROP CONSTRAINT IF EXISTS care_team_care_team_id_key")
    for column in ("tenant_id", "created_at", "updated_at"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)

    # status: recreated as an enum holding the real FHIR codes.
    postgresql.ENUM(*_STATUS, name="care_team_status").create(bind, checkfirst=True)
    op.add_column(
        P,
        sa.Column(
            "status",
            postgresql.ENUM(*_STATUS, name="care_team_status", create_type=False),
            nullable=True,
        ),
    )
    op.create_index("ix_care_team_period", P, ["period_start", "period_end"])
    op.create_index("ix_care_team_subject_type_id", P, ["subject_type", "subject_id"])

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
    op.create_index("ix_care_team_token_param_code", f"{P}_token", ["param", "code"])

    op.create_table(
        f"{P}_participant",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        _fk(),
        sa.Column("reference_reference", sa.String(), nullable=True),
        sa.Column("reference_type", sa.String(), nullable=True),
        sa.Column("reference_id", sa.BigInteger(), nullable=True),
        sa.Column("reference_identifier_system", sa.String(), nullable=True),
        sa.Column("reference_identifier_value", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    _index(f"{P}_participant", f"{P}_pk")
    op.create_index(
        "ix_care_team_participant_type_id",
        f"{P}_participant",
        ["reference_type", "reference_id"],
    )

    _rebuild_index(bind)
    for column in ("id", "encounter_id", "status"):
        op.create_index(f"ix_{P}_{column}", P, [column], if_not_exists=True)
    op.alter_column(P, "content", nullable=False)


def downgrade() -> None:
    raise NotImplementedError(
        "care_team content/index migration is one-way: its old normalized tables are not "
        "rebuilt from `content`. Restore from a backup taken before upgrading."
    )
