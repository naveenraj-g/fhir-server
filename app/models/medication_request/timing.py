from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class MedicationRequestTiming(Base):
    """Search index for `date` (MedicationRequest.dosageInstruction.timing.event, a 0..* dateTime
    of every dosage instruction): one row per event, as the half-open [start, end) range of
    instants the dateTime covers at its written precision. A `date` search matches any event
    (matched with period_match). Derived from MedicationRequestModel.content - never read to
    build a response."""

    __tablename__ = "medication_request_timing"
    __table_args__ = (
        Index("ix_medication_request_timing_event", "event_start", "event_end"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_request_pk = Column(
        BigInteger, ForeignKey("medication_request.id"), nullable=False, index=True
    )
    event_start = Column(DateTime(timezone=True), nullable=True)
    event_end = Column(DateTime(timezone=True), nullable=True)

    medication_request = relationship(
        "MedicationRequestModel", back_populates="timings"
    )
