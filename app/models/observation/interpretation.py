from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# interpretation (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class ObservationInterpretation(TenantAuditMixin, Base):
    """One entry of Observation.interpretation (0..* CodeableConcept)."""

    __tablename__ = "observation_interpretation"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_pk = Column(BigInteger, ForeignKey("observation.id"), nullable=False, index=True)
    text = Column(String, nullable=True)

    observation = relationship("ObservationModel", back_populates="interpretations")
    codings = relationship(
        "ObservationInterpretationCoding", back_populates="interpretation", cascade="all, delete-orphan"
    )


class ObservationInterpretationCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Observation.interpretation.coding (0..*)."""

    __tablename__ = "observation_interpretation_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_interpretation_id = Column(
        BigInteger, ForeignKey("observation_interpretation.id"), nullable=False, index=True
    )

    interpretation = relationship("ObservationInterpretation", back_populates="codings")
