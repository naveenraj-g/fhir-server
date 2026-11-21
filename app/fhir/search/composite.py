"""
FHIR R4 `composite` search (https://www.hl7.org/fhir/R4/search.html#composite): a parameter
whose value is several single-parameter values joined by `$`, e.g.

    Observation?code-value-quantity=http://loinc.org|8480-6$gt100|http://unitsofmeasure.org|mm[Hg]

meaning "an element whose code is 8480-6 *and* whose value is a quantity above 100 mm[Hg]" — both
conditions on the *same* element, which is the point of a composite: `code=...&value-quantity=...`
would be satisfied by one component's code and another component's value.

This module only splits and validates the `$`-separated parts; what each part means is the
resource's own SQL (a registry declares a composite as a `SearchParam` with `type="composite"`,
no modifiers, and a `match` builder that pairs the parts — see
app.repository.observation.search). `,` still separates OR alternatives (handled by the parser
before the builder sees the value) and a literal `$` inside a part is written `\\$`.
"""

from __future__ import annotations

from .errors import SearchError
from .values import split_escaped


def split_composite(value: str, parts: int) -> list[str]:
    """The `parts` `$`-separated pieces of one composite search value, still escaped (each
    piece is parsed by the parser of its own component type, which unescapes it). Raises
    SearchError (400) when the value does not have exactly that many non-empty pieces."""
    pieces = split_escaped(value, "$")
    if len(pieces) != parts or any(p == "" for p in pieces):
        raise SearchError(
            value,
            f"Invalid composite value '{value}': expected {parts} non-empty parts separated by '$'.",
        )
    return pieces
