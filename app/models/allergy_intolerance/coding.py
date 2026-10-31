from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class AllergyIntoleranceClinicalStatusCoding(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """AllergyIntolerance.clinicalStatus.coding (0..* Coding) child table."""

    __tablename__ = "allergy_intolerance_clinical_status_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    allergy_intolerance_pk = Column(
        BigInteger,
        ForeignKey("allergy_intolerance.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    allergy_intolerance = relationship(
        "AllergyIntoleranceModel",
        back_populates="clinical_status_codings",
    )


class AllergyIntoleranceVerificationStatusCoding(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """AllergyIntolerance.verificationStatus.coding (0..* Coding) child table."""

    __tablename__ = "allergy_intolerance_verification_status_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    allergy_intolerance_pk = Column(
        BigInteger,
        ForeignKey("allergy_intolerance.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    allergy_intolerance = relationship(
        "AllergyIntoleranceModel",
        back_populates="verification_status_codings",
    )


class AllergyIntoleranceCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """AllergyIntolerance.code.coding (0..* Coding) child table."""

    __tablename__ = "allergy_intolerance_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    allergy_intolerance_pk = Column(
        BigInteger,
        ForeignKey("allergy_intolerance.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    allergy_intolerance = relationship(
        "AllergyIntoleranceModel",
        back_populates="code_codings",
    )
