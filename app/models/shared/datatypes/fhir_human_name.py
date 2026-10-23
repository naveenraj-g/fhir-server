"""Shared FHIR `HumanName` datatype columns, reusable across every table
that embeds exactly one HumanName — either a dedicated table (one row per
`name[]` entry, see practitioner/name.py) or a prefixed group of columns
sharing a row with other fields (Organization.contact's `name_*` columns,
which predate this mixin and stay hand-declared rather than being migrated
retroactively).

`Fhir` prefix (file and class) marks this as a FHIR-datatype mixin
specifically — distinct from TenantAuditMixin, which is tenant/audit
infrastructure, not a FHIR datatype, and deliberately doesn't get this
prefix.
"""

from sqlalchemy import Column, DateTime, Enum, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import declared_attr

from app.schemas.enums import HumanNameUse


class FhirHumanNameMixin:
    """Mix into any declarative model whose row (or a prefixed slice of its
    row) represents one HumanName entry. No `-> Column` return-type
    annotations here, deliberately — see TenantAuditMixin's docstring for
    why (SQLAlchemy 2.0's MappedAnnotationError)."""

    _human_name_prefix = ""

    @declared_attr
    def use(cls):
        return Column(
            f"{cls._human_name_prefix}use",
            Enum(HumanNameUse, name="human_name_use"),
            nullable=True,
        )

    @declared_attr
    def text(cls):
        return Column(f"{cls._human_name_prefix}text", String, nullable=True)

    @declared_attr
    def family(cls):
        return Column(f"{cls._human_name_prefix}family", String, nullable=True)

    @declared_attr
    def given(cls):
        # 0..* string — a real Postgres array, not comma-separated text.
        return Column(f"{cls._human_name_prefix}given", ARRAY(String), nullable=True)

    @declared_attr
    def prefix(cls):
        return Column(f"{cls._human_name_prefix}prefix", ARRAY(String), nullable=True)

    @declared_attr
    def suffix(cls):
        return Column(f"{cls._human_name_prefix}suffix", ARRAY(String), nullable=True)

    @declared_attr
    def period_start(cls):
        return Column(
            f"{cls._human_name_prefix}period_start", DateTime(timezone=True), nullable=True
        )

    @declared_attr
    def period_end(cls):
        return Column(
            f"{cls._human_name_prefix}period_end", DateTime(timezone=True), nullable=True
        )
