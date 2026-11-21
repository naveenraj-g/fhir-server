"""`parse_quantity` / `quantity_match` — R4 quantity search,
https://www.hl7.org/fhir/R4/search.html#quantity.

`[prefix]number[|system|code]`: the number is matched at the precision written
(`5` is [4.5, 5.5), `5.00` is [4.995, 5.005)), the comparison prefixes ignore
that precision, and the unit is optional — `||code` also matches the human
`unit` text, a system pins the code precisely. The expected sets are worked out
by hand from the R4 text.
"""

from decimal import Decimal

import pytest
from sqlalchemy import (
    Column,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    create_engine,
    select,
)

from app.fhir.search.errors import SearchError
from app.fhir.search.quantity import (
    parse_quantity,
    quantity_match,
    quantity_range_match,
)

UCUM = "http://unitsofmeasure.org"

metadata = MetaData()
lengths = Table(
    "lengths",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("value", Numeric, nullable=True),
    Column("system", String, nullable=True),
    Column("code", String, nullable=True),
    Column("unit", String, nullable=True),
)

# id -> (value, system, code, unit)
ROWS = {
    1: (2, UCUM, "d", "d"),
    2: (5, UCUM, "d", "days"),
    3: (5.5, UCUM, "d", "days"),
    4: (90, UCUM, "min", "min"),
    5: (5, None, None, "week"),  # a Quantity with only a human unit
    6: (None, None, None, None),  # no length at all
}


@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite://")
    metadata.create_all(eng)
    with eng.begin() as conn:
        conn.execute(
            lengths.insert(),
            [
                {"id": i, "value": v, "system": s, "code": c, "unit": u}
                for i, (v, s, c, u) in ROWS.items()
            ],
        )
    return eng


def _match(engine, value: str) -> set[int]:
    cond = quantity_match(
        lengths.c.value, lengths.c.system, lengths.c.code, lengths.c.unit, value
    )
    with engine.connect() as conn:
        return {r[0] for r in conn.execute(select(lengths.c.id).where(cond))}


@pytest.mark.parametrize(
    "value,expected",
    [
        ("5", {2, 5}),  # [4.5, 5.5): 5.5 itself is outside
        ("5.5", {3}),  # [5.45, 5.55)
        ("5.0", {2, 5}),  # [4.95, 5.05)
        ("2", {1}),
        ("eq2", {1}),
        ("1e2", {4}),  # [50, 150)
        ("ne5", {1, 3, 4}),  # rows with no value never match
        ("gt5", {3, 4}),  # precision ignored: strictly above 5
        ("ge5", {2, 3, 4, 5}),
        ("lt5", {1}),
        ("le5", {1, 2, 5}),
        ("sa5", {3, 4}),  # starts after the range [4.5, 5.5)
        ("eb5", {1}),  # ends before it
        ("ap5", {2, 3, 5}),  # within 10%: [4.5, 5.5]
        ("-1", set()),
    ],
)
def test_number_and_prefix(engine, value, expected):
    assert _match(engine, value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        (f"5|{UCUM}|d", {2}),  # system + code, precisely
        (f"5|{UCUM}|", {2}),  # system only
        (f"gt1|{UCUM}|min", {4}),
        ("5||d", {2}),  # code without a system: code...
        ("5||days", {2}),  # ...or the human unit
        ("5||week", {5}),
        ("5|http://wrong|d", set()),
        (f"5|{UCUM}|min", set()),
        ("5||", {2, 5}),  # no unit constraint
        ("5|", {2, 5}),
    ],
)
def test_units(engine, value, expected):
    assert _match(engine, value) == expected


def test_parse_quantity_range_follows_the_written_precision():
    _, number, low, high, system, code, _ = parse_quantity("5|s|c")
    assert (number, low, high, system, code) == (
        Decimal(5),
        Decimal("4.5"),
        Decimal("5.5"),
        "s",
        "c",
    )
    _, _, low, high, *_ = parse_quantity("5.00")
    assert (low, high) == (Decimal("4.995"), Decimal("5.005"))
    _, _, low, high, *_ = parse_quantity("1e2")
    assert (low, high) == (Decimal(50), Decimal(150))


@pytest.mark.parametrize(
    "bad", ["", "abc", "gt", "5e", "NaN", "Infinity", "1|2|3|4", "gtx5"]
)
def test_bad_values_are_search_errors(bad):
    with pytest.raises(SearchError):
        parse_quantity(bad)


# ── quantity_range_match: an Age (a point) or a Range held as low / high bounds ──
# id -> (low, high, system, code, unit); None = open on that side.
SPANS = {
    1: (12, 12, UCUM, "a", "years"),  # an Age: low == high
    2: (5, 10, UCUM, "a", "years"),
    3: (20, None, UCUM, "a", "years"),  # open above
    4: (None, 8, UCUM, "a", "years"),  # open below
    5: (None, None, None, None, None),  # no quantity at all
    6: (12, 30, UCUM, "mo", "months"),
}
spans = Table(
    "spans",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("low", Numeric, nullable=True),
    Column("high", Numeric, nullable=True),
    Column("system", String, nullable=True),
    Column("code", String, nullable=True),
    Column("unit", String, nullable=True),
)


@pytest.fixture(scope="module")
def span_engine():
    eng = create_engine("sqlite://")
    metadata.create_all(eng)
    with eng.begin() as conn:
        conn.execute(
            spans.insert(),
            [
                {"id": i, "low": lo, "high": hi, "system": s, "code": c, "unit": u}
                for i, (lo, hi, s, c, u) in SPANS.items()
            ],
        )
    return eng


def _span_match(engine, value: str) -> set[int]:
    c = spans.c
    cond = quantity_range_match(c.low, c.high, c.system, c.code, c.unit, value)
    with engine.connect() as conn:
        return {r[0] for r in conn.execute(select(c.id).where(cond))}


@pytest.mark.parametrize(
    "value,expected",
    [
        ("12", {1}),  # [11.5, 12.5) wholly contains only the point 12
        ("1e1", {1, 2}),  # [5, 15) wholly contains the point 12 and the range 5-10
        ("10", set()),  # [9.5, 10.5) contains no target range
        (
            "ne12",
            {2, 3, 4, 6},
        ),  # not wholly contained; an open end is never contained; row 5 has no quantity
        (
            "gt15",
            {3, 6},
        ),  # the range above 15 overlaps an open-ended and a 12-30 target
        ("lt6", {2, 4}),  # the range below 6 overlaps 5-10 and the open-below one
        ("ge10", {1, 2, 3, 6}),
        ("le8", {2, 4}),
        ("sa10", {1, 3, 6}),  # starts after [9.5, 10.5): low >= 10.5
        ("eb10", {4}),  # ends before it: high < 9.5
        ("ap10", {2}),  # overlaps [9, 11]
    ],
)
def test_range_prefixes(span_engine, value, expected):
    assert _span_match(span_engine, value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        (f"12|{UCUM}|a", {1}),
        (f"gt1|{UCUM}|mo", {6}),
        ("gt1||years", {1, 2, 3, 4}),  # code or the human unit, no system
        ("gt1||months", {6}),
        (f"12|{UCUM}|mo", set()),
        ("12|http://wrong|a", set()),
    ],
)
def test_range_units(span_engine, value, expected):
    assert _span_match(span_engine, value) == expected


def test_range_bad_values_are_search_errors():
    with pytest.raises(SearchError):
        quantity_range_match(
            spans.c.low, spans.c.high, spans.c.system, spans.c.code, spans.c.unit, "abc"
        )
