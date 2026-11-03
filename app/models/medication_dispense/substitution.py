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
from app.models.medication_dispense.enums import (
    MedicationDispenseSubstitutionResponsiblePartyReferenceType,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationDispenseSubstitutionTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MedicationDispense.substitution.type.coding (0..*) child table."""

    __tablename__ = "medication_dispense_substitution_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_dispense_pk = Column(
        BigInteger, ForeignKey("medication_dispense.id"), nullable=False, index=True
    )

    medication_dispense = relationship(
        "MedicationDispenseModel", back_populates="substitution_type_codings"
    )


class MedicationDispenseSubstitutionReason(TenantAuditMixin, Base):
    """MedicationDispense.substitution.reason (0..* CodeableConcept) child table."""

    __tablename__ = "medication_dispense_substitution_reason"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_dispense_pk = Column(
        BigInteger, ForeignKey("medication_dispense.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    medication_dispense = relationship(
        "MedicationDispenseModel", back_populates="substitution_reasons"
    )
    codings = relationship(
        "MedicationDispenseSubstitutionReasonCoding",
        back_populates="reason",
        cascade="all, delete-orphan",
    )


class MedicationDispenseSubstitutionReasonCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MedicationDispense.substitution.reason.coding (0..*) grandchild table."""

    __tablename__ = "medication_dispense_substitution_reason_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_dispense_substitution_reason_id = Column(
        BigInteger,
        ForeignKey("medication_dispense_substitution_reason.id"),
        nullable=False,
        index=True,
    )

    reason = relationship(
        "MedicationDispenseSubstitutionReason", back_populates="codings"
    )


class MedicationDispenseSubstitutionResponsibleParty(TenantAuditMixin, Base):
    """MedicationDispense.substitution.responsibleParty (0..* Reference) child table."""

    __tablename__ = "medication_dispense_substitution_responsible_party"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_dispense_pk = Column(
        BigInteger, ForeignKey("medication_dispense.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            MedicationDispenseSubstitutionResponsiblePartyReferenceType,
            name="medication_dispense_substitution_responsible_party_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    # Reference.identifier fallback (11 columns)
    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
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

    medication_dispense = relationship(
        "MedicationDispenseModel", back_populates="substitution_responsible_parties"
    )
