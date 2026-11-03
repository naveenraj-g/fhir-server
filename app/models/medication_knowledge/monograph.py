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
    MedicationKnowledgeMonographSourceReferenceType,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationKnowledgeMonograph(Base, TenantAuditMixin):
    """MedicationKnowledge.monograph (0..* BackboneElement)."""

    __tablename__ = "medication_knowledge_monograph"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_pk = Column(
        BigInteger,
        ForeignKey("medication_knowledge.id"),
        nullable=False,
        index=True,
    )

    type_text = Column(String, nullable=True)

    source_reference = Column(String, nullable=True)
    source_type = Column(
        Enum(
            MedicationKnowledgeMonographSourceReferenceType,
            name="medication_knowledge_monograph_source_ref_type",
        ),
        nullable=True,
    )
    source_id = Column(BigInteger, nullable=True, index=True)
    source_display = Column(String, nullable=True)

    source_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False),
        nullable=True,
    )
    source_identifier_type_system = Column(String, nullable=True)
    source_identifier_type_version = Column(String, nullable=True)
    source_identifier_type_code = Column(String, nullable=True)
    source_identifier_type_display = Column(String, nullable=True)
    source_identifier_type_user_selected = Column(Boolean, nullable=True)
    source_identifier_type_text = Column(String, nullable=True)
    source_identifier_system = Column(String, nullable=True)
    source_identifier_value = Column(String, nullable=True)
    source_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    source_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    medication_knowledge = relationship(
        "MedicationKnowledgeModel", back_populates="monographs"
    )
    type_codings = relationship(
        "MedicationKnowledgeMonographTypeCoding",
        back_populates="monograph",
        cascade="all, delete-orphan",
    )


class MedicationKnowledgeMonographTypeCoding(Base, TenantAuditMixin, FhirCodingMixin):
    """MedicationKnowledge.monograph.type.coding (0..* Coding)."""

    __tablename__ = "medication_knowledge_monograph_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_monograph_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_monograph.id"),
        nullable=False,
        index=True,
    )

    monograph = relationship(
        "MedicationKnowledgeMonograph", back_populates="type_codings"
    )
