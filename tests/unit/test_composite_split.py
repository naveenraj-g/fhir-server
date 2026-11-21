"""`split_composite` — the `$`-separated parts of an R4 `composite` search value
(https://www.hl7.org/fhir/R4/search.html#composite).

Only the splitting and its validation live in the engine (what each part means is the
resource's own SQL, tested through Observation's composite searches): exactly the expected
number of non-empty parts, `\\$` is a literal `$` inside a part, and the parts come back still
escaped so each can be parsed by the parser of its own component type.
"""

import pytest

from app.fhir.search.composite import split_composite
from app.fhir.search.errors import SearchError


def test_splits_two_parts():
    assert split_composite(
        "http://loinc.org|8480-6$gt100|http://unitsofmeasure.org|mm[Hg]", 2
    ) == [
        "http://loinc.org|8480-6",
        "gt100|http://unitsofmeasure.org|mm[Hg]",
    ]


def test_a_part_keeps_its_own_pipes():
    assert split_composite("a|b$c|d|e", 2) == ["a|b", "c|d|e"]


def test_an_escaped_dollar_is_not_a_separator_and_stays_escaped():
    assert split_composite("a\\$b$c", 2) == ["a\\$b", "c"]


def test_three_parts():
    assert split_composite("a$b$c", 3) == ["a", "b", "c"]


@pytest.mark.parametrize("value", ["a", "a$b$c", "a$", "$b", "$", ""])
def test_wrong_number_of_parts_or_an_empty_part_is_rejected(value):
    with pytest.raises(SearchError):
        split_composite(value, 2)
