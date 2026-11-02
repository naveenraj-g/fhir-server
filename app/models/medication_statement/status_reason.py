from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationStatementStatusReason(TenantAuditMixin, Base):
    """MedicationStatement.statusReason (0..* CodeableConcept) child table."""

    __tablename__ = "medication_statement_status_reason"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_statement_pk = Column(
        BigInteger, ForeignKey("medication_statement.id"), nullable=False, index=True
    )

    text = Column(String, nullable=True)

    medication_statement = relationship(
        "MedicationStatementModel", back_populates="status_reasons"
    )
    codings = relationship(
        "MedicationStatementStatusReasonCoding",
        back_populates="status_reason",
        cascade="all, delete-orphan",
    )


class MedicationStatementStatusReasonCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MedicationStatement.statusReason.coding (0..*) grandchild table."""

    __tablename__ = "medication_statement_status_reason_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_statement_status_reason_id = Column(
        BigInteger,
        ForeignKey("medication_statement_status_reason.id"),
        nullable=False,
        index=True,
    )

    status_reason = relationship(
        "MedicationStatementStatusReason", back_populates="codings"
    )
