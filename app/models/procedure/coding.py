from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ProcedureStatusReasonCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Procedure.statusReason.coding (0..* Coding) child table."""

    __tablename__ = "procedure_status_reason_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    procedure_pk = Column(
        BigInteger, ForeignKey("procedure.id", ondelete="CASCADE"), nullable=False, index=True
    )

    procedure = relationship("ProcedureModel", back_populates="status_reason_codings")


class ProcedureCategoryCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Procedure.category.coding (0..* Coding) child table."""

    __tablename__ = "procedure_category_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    procedure_pk = Column(
        BigInteger, ForeignKey("procedure.id", ondelete="CASCADE"), nullable=False, index=True
    )

    procedure = relationship("ProcedureModel", back_populates="category_codings")


class ProcedureCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Procedure.code.coding (0..* Coding) child table."""

    __tablename__ = "procedure_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    procedure_pk = Column(
        BigInteger, ForeignKey("procedure.id", ondelete="CASCADE"), nullable=False, index=True
    )

    procedure = relationship("ProcedureModel", back_populates="code_codings")


class ProcedureOutcomeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Procedure.outcome.coding (0..* Coding) child table."""

    __tablename__ = "procedure_outcome_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    procedure_pk = Column(
        BigInteger, ForeignKey("procedure.id", ondelete="CASCADE"), nullable=False, index=True
    )

    procedure = relationship("ProcedureModel", back_populates="outcome_codings")
