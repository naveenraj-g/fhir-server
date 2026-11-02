from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationStatementReasonCode(TenantAuditMixin, Base):
    """MedicationStatement.reasonCode (0..* CodeableConcept) child table."""

    __tablename__ = "medication_statement_reason_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_statement_pk = Column(
        BigInteger, ForeignKey("medication_statement.id"), nullable=False, index=True
    )

    text = Column(String, nullable=True)

    medication_statement = relationship(
        "MedicationStatementModel", back_populates="reason_codes"
    )
    codings = relationship(
        "MedicationStatementReasonCodeCoding",
        back_populates="reason_code",
        cascade="all, delete-orphan",
    )


class MedicationStatementReasonCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MedicationStatement.reasonCode.coding (0..*) grandchild table."""

    __tablename__ = "medication_statement_reason_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_statement_reason_code_id = Column(
        BigInteger,
        ForeignKey("medication_statement_reason_code.id"),
        nullable=False,
        index=True,
    )

    reason_code = relationship(
        "MedicationStatementReasonCode", back_populates="codings"
    )
