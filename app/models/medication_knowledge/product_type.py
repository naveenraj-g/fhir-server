from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationKnowledgeProductType(Base, TenantAuditMixin):
    """MedicationKnowledge.productType (0..* CodeableConcept)."""

    __tablename__ = "medication_knowledge_product_type"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_pk = Column(
        BigInteger,
        ForeignKey("medication_knowledge.id"),
        nullable=False,
        index=True,
    )

    text = Column(String, nullable=True)

    medication_knowledge = relationship(
        "MedicationKnowledgeModel", back_populates="product_types"
    )
    codings = relationship(
        "MedicationKnowledgeProductTypeCoding",
        back_populates="product_type",
        cascade="all, delete-orphan",
    )


class MedicationKnowledgeProductTypeCoding(Base, TenantAuditMixin, FhirCodingMixin):
    """MedicationKnowledge.productType.coding (0..* Coding)."""

    __tablename__ = "medication_knowledge_product_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_product_type_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_product_type.id"),
        nullable=False,
        index=True,
    )

    product_type = relationship(
        "MedicationKnowledgeProductType", back_populates="codings"
    )
