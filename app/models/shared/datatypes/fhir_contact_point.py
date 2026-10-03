"""Shared FHIR `ContactPoint` datatype columns, reusable across every table
that embeds exactly one ContactPoint — either a dedicated table (the normal
case: organization_telecom, organization_contact_telecom) or, if a future
table ever needs it, a prefixed group of columns sharing a row with other
fields (same `_contact_point_prefix` mechanism as FhirAddressMixin — see
that file). Not needed by any current usage, but kept consistent with every
other Fhir*Mixin so the pattern doesn't have to be re-derived later.

Table-specific CHECK-style rules (e.g. org-3's "no home-use telecom" on
Organization.telecom, or the positiveInt rank>0 rule) are enforced by the
FHIR validator layer, not here — see OrganizationModel's docstring
(app/models/organization/core.py) for why.

`Fhir` prefix (file and class) marks this as a FHIR-datatype mixin
specifically — distinct from TenantAuditMixin, which is tenant/audit
infrastructure, not a FHIR datatype, and deliberately doesn't get this
prefix.
"""

from sqlalchemy import Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import declared_attr

from app.schemas.enums import ContactPointSystem, ContactPointUse


class FhirContactPointMixin:
    """Mix into any declarative model whose row (or a prefixed slice of its
    row) represents one ContactPoint entry. No `-> Column` return-type
    annotations here, deliberately — see TenantAuditMixin's docstring for
    why (SQLAlchemy 2.0's MappedAnnotationError)."""

    _contact_point_prefix = ""

    @declared_attr
    def system(cls):
        # system/value are 0..1 on ContactPoint — not required even here.
        return Column(
            f"{cls._contact_point_prefix}system",
            Enum(ContactPointSystem, name="contact_point_system"),
            nullable=True,
        )

    @declared_attr
    def value(cls):
        return Column(f"{cls._contact_point_prefix}value", String, nullable=True)

    @declared_attr
    def use(cls):
        return Column(
            f"{cls._contact_point_prefix}use",
            Enum(ContactPointUse, name="contact_point_use"),
            nullable=True,
        )

    @declared_attr
    def rank(cls):
        # positiveInt (1..2,147,483,647) — enforced by the FHIR validator
        # layer (lower bound excludes zero); Postgres's int4 upper bound
        # already matches positiveInt's max.
        return Column(f"{cls._contact_point_prefix}rank", Integer, nullable=True)

    @declared_attr
    def period_start(cls):
        return Column(
            f"{cls._contact_point_prefix}period_start", DateTime(timezone=True), nullable=True
        )

    @declared_attr
    def period_end(cls):
        return Column(
            f"{cls._contact_point_prefix}period_end", DateTime(timezone=True), nullable=True
        )
