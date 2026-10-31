from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class TaskCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Task.code.coding (0..*) child table."""

    __tablename__ = "task_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_pk = Column(
        BigInteger, ForeignKey("task.id"), nullable=False, index=True
    )

    task = relationship("TaskModel", back_populates="code_codings")


class TaskStatusReasonCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Task.statusReason.coding (0..*) child table."""

    __tablename__ = "task_status_reason_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_pk = Column(
        BigInteger, ForeignKey("task.id"), nullable=False, index=True
    )

    task = relationship("TaskModel", back_populates="status_reason_codings")


class TaskBusinessStatusCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Task.businessStatus.coding (0..*) child table."""

    __tablename__ = "task_business_status_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_pk = Column(
        BigInteger, ForeignKey("task.id"), nullable=False, index=True
    )

    task = relationship("TaskModel", back_populates="business_status_codings")


class TaskReasonCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Task.reasonCode.coding (0..*) child table."""

    __tablename__ = "task_reason_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_pk = Column(
        BigInteger, ForeignKey("task.id"), nullable=False, index=True
    )

    task = relationship("TaskModel", back_populates="reason_code_codings")
