"""
Parsing of individual FHIR R4 search *values* — escaping, string
normalization, token / date / reference syntax
(https://www.hl7.org/fhir/R4/search.html). Pure Python, no SQL: the
condition builders in app.fhir.search.sql consume what these return.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone

from .errors import SearchError

# ── Escaping (R4 §2.21.1.8 "Escaping Search Parameters") ─────────────────────
# `,` separates OR values, `|` separates token/quantity parts and `$`
# separates composite parts; a literal one is written `\,` `\|` `\$`, and a
# literal backslash `\\`.


def split_escaped(value: str, separator: str) -> list[str]:
    """Split on every *unescaped* `separator`. Escape sequences are kept
    as-is in the parts (unescape each part with `unescape()` once it has
    been split on everything it needs to be)."""
    parts, current, i = [], [], 0
    while i < len(value):
        ch = value[i]
        if ch == "\\" and i + 1 < len(value):
            current.append(value[i : i + 2])
            i += 2
            continue
        if ch == separator:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
        i += 1
    parts.append("".join(current))
    return parts


def unescape(value: str) -> str:
    return re.sub(r"\\(.)", r"\1", value)


# ── String normalization ─────────────────────────────────────────────────────
# R4 string search is "case-insensitive and accent-insensitive": both the
# stored value and the query are normalized the same way before comparing.
# Done in Python (not with a DB function such as unaccent()) so it behaves
# identically on Postgres and the SQLite test database, and so the stored,
# pre-normalized column can carry a plain btree prefix index.


def normalize(text: str | None) -> str | None:
    """Strip accents (NFKD + drop combining marks) and case-fold."""
    if text is None:
        return None
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def like_escape(value: str) -> str:
    """Escape LIKE wildcards; use with `ESCAPE '\\'`."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


# ── Token ────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Token:
    """One token search value. `system` is None when no `|` was given
    (any system), "" for `|code` (no system), and the system otherwise;
    `code` is None for `system|` (any code in the system)."""

    system: str | None
    code: str | None


def parse_token(value: str) -> Token:
    parts = split_escaped(value, "|")
    if len(parts) == 1:
        return Token(system=None, code=unescape(parts[0]))
    if len(parts) == 2:
        system, code = (unescape(p) for p in parts)
        return Token(system=system, code=code or None)
    raise SearchError(value, f"Invalid token '{value}': expected [system|]code.")


def parse_of_type(value: str) -> tuple[str, str, str]:
    """`identifier:of-type` value: `type-system|type-code|value`, all three
    required (R4 §2.21.1.4.4)."""
    parts = [unescape(p) for p in split_escaped(value, "|")]
    if len(parts) != 3 or not all(parts):
        raise SearchError(
            value,
            f"Invalid :of-type value '{value}': expected system|code|value, all three present.",
        )
    return parts[0], parts[1], parts[2]


# ── Date ─────────────────────────────────────────────────────────────────────

DATE_PREFIXES = ("eq", "ne", "gt", "lt", "ge", "le", "sa", "eb", "ap")

_DATE_RE = re.compile(
    r"^(?P<y>\d{4})(?:-(?P<m>\d{2})(?:-(?P<d>\d{2})"
    r"(?:T(?P<H>\d{2}):(?P<M>\d{2})(?::(?P<S>\d{2})(?P<f>\.\d+)?)?"
    r"(?P<tz>Z|[+-]\d{2}:\d{2})?)?)?)?$"
)


@dataclass(frozen=True)
class DateValue:
    """A date search value as the half-open range it denotes: a value is
    only as precise as written, so `2024-03` means [2024-03-01, 2024-04-01)."""

    prefix: str
    low: datetime
    high: datetime


def _add_month(dt: datetime, months: int) -> datetime:
    month = dt.month - 1 + months
    return dt.replace(year=dt.year + month // 12, month=month % 12 + 1)


def parse_date(value: str) -> DateValue:
    prefix, rest = "eq", value
    if len(value) > 2 and value[:2] in DATE_PREFIXES and value[2].isdigit():
        prefix, rest = value[:2], value[2:]
    match = _DATE_RE.match(rest)
    if not match:
        raise SearchError(
            value,
            f"Invalid date '{value}': expected [prefix]YYYY[-MM[-DD[Thh:mm[:ss[.fff]][Z|±hh:mm]]]] "
            f"with an optional prefix ({', '.join(DATE_PREFIXES)}).",
        )
    g = match.groupdict()
    tz = UTC
    if g["tz"] and g["tz"] != "Z":
        sign = 1 if g["tz"][0] == "+" else -1
        hours, minutes = int(g["tz"][1:3]), int(g["tz"][4:6])
        tz = timezone(sign * timedelta(hours=hours, minutes=minutes))
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
    except ValueError as exc:
        raise SearchError(value, f"Invalid date '{value}': {exc}.") from exc
    if g["f"]:
        high = low + timedelta(microseconds=1)
    elif g["S"]:
        high = low + timedelta(seconds=1)
    elif g["M"]:
        high = low + timedelta(minutes=1)
    elif g["d"]:
        high = low + timedelta(days=1)
    elif g["m"]:
        high = _add_month(low, 1)
    else:
        high = low.replace(year=low.year + 1)
    return DateValue(prefix, low.astimezone(UTC), high.astimezone(UTC))


# ── Reference ────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class ReferenceValue:
    """A reference search value, resolved: either a local resource
    (`resource_type`/`resource_id`, the public id) or an absolute URL this
    server doesn't own (`url`). `resource_type` is None for a bare id whose
    type the caller didn't pin."""

    resource_type: str | None = None
    resource_id: str | None = None
    url: str | None = None


_HISTORY = re.compile(r"/_history/[^/]+$")
_LOCAL = re.compile(r"^(?:(?P<type>[A-Z][A-Za-z]+)/)?(?P<id>[A-Za-z0-9\-.]{1,64})$")


def parse_reference_value(value: str, fhir_base: str | None) -> ReferenceValue:
    """`[id]`, `[type]/[id]` or an absolute `[url]` (R4 §2.21.1.4.5). An
    absolute URL under this server's own base is treated as the local
    reference it denotes, so relative and absolute forms match alike. A
    version suffix (`/_history/x`) is ignored."""
    v = _HISTORY.sub("", unescape(value))
    if re.match(r"^[a-z][a-z0-9+.\-]*:", v):
        if fhir_base and v.startswith(fhir_base.rstrip("/") + "/"):
            local = v[len(fhir_base.rstrip("/")) + 1 :]
            m = re.match(r"^(?P<type>[A-Za-z]+)/(?P<id>[A-Za-z0-9\-.]{1,64})$", local)
            if m:
                return ReferenceValue(_resource_type(m["type"]), m["id"])
        return ReferenceValue(url=v)
    m = _LOCAL.match(v)
    if not m:
        raise SearchError(value, f"Invalid reference '{value}': expected [type/]id or an absolute URL.")
    return ReferenceValue(m["type"], m["id"])


def _resource_type(segment: str) -> str:
    """This server's own URLs use lower-case plural paths
    (`/organizations/1`, `/healthcare-services/1`); map one back to its
    FHIR type name."""
    if segment[:1].isupper():
        return segment
    singular = segment[:-1] if segment.endswith("s") else segment
    return "".join(part.capitalize() for part in singular.split("-"))
