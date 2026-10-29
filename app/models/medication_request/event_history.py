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
from app.models.enums import IdentifierUse
from app.models.medication_request.enums import MedicationRequestEventHistoryReferenceType
from app.models.shared import TenantAuditMixin


class MedicationRequestEventHistory(TenantAuditMixin, Base):
    """eventHistory[] — Provenance is not a modeled resource in this
    system; the existence check is never attempted for this field."""

    __tablename__ = "medication_request_event_history"
    __table_args__ = (
        UniqueConstraint(
            "medication_request_pk", "reference_id",
            name="uq_medication_request_event_history_reference",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_request_pk = Column(BigInteger, ForeignKey("medication_request.id"), nullable=False, index=True)

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(MedicationRequestEventHistoryReferenceType, name="medication_request_event_history_reference_type"),
        nullable=True,
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

    medication_request = relationship("MedicationRequestModel", back_populates="event_histories")
