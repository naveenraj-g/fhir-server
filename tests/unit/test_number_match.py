"""`number_range_match` — R4 `number` search (https://www.hl7.org/fhir/R4/search.html#number)
over an element held as a lower and an upper bound: a decimal is a point (low == high), a
Range has two bounds, either of which may be open (NULL).

`[prefix]number`: the number is matched at the precision written (`0.5` is [0.45, 0.55),
`5` is [4.5, 5.5)), the comparison prefixes ignore that precision, a row with no number never
matches, and a number takes no unit. The expected sets are worked out by hand from the R4 text
(the same range semantics `quantity_range_match` applies).
"""

import pytest
from sqlalchemy import Column, Integer, MetaData, Numeric, Table, create_engine, select

from app.fhir.search.errors import SearchError
from app.fhir.search.quantity import number_range_match

metadata = MetaData()
probabilities = Table(
    "probabilities",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("low", Numeric, nullable=True),
    Column("high", Numeric, nullable=True),
)

# id -> (low, high); None = open on that side. A decimal is a point.
ROWS = {
    1: (0.5, 0.5),  # probabilityDecimal 0.5
    2: (0.2, 0.4),  # probabilityRange 0.2 - 0.4
    3: (0.7, None),  # open above
    4: (None, 0.1),  # open below
    5: (None, None),  # no probability at all
    6: (10, 10),  # a percentage-sized decimal
}


@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite://")
    metadata.create_all(eng)
    with eng.begin() as conn:
        conn.execute(
            probabilities.insert(),
            [{"id": i, "low": lo, "high": hi} for i, (lo, hi) in ROWS.items()],
        )
    return eng


def _match(engine, value: str) -> set[int]:
    c = probabilities.c
    with engine.connect() as conn:
        return {
            r[0]
            for r in conn.execute(
                select(c.id).where(number_range_match(c.low, c.high, value))
            )
        }


@pytest.mark.parametrize(
    "value,expected",
    [
        ("0.5", {1}),  # [0.45, 0.55) wholly contains only the point 0.5
        ("0.3", set()),  # [0.25, 0.35) wholly contains no target
        ("1", {1}),  # [0.5, 1.5) wholly contains the point 0.5
        ("1e1", {6}),  # [5, 15) wholly contains the point 10
        (
            "ne0.5",
            {2, 3, 4, 6},
        ),  # not wholly contained; an open end is never contained; row 5 has no number
        ("gt0.6", {3, 6}),  # the range above 0.6 overlaps the open-above one and 10
        (
            "lt0.3",
            {2, 4},
        ),  # the range below 0.3 overlaps 0.2-0.4 and the open-below one
        ("ge0.5", {1, 3, 6}),
        ("le0.2", {2, 4}),
        ("sa0.5", {3, 6}),  # starts after [0.45, 0.55): low >= 0.55
        ("eb0.5", {2, 4}),  # ends before it: high < 0.45
        ("ap0.5", {1}),  # overlaps [0.45, 0.55]
    ],
)
def test_prefixes(engine, value, expected):
    assert _match(engine, value) == expected


def test_a_row_with_no_number_never_matches(engine):
    for value in ("0.5", "gt0", "lt1", "ne0.5", "ge0", "le1", "ap0.5"):
        assert 5 not in _match(engine, value), value


@pytest.mark.parametrize(
    "bad", ["abc", "", "0.5|http://unitsofmeasure.org|%", "gt", "1|2"]
)
def test_bad_values_are_search_errors(bad):
    with pytest.raises(SearchError):
        number_range_match(probabilities.c.low, probabilities.c.high, bad)
