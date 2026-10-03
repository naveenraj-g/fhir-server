from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Sequence,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.shared import TenantAuditMixin

organization_id_seq = Sequence(
    "organization_pub_seq", start=190000, increment=1, metadata=Base.metadata
)


class OrganizationModel(TenantAuditMixin, Base):
    """FHIR R4 Organization. No DB-level CHECK constraints — every R4 rule
    (org-1, org-2, org-3, Reference's own "at least one of reference/
    identifier/display" shape rule, etc.), single-table or cross-table
    alike, is enforced by the FHIR validator layer (base -> country ->
    organization profile chain — see
    docs/architecture/fhir-profiling-and-extensibility-strategy.md), not by
    the database. This is a deliberate architecture choice for consistency:
    some R4 rules (org-1) can only ever be checked by application code since
    they span multiple tables, and DB triggers (the only way to make a
    cross-table rule a database-level constraint) are avoided as a matter of
    policy, so every rule — including the ones that technically could be a
    single-table CHECK — lives in the validator instead, not split across
    two places depending on which table(s) it happens to touch."""

    __tablename__ = "organization"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    organization_id = Column(
        BigInteger,
        organization_id_seq,
        server_default=organization_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    # active (0..1) — R4 removed the R3 default of true; absent means
    # unknown, not false, so this has no default and is nullable.
    active = Column(Boolean, nullable=True)

    # name (0..1) — not required on its own; org-1 ("SHALL at least have a
    # name or an identifier") is enforced at the application layer, not as a
    # DB NOT NULL (identifier lives in a separate child table, so a
    # single-column constraint can't express it anyway).
    name = Column(String, nullable=True)

    # partOf (0..1 Reference(Organization)) — a Reference is {reference,
    # type, identifier, display}, each independently 0..1 (see
    # hl7.org/fhir/R4/references.html).
    #
    # partof_reference is the raw literal string exactly as received —
    # relative ("Organization/190004") or an absolute URL to another
    # system's server entirely. Kept regardless of whether it resolves to a
    # local row. An absolute URL to an org we don't have locally has nowhere
    # else to live — it isn't partof_id (nothing to resolve to) and it isn't
    # partof_identifier_* (that's a structured business Identifier, not a
    # URL — a sender may populate either, both, or neither).
    partof_reference = Column(String, nullable=True)
    # Deliberately NOT a ForeignKey, even though partOf's target type is
    # fixed by spec (always Organization). Architecture decision: most FHIR
    # Reference fields genuinely are polymorphic (one column, several
    # possible target resource types), so this project picks one uniform
    # pattern for every cross-resource reference — flattened, no DB-level
    # FK, existence validated by the service layer at write time via
    # RESOURCE_REGISTRY/ensure_resource_exists() — rather than real FKs for
    # the handful of fields that happen to be single-target today and
    # flattened columns for the rest. Holds the PUBLIC organization_id value
    # (matching what's actually serialized into "Organization/{id}"), in
    # addition to partof_reference, when (and only when) that string
    # resolves to a local row. Three legal states are representable:
    #   - resolved locally:    partof_reference + partof_id both set
    #   - external/unresolved: partof_reference set, partof_id NULL
    #   - logical-only:        partof_identifier_* set, partof_reference/id NULL
    #   - display-only:        partof_display set, everything else NULL
    # Reference's own shape rule ("at least one of reference/identifier/
    # display") is enforced by the FHIR validator, not a DB CHECK — see the
    # class docstring.
    partof_id = Column(BigInteger, nullable=True, index=True)
    # Always "Organization" for this field — still stored, not hardcoded at
    # the mapper layer, because Reference.type is an independent spec
    # element ("avoids having to resolve the reference to know its type"),
    # not merely a polymorphism discriminator that can be dropped once
    # there's only one possible value.
    partof_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    partof_display = Column(String, nullable=True)

    # partOf's logical-reference fallback (Reference.identifier) — populated
    # instead of partof_id when the parent organization isn't a resource in
    # this system at all ("no requirement that Reference.identifier point to
    # something actually exposed as a FHIR instance" — same spec page).
    partof_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    partof_identifier_type_system = Column(String, nullable=True)
    partof_identifier_type_version = Column(String, nullable=True)
    partof_identifier_type_code = Column(String, nullable=True)
    partof_identifier_type_display = Column(String, nullable=True)
    partof_identifier_type_user_selected = Column(Boolean, nullable=True)
    partof_identifier_type_text = Column(String, nullable=True)
    partof_identifier_system = Column(String, nullable=True)
    partof_identifier_value = Column(String, nullable=True)
    partof_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    partof_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # Resource-level extension support. Raw [{url, valueType, value}, ...];
    # validated against registered extension definitions by the
    # (not-yet-built) profile pipeline — see
    # docs/architecture/fhir-profiling-and-extensibility-strategy.md §6 —
    # not by the database.
    # No explicit ::jsonb cast — Postgres infers it from the column's own
    # type in a DEFAULT clause, and the explicit cast is invalid SQL on
    # SQLite (the test suite's engine), which has no cast syntax at all.
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # Relationships
    identifiers = relationship(
        "OrganizationIdentifier",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    types = relationship(
        "OrganizationType", back_populates="organization", cascade="all, delete-orphan"
    )
    aliases = relationship(
        "OrganizationAlias", back_populates="organization", cascade="all, delete-orphan"
    )
    telecoms = relationship(
        "OrganizationTelecom",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    addresses = relationship(
        "OrganizationAddress",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    contacts = relationship(
        "OrganizationContact",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
    endpoints = relationship(
        "OrganizationEndpoint",
        back_populates="organization",
        cascade="all, delete-orphan",
    )
