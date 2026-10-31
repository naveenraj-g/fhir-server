from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.procedure.enums import (
    ProcedureBasedOnReferenceType,
    ProcedureComplicationDetailReferenceType,
    ProcedurePartOfReferenceType,
    ProcedureReasonReferenceReferenceType,
    ProcedureReportReferenceType,
    ProcedureUsedReferenceReferenceType,
)
from app.models.shared import TenantAuditMixin


class ProcedureBasedOn(TenantAuditMixin, Base):
    """Procedure.basedOn (0..* Reference(CarePlan | ServiceRequest)) child table."""

    __tablename__ = "procedure_based_on"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    procedure_pk = Column(
        BigInteger, ForeignKey("procedure.id", ondelete="CASCADE"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(ProcedureBasedOnReferenceType, name="procedure_based_on_reference_type"),
        nullable=False,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    procedure = relationship("ProcedureModel", back_populates="based_on")


class ProcedurePartOf(TenantAuditMixin, Base):
    """Procedure.partOf (0..* Reference(Procedure | Observation | MedicationAdministration)) child table."""

    __tablename__ = "procedure_part_of"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    procedure_pk = Column(
        BigInteger, ForeignKey("procedure.id", ondelete="CASCADE"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(ProcedurePartOfReferenceType, name="procedure_part_of_reference_type"),
        nullable=False,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    procedure = relationship("ProcedureModel", back_populates="part_of")


class ProcedureReasonReference(TenantAuditMixin, Base):
    """Procedure.reasonReference (0..* Reference(Condition | Observation | Procedure | DiagnosticReport | DocumentReference)) child table."""

    __tablename__ = "procedure_reason_reference"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    procedure_pk = Column(
        BigInteger, ForeignKey("procedure.id", ondelete="CASCADE"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            ProcedureReasonReferenceReferenceType,
            name="procedure_reason_reference_reference_type",
        ),
        nullable=False,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    procedure = relationship("ProcedureModel", back_populates="reason_references")


class ProcedureReport(TenantAuditMixin, Base):
    """Procedure.report (0..* Reference(DiagnosticReport | DocumentReference | Composition)) child table."""

    __tablename__ = "procedure_report"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    procedure_pk = Column(
        BigInteger, ForeignKey("procedure.id", ondelete="CASCADE"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(ProcedureReportReferenceType, name="procedure_report_reference_type"),
        nullable=False,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    procedure = relationship("ProcedureModel", back_populates="reports")


class ProcedureComplicationDetail(TenantAuditMixin, Base):
    """Procedure.complicationDetail (0..* Reference(Condition)) child table."""

    __tablename__ = "procedure_complication_detail"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    procedure_pk = Column(
        BigInteger, ForeignKey("procedure.id", ondelete="CASCADE"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            ProcedureComplicationDetailReferenceType,
            name="procedure_complication_detail_reference_type",
        ),
        nullable=False,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    procedure = relationship("ProcedureModel", back_populates="complication_details")


class ProcedureUsedReference(TenantAuditMixin, Base):
    """Procedure.usedReference (0..* Reference(Device | Medication | Substance)) child table."""

    __tablename__ = "procedure_used_reference"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    procedure_pk = Column(
        BigInteger, ForeignKey("procedure.id", ondelete="CASCADE"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            ProcedureUsedReferenceReferenceType,
            name="procedure_used_reference_reference_type",
        ),
        nullable=False,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    procedure = relationship("ProcedureModel", back_populates="used_references")
