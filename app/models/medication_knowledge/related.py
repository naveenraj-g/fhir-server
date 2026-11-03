from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.medication_knowledge.enums import (
    MedicationKnowledgeRelatedReferenceType,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationKnowledgeRelated(Base, TenantAuditMixin):
    """MedicationKnowledge.relatedMedicationKnowledge (0..* BackboneElement)."""

    __tablename__ = "medication_knowledge_related"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_pk = Column(
        BigInteger,
        ForeignKey("medication_knowledge.id"),
        nullable=False,
        index=True,
    )

    type_text = Column(String, nullable=True)

    medication_knowledge = relationship(
        "MedicationKnowledgeModel", back_populates="related_knowledge"
    )
    type_codings = relationship(
        "MedicationKnowledgeRelatedTypeCoding",
        back_populates="related_knowledge",
        cascade="all, delete-orphan",
    )
    references = relationship(
        "MedicationKnowledgeRelatedReference",
        back_populates="related_knowledge",
        cascade="all, delete-orphan",
    )


class MedicationKnowledgeRelatedTypeCoding(Base, TenantAuditMixin, FhirCodingMixin):
    """MedicationKnowledge.relatedMedicationKnowledge.type.coding (0..* Coding)."""

    __tablename__ = "medication_knowledge_related_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_related_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_related.id"),
        nullable=False,
        index=True,
    )

    related_knowledge = relationship(
        "MedicationKnowledgeRelated", back_populates="type_codings"
    )


class MedicationKnowledgeRelatedReference(Base, TenantAuditMixin):
    """MedicationKnowledge.relatedMedicationKnowledge.reference (1..* Reference(MedicationKnowledge))."""

    __tablename__ = "medication_knowledge_related_reference"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_related_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_related.id"),
        nullable=False,
        index=True,
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            MedicationKnowledgeRelatedReferenceType,
            name="medication_knowledge_related_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False),
        nullable=True,
    )
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    related_knowledge = relationship(
        "MedicationKnowledgeRelated", back_populates="references"
    )
