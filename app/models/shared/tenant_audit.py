"""Shared tenant-scoping + audit columns, reusable across every resource.

Not FHIR content. None of these columns are ever serialized into a FHIR JSON
representation — they exist purely so one Postgres database can serve many
tenants safely.

`tenant_id` replaces this project's `org_id` naming. `org_id` reads as
ambiguous specifically on a resource that *is* itself a FHIR Organization —
is "org_id" the tenant, or a reference to an Organization row? This is
already called out as a point of confusion in `OrganizationCreateSchema`'s
own docstring. `tenant_id` names the concept directly and removes the
ambiguity.

Adopted first for Organization (see app/models/organization/); other
resources keep their existing hand-declared `org_id` columns until they get
the same treatment.
"""

from sqlalchemy import Column, DateTime, String
from sqlalchemy.orm import declared_attr
from sqlalchemy.sql import func


class TenantAuditMixin:
    """Mix into any declarative model to add tenant_id/created_by/updated_by/
    created_at/updated_at. Uses `declared_attr` (not bare `Column(...)`
    instances) because a `Column` object can only ever belong to one `Table`
    — `declared_attr` makes SQLAlchemy construct a fresh `Column` per
    subclass, which is what lets the same mixin be reused on every table
    without them fighting over the same column object.

    No `-> Column` return-type annotations on the methods below,
    deliberately: SQLAlchemy 2.0's Annotated-Declarative scanner misreads a
    declared_attr method's return-type hint as a mapped annotation and
    raises MappedAnnotationError — see https://sqlalche.me/e/20/zlpr.
    """

    @declared_attr
    def tenant_id(cls):
        return Column(String, nullable=False, index=True)

    @declared_attr
    def created_by(cls):
        return Column(String, nullable=False)

    @declared_attr
    def updated_by(cls):
        return Column(String, nullable=True)

    @declared_attr
    def created_at(cls):
        return Column(DateTime(timezone=True), server_default=func.now(), index=True)

    @declared_attr
    def updated_at(cls):
        return Column(DateTime(timezone=True), onupdate=func.now(), index=True)
