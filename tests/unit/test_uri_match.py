"""`uri_match` — R4 `uri` search, https://www.hl7.org/fhir/R4/search.html#uri.

A uri is compared as a whole string, case-sensitively. `:below` matches stored URIs
that start with the value, `:above` stored URIs that are a prefix of the value.
The expected sets are worked out by hand from the R4 text.
"""

import pytest
from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine, select

from app.fhir.search.sql import uri_match

metadata = MetaData()
uris = Table("uris", metadata, Column("id", Integer, primary_key=True), Column("uri", String, nullable=False))

ROWS = {
    1: "http://example.org/protocols/knee",
    2: "http://example.org/protocols/knee/step1",
    3: "http://example.org/protocols",
    4: "http://example.org/Protocols/knee",
    5: "http://other.org/x",
    6: "urn:oid:1.2.3",
    7: "http://example.org/100%_done",
}


@pytest.fixture(scope="module")
def engine():
    eng = create_engine("sqlite://")
    metadata.create_all(eng)
    with eng.begin() as conn:
        conn.execute(uris.insert(), [{"id": i, "uri": u} for i, u in ROWS.items()])
    return eng


def _match(engine, value: str, modifier: str | None = None) -> set[int]:
    with engine.connect() as conn:
        return {r[0] for r in conn.execute(select(uris.c.id).where(uri_match(uris.c.uri, value, modifier)))}


@pytest.mark.parametrize(
    "value,modifier,expected",
    [
        ("http://example.org/protocols/knee", None, {1}),  # exact: not a prefix of row 2
        ("http://example.org/protocols/Knee", None, set()),  # case-sensitive
        ("http://example.org/Protocols/knee", None, {4}),
        ("urn:oid:1.2.3", None, {6}),
        ("http://example.org/protocols", "below", {1, 2, 3}),  # starts with the value
        ("http://example.org/protocols/knee", "below", {1, 2}),
        ("http://other.org", "below", {5}),
        ("http://nothing", "below", set()),
        ("http://example.org/protocols/knee/step1/detail", "above", {1, 2, 3}),  # stored is a prefix of the value
        ("http://example.org/protocols/knee", "above", {1, 3}),
        ("http://example.org/protocols", "above", {3}),
        ("http://example.org/100%_done", None, {7}),  # LIKE wildcards in the data are not wildcards
        ("http://example.org/100%", "below", {7}),
        ("http://example.org/1%", "below", set()),  # ...nor in the search value
        ("http://example.org/100%_done/more", "above", {7}),
    ],
)
def test_uri_match(engine, value, modifier, expected):
    assert _match(engine, value, modifier) == expected
