"""Shared FHIR `Coding` datatype columns, reusable across every table that
embeds exactly one Coding — either a dedicated table (the normal case: one
row per coding[] entry, see organization/type.py, contact.py, identifier.py)
or, if a future table ever needs it, a prefixed group of columns sharing a
row with other fields (same `_coding_prefix` mechanism as FhirAddressMixin —
see that file). Not needed by any current usage, but kept consistent with
every other Fhir*Mixin so the pattern doesn't have to be re-derived later.

`Fhir` prefix (file and class) marks this as a FHIR-datatype mixin
specifically — distinct from TenantAuditMixin, which is tenant/audit
infrastructure, not a FHIR datatype, and deliberately doesn't get this
prefix.
"""

from sqlalchemy import Boolean, Column, String
from sqlalchemy.orm import declared_attr


class FhirCodingMixin:
    """Mix into any declarative model whose row (or a prefixed slice of its
    row) represents one Coding entry (system/version/code/display/
    userSelected). No `-> Column` return-type annotations here,
    deliberately — see TenantAuditMixin's docstring for why (SQLAlchemy
    2.0's MappedAnnotationError)."""

    _coding_prefix = ""

    @declared_attr
    def system(cls):
        return Column(f"{cls._coding_prefix}system", String, nullable=True)

    @declared_attr
    def version(cls):
        return Column(f"{cls._coding_prefix}version", String, nullable=True)

    @declared_attr
    def code(cls):
        return Column(f"{cls._coding_prefix}code", String, nullable=True)

    @declared_attr
    def display(cls):
        return Column(f"{cls._coding_prefix}display", String, nullable=True)

    @declared_attr
    def user_selected(cls):
        return Column(f"{cls._coding_prefix}user_selected", Boolean, nullable=True)
