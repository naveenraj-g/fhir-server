from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.activity_definition.enums import ActivityDefinitionAssignerReferenceType
from app.models.enums import IdentifierUse
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ActivityDefinitionIdentifier(TenantAuditMixin, Base):
    """ActivityDefinition.identifier (0..*) child table."""

    __tablename__ = "activity_definition_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_pk = Column(
        BigInteger, ForeignKey("activity_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )

    use = Column(
        Enum(IdentifierUse, name="activity_definition_identifier_use"),
        nullable=True,
    )
    type_text = Column(String, nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    assigner_reference = Column(String, nullable=True)
    assigner_type = Column(
        Enum(
            ActivityDefinitionAssignerReferenceType,
            name="activity_definition_assigner_reference_type",
        ),
        nullable=True,
    )
    assigner_id = Column(BigInteger, nullable=True, index=True)
    assigner_display = Column(String, nullable=True)

    activity_definition = relationship("ActivityDefinitionModel", back_populates="identifiers")
    type_codings = relationship(
        "ActivityDefinitionIdentifierTypeCoding",
        back_populates="identifier",
        cascade="all, delete-orphan",
    )


class ActivityDefinitionIdentifierTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """ActivityDefinition.identifier.type.coding (0..*) grandchild table."""

    __tablename__ = "activity_definition_identifier_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    identifier_id = Column(
        BigInteger,
        ForeignKey("activity_definition_identifier.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    identifier = relationship("ActivityDefinitionIdentifier", back_populates="type_codings")
