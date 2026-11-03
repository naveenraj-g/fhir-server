from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.medication_knowledge.enums import (
    MedicationKnowledgeQuantityComparator,
    MedicationKnowledgeRegulatoryAuthorityReferenceType,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationKnowledgeRegulatory(Base, TenantAuditMixin):
    """MedicationKnowledge.regulatory (0..* BackboneElement)."""

    __tablename__ = "medication_knowledge_regulatory"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_pk = Column(
        BigInteger,
        ForeignKey("medication_knowledge.id"),
        nullable=False,
        index=True,
    )

    # regulatoryAuthority (1..1 Reference(Organization))
    regulatory_authority_reference = Column(String, nullable=True)
    regulatory_authority_type = Column(
        Enum(
            MedicationKnowledgeRegulatoryAuthorityReferenceType,
            name="medication_knowledge_reg_auth_ref_type",
        ),
        nullable=True,
    )
    regulatory_authority_id = Column(BigInteger, nullable=True, index=True)
    regulatory_authority_display = Column(String, nullable=True)

    regulatory_authority_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False),
        nullable=True,
    )
    regulatory_authority_identifier_type_system = Column(String, nullable=True)
    regulatory_authority_identifier_type_version = Column(String, nullable=True)
    regulatory_authority_identifier_type_code = Column(String, nullable=True)
    regulatory_authority_identifier_type_display = Column(String, nullable=True)
    regulatory_authority_identifier_type_user_selected = Column(Boolean, nullable=True)
    regulatory_authority_identifier_type_text = Column(String, nullable=True)
    regulatory_authority_identifier_system = Column(String, nullable=True)
    regulatory_authority_identifier_value = Column(String, nullable=True)
    regulatory_authority_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    regulatory_authority_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # maxDispense (0..1 BackboneElement)
    max_dispense_quantity_value = Column(Numeric, nullable=True)
    max_dispense_quantity_comparator = Column(
        Enum(
            MedicationKnowledgeQuantityComparator,
            name="medication_knowledge_quantity_comparator",
            create_type=False,
        ),
        nullable=True,
    )
    max_dispense_quantity_unit = Column(String, nullable=True)
    max_dispense_quantity_system = Column(String, nullable=True)
    max_dispense_quantity_code = Column(String, nullable=True)

    max_dispense_period_value = Column(Numeric, nullable=True)
    max_dispense_period_comparator = Column(
        Enum(
            MedicationKnowledgeQuantityComparator,
            name="medication_knowledge_quantity_comparator",
            create_type=False,
        ),
        nullable=True,
    )
    max_dispense_period_unit = Column(String, nullable=True)
    max_dispense_period_system = Column(String, nullable=True)
    max_dispense_period_code = Column(String, nullable=True)

    medication_knowledge = relationship(
        "MedicationKnowledgeModel", back_populates="regulatory"
    )
    substitutions = relationship(
        "MedicationKnowledgeRegulatorySubstitution",
        back_populates="regulatory",
        cascade="all, delete-orphan",
    )
    schedules = relationship(
        "MedicationKnowledgeRegulatorySchedule",
        back_populates="regulatory",
        cascade="all, delete-orphan",
    )


class MedicationKnowledgeRegulatorySubstitution(Base, TenantAuditMixin):
    """MedicationKnowledge.regulatory.substitution (0..* BackboneElement)."""

    __tablename__ = "medication_knowledge_reg_sub"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_regulatory_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_regulatory.id"),
        nullable=False,
        index=True,
    )

    type_text = Column(String, nullable=True)
    allowed = Column(Boolean, nullable=True)

    regulatory = relationship(
        "MedicationKnowledgeRegulatory", back_populates="substitutions"
    )
    type_codings = relationship(
        "MedicationKnowledgeRegulatorySubstitutionTypeCoding",
        back_populates="reg_sub",
        cascade="all, delete-orphan",
    )


class MedicationKnowledgeRegulatorySubstitutionTypeCoding(Base, TenantAuditMixin, FhirCodingMixin):
    """MedicationKnowledge.regulatory.substitution.type.coding (0..* Coding)."""

    __tablename__ = "medication_knowledge_reg_sub_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_reg_sub_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_reg_sub.id"),
        nullable=False,
        index=True,
    )

    reg_sub = relationship(
        "MedicationKnowledgeRegulatorySubstitution", back_populates="type_codings"
    )


class MedicationKnowledgeRegulatorySchedule(Base, TenantAuditMixin):
    """MedicationKnowledge.regulatory.schedule (0..* BackboneElement)."""

    __tablename__ = "medication_knowledge_reg_sched"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_regulatory_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_regulatory.id"),
        nullable=False,
        index=True,
    )

    schedule_text = Column(String, nullable=True)

    regulatory = relationship(
        "MedicationKnowledgeRegulatory", back_populates="schedules"
    )
    schedule_codings = relationship(
        "MedicationKnowledgeRegulatoryScheduleCoding",
        back_populates="reg_sched",
        cascade="all, delete-orphan",
    )


class MedicationKnowledgeRegulatoryScheduleCoding(Base, TenantAuditMixin, FhirCodingMixin):
    """MedicationKnowledge.regulatory.schedule.schedule.coding (0..* Coding)."""

    __tablename__ = "medication_knowledge_reg_sched_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_knowledge_reg_sched_id = Column(
        BigInteger,
        ForeignKey("medication_knowledge_reg_sched.id"),
        nullable=False,
        index=True,
    )

    reg_sched = relationship(
        "MedicationKnowledgeRegulatorySchedule", back_populates="schedule_codings"
    )
