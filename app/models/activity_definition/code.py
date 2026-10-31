from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ActivityDefinitionCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """ActivityDefinition.code.coding (0..*) child table."""

    __tablename__ = "activity_definition_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_pk = Column(
        BigInteger, ForeignKey("activity_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )

    activity_definition = relationship("ActivityDefinitionModel", back_populates="code_codings")


class ActivityDefinitionSubjectCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """ActivityDefinition.subjectCodeableConcept.coding (0..*) child table."""

    __tablename__ = "activity_definition_subject_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_pk = Column(
        BigInteger, ForeignKey("activity_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )

    activity_definition = relationship("ActivityDefinitionModel", back_populates="subject_codings")


class ActivityDefinitionProductCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """ActivityDefinition.productCodeableConcept.coding (0..*) child table."""

    __tablename__ = "activity_definition_product_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_pk = Column(
        BigInteger, ForeignKey("activity_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )

    activity_definition = relationship("ActivityDefinitionModel", back_populates="product_codings")
