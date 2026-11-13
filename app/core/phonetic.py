"""
Phonetic keys for FHIR `phonetic` string search parameters
(e.g. Organization `phonetic`: "A portion of the organization's name using
some kind of phonetic matching algorithm" — the algorithm is server-defined).

This server uses American Soundex, computed in Python (not Postgres'
fuzzystrmatch extension) so it behaves identically on the SQLite test
database. A name's key is the Soundex code of each of its words,
space-padded (" G564 H213 "), so the search side can match one word's code
as a whole token with a plain `LIKE '% G564 %'`.
"""

from __future__ import annotations

import re

_CODES = {
    **dict.fromkeys("BFPV", "1"),
    **dict.fromkeys("CGJKQSXZ", "2"),
    **dict.fromkeys("DT", "3"),
    "L": "4",
    **dict.fromkeys("MN", "5"),
    "R": "6",
}


def soundex(word: str) -> str | None:
    """American Soundex (letter + 3 digits) of one word; None if the word
    has no ASCII letters."""
    letters = re.sub(r"[^A-Z]", "", word.upper())
    if not letters:
        return None
    first = letters[0]
    digits: list[str] = []
    prev = _CODES.get(first, "")
    for ch in letters[1:]:
        code = _CODES.get(ch, "")
        if code and code != prev:
            digits.append(code)
        # H and W don't separate letters with the same code; vowels do.
        if ch not in "HW":
            prev = code
    return (first + "".join(digits) + "000")[:4]


def phonetic_codes(text: str | None) -> list[str]:
    """Soundex code of each word in `text`, in order, without duplicates."""
    codes: list[str] = []
    for word in re.split(r"\s+", text or ""):
        code = soundex(word)
        if code and code not in codes:
            codes.append(code)
    return codes


def phonetic_key(text: str | None) -> str | None:
    """Stored form: space-padded codes (" G564 H213 "), or None."""
    codes = phonetic_codes(text)
    return f" {' '.join(codes)} " if codes else None
