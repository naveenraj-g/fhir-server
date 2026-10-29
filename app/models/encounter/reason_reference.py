from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.encounter.enums import EncounterReasonReferenceType
from app.models.enums import IdentifierUse
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# reasonReference (0..*) Reference(Condition|Procedure|Observation|
# ImmunizationRecommendation) child table
# ---------------------------------------------------------------------------


class EncounterReasonReference(TenantAuditMixin, Base):
    """reasonReference[] — reason the encounter takes place, expressed as
    a code/reference. None of Condition/Procedure/Observation/
    ImmunizationRecommendation are modeled resources in this system;
    existence check never attempted — same situation as
    AppointmentReasonReference."""

    __tablename__ = "encounter_reason_reference"
    __table_args__ = (
        UniqueConstraint(
            "encounter_pk", "reference_type", "reference_id",
            name="uq_encounter_reason_reference_reference",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_pk = Column(
        BigInteger, ForeignKey("encounter.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(EncounterReasonReferenceType, name="encounter_reason_reference_type"),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    encounter = relationship("EncounterModel", back_populates="reason_references")
