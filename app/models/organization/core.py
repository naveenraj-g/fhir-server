from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, Sequence, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse, OrganizationReferenceType

organization_id_seq = Sequence(
    "organization_pub_seq", start=190000, increment=1, metadata=Base.metadata
)


# ---------------------------------------------------------------------------
# Main table
# ---------------------------------------------------------------------------


class OrganizationModel(Base):
    __tablename__ = "organization"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    organization_id = Column(
        Integer,
        organization_id_seq,
        server_default=organization_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )
    org_id = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    # active (0..1)
    active = Column(Boolean, nullable=False, default=False)

    # name (0..1)
    name = Column(String, nullable=False)

    # partOf (0..1) Reference(Organization) — shared PG type
    partof_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    partof_id = Column(Integer, nullable=True)
    partof_display = Column(String, nullable=True)

    # partOf.identifier (0..1 Identifier) — logical-reference fallback for
    # when the parent organization isn't a resource in this system
    partof_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    partof_identifier_type_system = Column(String, nullable=True)
    partof_identifier_type_version = Column(String, nullable=True)
    partof_identifier_type_code = Column(String, nullable=True)
    partof_identifier_type_display = Column(String, nullable=True)
    partof_identifier_type_text = Column(String, nullable=True)
    partof_identifier_type_user_selected = Column(Boolean, nullable=True)
    partof_identifier_system = Column(String, nullable=True)
    partof_identifier_value = Column(String, nullable=True)
    partof_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    partof_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

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
