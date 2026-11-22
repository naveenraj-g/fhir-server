"""required-binding `code` search parameters held as Postgres enums: AllergyIntolerance, Appointment

Revision ID: a1d7e4f0b826
Revises: f9e4a1c7d583
Create Date: 2026-12-15 12:00:00.000000

A `code` element with a *required* binding is a closed list HL7 defines completely and no profile can
extend, so when a search parameter reads one it is held as a Postgres enum (the same rule as every
`status`). Auditing every rebuilt resource against HL7's R4 definitions found three that were not:

  AllergyIntolerance.category (0..*)           -> allergy_intolerance.category, an array of the enum
                                                  `allergy_intolerance_category` (was token rows)
  AllergyIntolerance.reaction.severity (0..1)  -> allergy_intolerance_reaction.severity, the enum
                                                  `allergy_intolerance_reaction_severity` (was token rows)
  Appointment.participant.status (1..1)        -> appointment_participant.status, the enum
                                                  `appointment_participant_status` (was a string)

upgrade: creates the types and columns, fills them from `content` (the allergy reaction rows are
rebuilt: they now exist for a reaction with an onset *or* a severity), deletes the now-unused
`category` / `severity` rows of `allergy_intolerance_token`, and casts the appointment participant
status (a value outside the four codes - the validator rejects those - becomes NULL).

downgrade: not supported (one-way, like the other content-based migrations).
"""

import json
import re
from datetime import UTC, datetime, timedelta, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "a1d7e4f0b826"
down_revision: Union[str, None] = "f9e4a1c7d583"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CATEGORY = ("food", "medication", "environment", "biologic")
_SEVERITY = ("mild", "moderate", "severe")
_PARTICIPANT_STATUS = ("accepted", "declined", "tentative", "needs-action")

_DATE_RE = re.compile(
    r"^(?P<y>\d{4})(?:-(?P<m>\d{2})(?:-(?P<d>\d{2})(?:T(?P<H>\d{2}):(?P<M>\d{2})"
    r"(?::(?P<S>\d{2})(?P<f>\.\d+)?)?(?P<tz>Z|[+-]\d{2}:\d{2})?)?)?)?$"
)


def _bounds(value):
    """(start, end) instants of a FHIR date/dateTime at its written precision - the half-open range
    it covers (frozen copy of app.fhir.search.values.parse_date). (None, None) if absent or
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


def _json(value):
    return json.loads(value) if isinstance(value, str) else value


def _enum(name, values):
    return postgresql.ENUM(*values, name=name, create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    for name, values in (
        ("allergy_intolerance_category", _CATEGORY),
        ("allergy_intolerance_reaction_severity", _SEVERITY),
        ("appointment_participant_status", _PARTICIPANT_STATUS),
    ):
        postgresql.ENUM(*values, name=name).create(bind, checkfirst=True)

    # -- Appointment.participant.status: string -> enum --------------------------------------
    codes = ", ".join(f"'{c}'" for c in _PARTICIPANT_STATUS)
    op.execute(
        "ALTER TABLE appointment_participant ALTER COLUMN status TYPE appointment_participant_status "
        f"USING (CASE WHEN status IN ({codes}) THEN status::appointment_participant_status END)"
    )

    # -- AllergyIntolerance.category and .reaction.severity ------------------------------------
    op.add_column(
        "allergy_intolerance",
        sa.Column(
            "category",
            postgresql.ARRAY(_enum("allergy_intolerance_category", _CATEGORY)),
            nullable=True,
        ),
    )
    op.add_column(
        "allergy_intolerance_reaction",
        sa.Column(
            "severity",
            _enum("allergy_intolerance_reaction_severity", _SEVERITY),
            nullable=True,
        ),
    )
    categories = ", ".join(f"'{c}'" for c in _CATEGORY)
    op.execute(
        "UPDATE allergy_intolerance SET category = NULLIF(ARRAY("
        "SELECT c::allergy_intolerance_category FROM jsonb_array_elements_text("
        "COALESCE(content->'category', '[]'::jsonb)) AS c "
        f"WHERE c IN ({categories})), '{{}}')"
    )
    # reaction rows: one per reaction with an onset or a severity (they only held the onset before)
    op.execute("DELETE FROM allergy_intolerance_reaction")
    for row in bind.execute(
        sa.text("SELECT id, content FROM allergy_intolerance")
    ).mappings():
        for reaction in _json(row["content"]).get("reaction") or []:
            start, end = _bounds(reaction.get("onset"))
            severity = reaction.get("severity")
            severity = severity if severity in _SEVERITY else None
            if start or end or severity:
                bind.execute(
                    sa.text(
                        "INSERT INTO allergy_intolerance_reaction "
                        "(allergy_intolerance_pk, onset_start, onset_end, severity) VALUES "
                        "(:pk, :s, :e, CAST(:sev AS allergy_intolerance_reaction_severity))"
                    ),
                    {"pk": row["id"], "s": start, "e": end, "sev": severity},
                )
    op.execute(
        "DELETE FROM allergy_intolerance_token WHERE param IN ('category', 'severity')"
    )


def downgrade() -> None:
    raise NotImplementedError(
        "required-code enum migration is one-way: the token rows and the string column are not "
        "rebuilt. Restore from a backup taken before upgrading."
    )
