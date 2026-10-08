from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase
from app.models.fhir_profile.enums import FhirProfileScopeLevel, FhirProfileStatus


class FhirProfile(FHIRBase):
    """One row per profile layer in the base -> country -> organization
    chain — the database-backed registry this project's file-based
    app/fhir/profiling/ stands in for today (see that folder's README).
    Each row's `structure_definition` is a real, complete FHIR
    `StructureDefinition` document — the same shape as the files already
    committed there — not a trimmed custom shape; registering a row with
    the validation sidecar (app/fhir/validation/java_validator.py) means
    POSTing `structure_definition` as-is to its /profiles endpoint.

    `scope_id` is NULL for base and country rows (shared/deployment-level,
    nobody's tenant) and the owning organization's public org_id for
    organization rows — the same nullable-tenant-column shape already used
    by TerminologyConcept.org_id, not a new pattern.

    Which country is active for a given deployment is a single, global
    config setting (settings.fhir_validation.country — see
    app/fhir/validation/dispatch.py's module docstring), not something
    resolved per-request from this table; this table can hold every
    country's profile at once, config just picks which one applies.
    """

    __tablename__ = "fhir_profile"
    __table_args__ = (
        UniqueConstraint(
            "canonical_url", "version", name="uq_fhir_profile_url_version"
        ),
        Index("ix_fhir_profile_resource_type", "resource_type"),
        Index("ix_fhir_profile_scope_level", "scope_level"),
        Index("ix_fhir_profile_scope_id", "scope_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # What this profile constrains, and where it sits in the chain.
    resource_type = Column(String, nullable=False)
    scope_level = Column(
        Enum(FhirProfileScopeLevel, name="fhir_profile_scope_level"), nullable=False
    )
    scope_id = Column(String, nullable=True)

    # Redundant with (but kept in sync against) structure_definition's own
    # "baseDefinition" field — a plain FK here means walking/validating the
    # chain is a cheap indexed query, not a JSONB parse, and the DB can
    # enforce a child's parent genuinely exists.
    parent_profile_id = Column(
        BigInteger, ForeignKey("fhir_profile.id"), nullable=True
    )

    # Redundant with (but kept in sync against) structure_definition's own
    # "url" field — the same value that gets passed as the `profile` query
    # param when validating, and what dispatch.py's URL-naming convention
    # derives for country layers (see its module docstring).
    canonical_url = Column(String, nullable=False)
    version = Column(String, nullable=False, server_default=text("'1'"))

    # Redundant with (but kept in sync against) structure_definition's own
    # "status" field — lets the app filter by status without parsing JSONB.
    status = Column(
        Enum(FhirProfileStatus, name="fhir_profile_status"),
        nullable=False,
        server_default=text("'draft'"),
    )

    # The real, complete StructureDefinition document — see this class's
    # own docstring for why this isn't a trimmed custom shape.
    structure_definition = Column(JSONB, nullable=False)

    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    parent = relationship("FhirProfile", remote_side=[id], backref="children")
