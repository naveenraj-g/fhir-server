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
    MedicationDispensePerformerActorReferenceType,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationDispensePerformer(TenantAuditMixin, Base):
    """MedicationDispense.performer (0..* BackboneElement) child table."""

    __tablename__ = "medication_dispense_performer"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_dispense_pk = Column(
        BigInteger, ForeignKey("medication_dispense.id"), nullable=False, index=True
    )

    function_text = Column(String, nullable=True)

    actor_reference = Column(String, nullable=False)
    actor_type = Column(
        Enum(
            MedicationDispensePerformerActorReferenceType,
            name="medication_dispense_performer_actor_reference_type",
        ),
        nullable=False,
    )
    actor_id = Column(BigInteger, nullable=True, index=True)
    actor_display = Column(String, nullable=True)

    # actor.identifier fallback (11 columns)
    actor_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    actor_identifier_type_system = Column(String, nullable=True)
    actor_identifier_type_version = Column(String, nullable=True)
    actor_identifier_type_code = Column(String, nullable=True)
    actor_identifier_type_display = Column(String, nullable=True)
    actor_identifier_type_user_selected = Column(Boolean, nullable=True)
    actor_identifier_type_text = Column(String, nullable=True)
    actor_identifier_system = Column(String, nullable=True)
    actor_identifier_value = Column(String, nullable=True)
    actor_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    actor_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    medication_dispense = relationship(
        "MedicationDispenseModel", back_populates="performers"
    )
    function_codings = relationship(
        "MedicationDispensePerformerFunctionCoding",
        back_populates="performer",
        cascade="all, delete-orphan",
    )


class MedicationDispensePerformerFunctionCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MedicationDispense.performer.function.coding (0..*) grandchild table."""

    __tablename__ = "medication_dispense_performer_function_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_dispense_performer_id = Column(
        BigInteger,
        ForeignKey("medication_dispense_performer.id"),
        nullable=False,
        index=True,
    )

    performer = relationship(
        "MedicationDispensePerformer", back_populates="function_codings"
    )
