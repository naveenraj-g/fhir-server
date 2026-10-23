"""Shared FHIR `Attachment` datatype columns, reusable across every table
that embeds exactly one Attachment — either a dedicated table (one row per
`photo[]` entry, see practitioner/photo.py — Practitioner.photo is 0..*) or
a prefixed group of columns sharing a row with other fields
(HealthcareService.photo is 0..1 and predates this mixin, so it stays
hand-declared `photo_*` columns on the main table rather than being migrated
retroactively).

`Fhir` prefix (file and class) marks this as a FHIR-datatype mixin
specifically — distinct from TenantAuditMixin, which is tenant/audit
infrastructure, not a FHIR datatype, and deliberately doesn't get this
prefix.
"""

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import declared_attr


class FhirAttachmentMixin:
    """Mix into any declarative model whose row (or a prefixed slice of its
    row) represents one Attachment entry. No `-> Column` return-type
    annotations here, deliberately — see TenantAuditMixin's docstring for
    why (SQLAlchemy 2.0's MappedAnnotationError)."""

    _attachment_prefix = ""

    @declared_attr
    def content_type(cls):
        return Column(f"{cls._attachment_prefix}content_type", String, nullable=True)

    @declared_attr
    def language(cls):
        return Column(f"{cls._attachment_prefix}language", String, nullable=True)

    @declared_attr
    def data(cls):
        # base64-encoded binary — unbounded, so Text not String.
        return Column(f"{cls._attachment_prefix}data", Text, nullable=True)

    @declared_attr
    def url(cls):
        return Column(f"{cls._attachment_prefix}url", String, nullable=True)

    @declared_attr
    def size(cls):
        # unsignedInt per R4 — bytes of content measured after decoding.
        return Column(f"{cls._attachment_prefix}size", Integer, nullable=True)

    @declared_attr
    def hash(cls):
        # base64-encoded SHA-1 hash of the data.
        return Column(f"{cls._attachment_prefix}hash", String, nullable=True)

    @declared_attr
    def title(cls):
        return Column(f"{cls._attachment_prefix}title", String, nullable=True)

    @declared_attr
    def creation(cls):
        return Column(
            f"{cls._attachment_prefix}creation", DateTime(timezone=True), nullable=True
        )
