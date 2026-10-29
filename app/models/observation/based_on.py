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
from app.models.observation.enums import ObservationBasedOnReferenceType
from app.models.shared import TenantAuditMixin


class ObservationBasedOn(TenantAuditMixin, Base):
    """basedOn[] — of the six allowed types, only MedicationRequest and
    ServiceRequest are modeled resources — the existence check is only
    ever attempted for that subset (see
    app.repository.observation._shared._MODELED_BASED_ON_TYPES).

    No UniqueConstraint on (observation_pk, reference_type, reference_id):
    R4 doesn't forbid listing the same reference twice — a deployment that
    wants that as a rule expresses it as a profile-layer invariant, not a
    base constraint."""

    __tablename__ = "observation_based_on"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_pk = Column(BigInteger, ForeignKey("observation.id"), nullable=False, index=True)

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(ObservationBasedOnReferenceType, name="observation_based_on_reference_type"), nullable=True
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    reference_identifier_use = Column(Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True)
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

    observation = relationship("ObservationModel", back_populates="based_ons")
