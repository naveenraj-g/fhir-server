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
from app.models.medication.enums import (
    MedicationIdentifierAssignerReferenceType,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationIdentifier(Base, TenantAuditMixin):
    """Medication.identifier (0..* Identifier) child table."""

    __tablename__ = "medication_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_pk = Column(
        BigInteger,
        ForeignKey("medication.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False),
        nullable=True,
    )
    type_text = Column(String, nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # assigner Reference(Organization) with identifier fallback (15 columns)
    assigner_reference = Column(String, nullable=True)
    assigner_type = Column(
        Enum(
            MedicationIdentifierAssignerReferenceType,
            name="medication_identifier_assigner_reference_type",
        ),
        nullable=True,
    )
    assigner_id = Column(BigInteger, nullable=True, index=True)
    assigner_display = Column(String, nullable=True)

    assigner_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False),
        nullable=True,
    )
    assigner_identifier_type_system = Column(String, nullable=True)
    assigner_identifier_type_version = Column(String, nullable=True)
    assigner_identifier_type_code = Column(String, nullable=True)
    assigner_identifier_type_display = Column(String, nullable=True)
    assigner_identifier_type_user_selected = Column(Boolean, nullable=True)
    assigner_identifier_type_text = Column(String, nullable=True)
    assigner_identifier_system = Column(String, nullable=True)
    assigner_identifier_value = Column(String, nullable=True)
    assigner_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    assigner_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    medication = relationship("MedicationModel", back_populates="identifiers")
    type_codings = relationship(
        "MedicationIdentifierTypeCoding",
        back_populates="identifier",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class MedicationIdentifierTypeCoding(Base, TenantAuditMixin, FhirCodingMixin):
    """Medication.identifier.type.coding (0..* Coding) grandchild table."""

    __tablename__ = "medication_identifier_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_identifier_id = Column(
        BigInteger,
        ForeignKey("medication_identifier.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    identifier = relationship("MedicationIdentifier", back_populates="type_codings")
