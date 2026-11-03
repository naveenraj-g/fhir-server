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
from app.models.medication_administration.enums import (
    MedicationAdministrationPerformerActorReferenceType,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationAdministrationPerformer(TenantAuditMixin, Base):
    """MedicationAdministration.performer (0..* BackboneElement) child table."""

    __tablename__ = "medication_administration_performer"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_administration_pk = Column(
        BigInteger, ForeignKey("medication_administration.id"), nullable=False, index=True
    )

    function_text = Column(String, nullable=True)

    actor_reference = Column(String, nullable=False)
    actor_type = Column(
        Enum(
            MedicationAdministrationPerformerActorReferenceType,
            name="medication_administration_performer_actor_reference_type",
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

    medication_administration = relationship(
        "MedicationAdministrationModel", back_populates="performers"
    )
    function_codings = relationship(
        "MedicationAdministrationPerformerFunctionCoding",
        back_populates="performer",
        cascade="all, delete-orphan",
    )


class MedicationAdministrationPerformerFunctionCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MedicationAdministration.performer.function.coding (0..*) grandchild table."""

    __tablename__ = "medication_administration_performer_function_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_administration_performer_id = Column(
        BigInteger,
        ForeignKey("medication_administration_performer.id"),
        nullable=False,
        index=True,
    )

    performer = relationship(
        "MedicationAdministrationPerformer", back_populates="function_codings"
    )
