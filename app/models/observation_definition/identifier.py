from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ObservationDefinitionIdentifier(TenantAuditMixin, Base):
    """ObservationDefinition.identifier (0..*) child table."""

    __tablename__ = "observation_definition_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_definition_pk = Column(
        BigInteger, ForeignKey("observation_definition.id"), nullable=False, index=True
    )

    use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    type_text = Column(String, nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # assigner (0..1 Reference(Organization))
    assigner_reference = Column(String, nullable=True)
    assigner_id = Column(BigInteger, nullable=True, index=True)
    assigner_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    assigner_display = Column(String, nullable=True)

    # assigner.identifier fallback
    assigner_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    assigner_identifier_system = Column(String, nullable=True)
    assigner_identifier_value = Column(String, nullable=True)
    assigner_identifier_type_text = Column(String, nullable=True)

    observation_definition = relationship(
        "ObservationDefinitionModel", back_populates="identifiers"
    )
    type_codings = relationship(
        "ObservationDefinitionIdentifierTypeCoding",
        back_populates="identifier",
        cascade="all, delete-orphan",
    )


class ObservationDefinitionIdentifierTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """ObservationDefinition.identifier.type.coding (0..*) grandchild table."""

    __tablename__ = "observation_definition_identifier_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    identifier_id = Column(
        BigInteger,
        ForeignKey("observation_definition_identifier.id"),
        nullable=False,
        index=True,
    )

    identifier = relationship(
        "ObservationDefinitionIdentifier", back_populates="type_codings"
    )
