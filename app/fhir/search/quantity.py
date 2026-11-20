"""
FHIR R4 `quantity` search (https://www.hl7.org/fhir/R4/search.html#quantity):
`[parameter]=[prefix][number]|[system]|[code]`.

The number is matched at the precision written — `5` is the range [4.5, 5.5),
`5.00` is [4.995, 5.005) — the same implicit-range rule as a `number`
parameter; `gt`, `lt`, `ge`, `le`, `sa` and `eb` ignore that precision. The
unit is optional: with a `system` and/or `code` both must match (a canonical,
precise match); with only `||code`, the code may be the Quantity's `code` *or*
its human `unit`. Units are compared as written — no UCUM conversion (R4 lets a
server choose; this one doesn't), so `length=2||d` does not find a length
stored in hours.

A Quantity is stored as four index columns (value, system, code, unit);
`quantity_match()` builds the SQL over them.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from sqlalchemy import and_, or_

from .errors import SearchError
from .values import split_escaped, unescape

QUANTITY_PREFIXES = ("eq", "ne", "gt", "lt", "ge", "le", "sa", "eb", "ap")


def parse_quantity(value: str) -> tuple[str, Decimal, Decimal, Decimal, str | None, str | None, bool]:
    """(prefix, number, low, high, system, code, unit_part_given) for one search
    value. `low`/`high` bound the implicit range ([low, high)); `unit_part_given`
    is whether the value had a `|` at all."""
    parts = split_escaped(value, "|")
    if len(parts) > 3:
        raise SearchError(value, f"Invalid quantity '{value}': expected [prefix]number[|system|code].")
    number_text = unescape(parts[0]).strip()
    prefix = "eq"
    if len(number_text) > 2 and number_text[:2] in QUANTITY_PREFIXES and (number_text[2].isdigit() or number_text[2] in "+-."):
        prefix, number_text = number_text[:2], number_text[2:]
    try:
        number = Decimal(number_text)
        if not number.is_finite():
            raise InvalidOperation
    except InvalidOperation as exc:
        raise SearchError(value, f"Invalid quantity '{value}': '{number_text}' is not a number.") from exc
    # Half a unit of the last written digit: 5 -> 0.5, 5.00 -> 0.005, 1e2 -> 50.
    half = Decimal(5).scaleb(number.as_tuple().exponent - 1)
    system = unescape(parts[1]) if len(parts) > 1 and parts[1] != "" else None
    code = unescape(parts[2]) if len(parts) > 2 and parts[2] != "" else None
    return prefix, number, number - half, number + half, system, code, len(parts) > 1


def quantity_match(value_col, system_col, code_col, unit_col, value: str):
    """A Quantity held as (value, system, code, unit) columns against one
    search value. For a single stored value v (the Quantity's own range is
    ignored — R4 stores a point):

      eq  low <= v < high          ne  not eq
      gt  v > n    lt  v < n       ge  v >= n   le  v <= n
      sa  v >= high                eb  v < low
      ap  within 10% of n
    """
    prefix, n, low, high, system, code, _ = parse_quantity(value)
    # Compared as floats: the columns are Numeric, and a float bind works on
    # both PostgreSQL and the SQLite test database.
    n, low, high = float(n), float(low), float(high)
    if prefix == "eq":
        number = and_(value_col >= low, value_col < high)
    elif prefix == "ne":
        number = or_(value_col < low, value_col >= high)
    elif prefix == "gt":
        number = value_col > n
    elif prefix == "lt":
        number = value_col < n
    elif prefix == "ge":
        number = value_col >= n
    elif prefix == "le":
        number = value_col <= n
    elif prefix == "sa":
        number = value_col >= high
    elif prefix == "eb":
        number = value_col < low
    else:  # ap
        slack = abs(n) * 0.1
        number = and_(value_col >= n - slack, value_col <= n + slack)

    conditions = [number]
    if system is not None:
        conditions.append(system_col == system)
    if code is not None:
        # `||mg` (no system): the code or the human-readable unit; with a
        # system the code is the Quantity's code, precisely.
        conditions.append(code_col == code if system is not None else or_(code_col == code, unit_col == code))
    return and_(*conditions)
