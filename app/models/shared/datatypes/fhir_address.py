"""Shared FHIR `Address` datatype columns, reusable across every table that
embeds exactly one Address — either a dedicated table (organization_address)
or a prefixed group of columns living alongside unrelated fields on a bigger
table (organization_contact's `address_*` columns, next to its `purpose_*`
and `name_*` groups).

Set `_address_prefix` on the concrete class to control the underlying DB
column names (defaults to no prefix, for a dedicated table). The Python-side
attribute names stay fixed (`use`, `city`, etc.) regardless of the prefix —
e.g. OrganizationContact sets `_address_prefix = "address_"` so the DB
columns stay `address_city`/`address_use` (matching its other prefixed
groups), while still giving you `contact.city`/`contact.use` in Python.

Only supports ONE Address usage per class — if a table ever needed two
Address groups at once, this mixin couldn't be used twice (a class can't
have two different `_address_prefix` values); a
`sqlalchemy.orm.composite()` mapping would be the right tool for that case
instead. No table in this resource needs that today.

`Fhir` prefix (file and class) marks this as a FHIR-datatype mixin
specifically — distinct from TenantAuditMixin, which is tenant/audit
infrastructure, not a FHIR datatype, and deliberately doesn't get this
prefix.
"""

from sqlalchemy import Column, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import declared_attr

from app.schemas.enums import AddressType, AddressUse


class FhirAddressMixin:
    """Mix into any declarative model whose row (or a prefixed slice of its
    row) represents one Address. No `-> Column` return-type annotations
    here, deliberately — see TenantAuditMixin's docstring for why
    (SQLAlchemy 2.0's MappedAnnotationError)."""

    _address_prefix = ""

    @declared_attr
    def use(cls):
        # 0..1 on Address — not required even here.
        return Column(
            f"{cls._address_prefix}use", Enum(AddressUse, name="address_use"), nullable=True
        )

    @declared_attr
    def type(cls):
        return Column(
            f"{cls._address_prefix}type", Enum(AddressType, name="address_type"), nullable=True
        )

    @declared_attr
    def text(cls):
        return Column(f"{cls._address_prefix}text", String, nullable=True)

    @declared_attr
    def line(cls):
        # 0..* string — a real Postgres array, not comma-separated text
        # (which loses structure and breaks on values containing commas).
        return Column(f"{cls._address_prefix}line", ARRAY(String), nullable=True)

    @declared_attr
    def city(cls):
        return Column(f"{cls._address_prefix}city", String, nullable=True)

    @declared_attr
    def district(cls):
        return Column(f"{cls._address_prefix}district", String, nullable=True)

    @declared_attr
    def state(cls):
        return Column(f"{cls._address_prefix}state", String, nullable=True)

    @declared_attr
    def postal_code(cls):
        return Column(f"{cls._address_prefix}postal_code", String, nullable=True)

    @declared_attr
    def country(cls):
        return Column(f"{cls._address_prefix}country", String, nullable=True)

    @declared_attr
    def period_start(cls):
        return Column(f"{cls._address_prefix}period_start", DateTime(timezone=True), nullable=True)

    @declared_attr
    def period_end(cls):
        return Column(f"{cls._address_prefix}period_end", DateTime(timezone=True), nullable=True)
