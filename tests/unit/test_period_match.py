"""`period_match` — R4 date search against a Period target (a start column and
an end column), https://www.hl7.org/fhir/R4/search.html#date.

The target is the half-open range [start, end) a period covers; a NULL start
means "since forever" and a NULL end "still going"; a row with neither has no
period and never matches. The expected sets below are worked out by hand from
the R4 table (the engine's own `date_match` covers point-in-time targets).
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy import Column, DateTime, Integer, MetaData, Table, create_engine, select

from app.fhir.search.sql import period_match

metadata = MetaData()
roles = Table(
    "roles",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("period_start", DateTime(timezone=True), nullable=True),
    Column("period_end", DateTime(timezone=True), nullable=True),
)


def _utc(y, m, d):
    return datetime(y, m, d, tzinfo=UTC)


# id -> (start, end)  — end is the first instant AFTER the period.
ROWS = {
    1: (_utc(2026, 1, 1), _utc(2026, 7, 1)),  # A  Jan-Jun 2026
    2: (_utc(2026, 7, 1), _utc(2027, 1, 1)),  # B  Jul-Dec 2026
    3: (_utc(2026, 1, 1), None),  # C  from Jan 2026, still going
    4: (None, _utc(2026, 3, 1)),  # D  since forever, until Mar 2026
    5: (None, None),  # E  no period at all
}
A, B, C, D, E = 1, 2, 3, 4, 5


@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite://")
    metadata.create_all(eng)
    with eng.begin() as conn:
        conn.execute(
            roles.insert(),
            [
                {"id": i, "period_start": s, "period_end": e}
                for i, (s, e) in ROWS.items()
            ],
        )
    return eng


def _found(engine, value, now=None) -> set[int]:
    stmt = select(roles.c.id).where(
        period_match(roles.c.period_start, roles.c.period_end, value, now)
    )
    with engine.connect() as conn:
        return set(conn.execute(stmt).scalars())


@pytest.mark.parametrize(
    "value,expected",
    [
        # S = March 2026 = [2026-03-01, 2026-04-01)
        ("eq2026-03", set()),  # nothing sits wholly inside March
        ("2026-03", set()),  # no prefix means eq
        ("ne2026-03", {A, B, C, D}),  # not wholly inside; E has no period
        ("gt2026-03", {A, B, C}),  # the range above March meets them; D ended on 1 Mar
        ("lt2026-03", {A, C, D}),  # the range below March meets them; B starts in July
        ("ge2026-03", {A, B, C}),
        ("le2026-03", {A, C, D}),
        (
            "sa2026-03",
            {B},
        ),  # B starts after March; the open-start D can't be "entirely above"
        ("eb2026-03", {D}),  # D ended exactly at the start of March
        # S = the whole of 2026
        ("eq2026", {A, B}),  # open-ended periods are never wholly inside a range
        ("ne2026", {C, D}),
        ("sa2026", set()),
        ("eb2026", set()),
        ("gt2026", {C}),  # only the still-going period reaches past 2026
        ("lt2026", {D}),  # only the since-forever period reaches before 2026
        # S = a single day inside A
        ("eq2026-02-10", set()),
        ("ge2026-02-10", {A, B, C, D}),  # D runs until 1 Mar, so it reaches past 10 Feb
        ("le2026-02-10", {A, C, D}),
        # precision of the written value matters: a datetime is a one-second range
        (
            "ge2026-07-01T00:00:00Z",
            {B, C},
        ),  # A's end is the first instant after it: 07-01 not covered
        ("lt2026-07-01T00:00:00Z", {A, C, D}),
        (
            "gt2026-12-31T23:59:59Z",
            {C},
        ),  # B ends at 2027-01-01T00:00:00Z, so it is not "above" this second
    ],
)
def test_prefixes(engine, value, expected):
    assert _found(engine, value) == expected


def test_row_without_a_period_never_matches(engine):
    for value in (
        "eq2026",
        "ne2026",
        "gt2000",
        "lt2100",
        "ge2000",
        "le2100",
        "sa2000",
        "eb2100",
    ):
        assert E not in _found(engine, value), value


def test_approximately_widens_the_range_by_ten_percent_of_its_distance_from_now(engine):
    # S = March 2026; "now" is 14 days after its start, so the range widens by 1.4 days each side.
    now = datetime(2026, 3, 15, tzinfo=UTC)
    assert _found(engine, "ap2026-03", now) == {
        A,
        C,
        D,
    }  # B (starts in July) is far outside
    # Far in the future, "approximately" widens a lot and reaches B too.
    assert _found(engine, "ap2026-03", datetime(2036, 3, 15, tzinfo=UTC)) == {
        A,
        B,
        C,
        D,
    }


def test_bad_date_is_rejected(engine):
    from app.fhir.search import SearchError

    with pytest.raises(SearchError):
        period_match(roles.c.period_start, roles.c.period_end, "not-a-date")
