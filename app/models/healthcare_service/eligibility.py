from sqlalchemy import BigInteger, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# eligibility (0..*) BackboneElement child table
# ---------------------------------------------------------------------------


class HealthcareServiceEligibility(TenantAuditMixin, Base):
    """eligibility[] BackboneElement — eligibility requirements for the service.

    BackboneElement fields:
      - code     (0..1 CodeableConcept)  eligibility classification
      - comment  (0..1 markdown)         explanation of the requirement

    code_text stays flattened (sibling of coding[], not part of it);
    code's coding[] is a real 0..* child table
    (HealthcareServiceEligibilityCodeCoding, below) rather than a single
    flattened coding — same reasoning as OrganizationType's own coding[]
    promotion.
    """

    __tablename__ = "healthcare_service_eligibility"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_pk = Column(
        BigInteger, ForeignKey("healthcare_service.id"), nullable=False, index=True
    )

    # code (0..1 CodeableConcept) — text flattened, coding[] a real child table
    code_text = Column(String, nullable=True)

    # comment (0..1 markdown)
    comment = Column(Text, nullable=True)

    healthcare_service = relationship(
        "HealthcareServiceModel", back_populates="eligibilities"
    )
    code_codings = relationship(
        "HealthcareServiceEligibilityCodeCoding",
        back_populates="eligibility",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------------------
# eligibility.code.coding (0..*) grandchild table
# ---------------------------------------------------------------------------


class HealthcareServiceEligibilityCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of HealthcareService.eligibility.code.coding (0..*)."""

    __tablename__ = "healthcare_service_eligibility_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    healthcare_service_eligibility_id = Column(
        BigInteger,
        ForeignKey("healthcare_service_eligibility.id"),
        nullable=False,
        index=True,
    )

    eligibility = relationship(
        "HealthcareServiceEligibility", back_populates="code_codings"
    )
