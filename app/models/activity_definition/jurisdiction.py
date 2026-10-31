from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ActivityDefinitionJurisdiction(TenantAuditMixin, Base):
    """ActivityDefinition.jurisdiction (0..* CodeableConcept) child table."""

    __tablename__ = "activity_definition_jurisdiction"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_pk = Column(
        BigInteger, ForeignKey("activity_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    activity_definition = relationship("ActivityDefinitionModel", back_populates="jurisdictions")
    codings = relationship(
        "ActivityDefinitionJurisdictionCoding",
        back_populates="jurisdiction",
        cascade="all, delete-orphan",
    )


class ActivityDefinitionJurisdictionCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """ActivityDefinition.jurisdiction.coding (0..*) grandchild table."""

    __tablename__ = "activity_definition_jurisdiction_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_jurisdiction_id = Column(
        BigInteger,
        ForeignKey("activity_definition_jurisdiction.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    jurisdiction = relationship("ActivityDefinitionJurisdiction", back_populates="codings")
