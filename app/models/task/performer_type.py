from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class TaskPerformerType(TenantAuditMixin, Base):
    """Task.performerType (0..*) CodeableConcept child table."""

    __tablename__ = "task_performer_type"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_pk = Column(
        BigInteger, ForeignKey("task.id"), nullable=False, index=True
    )

    text = Column(String, nullable=True)

    task = relationship("TaskModel", back_populates="performer_types")
    codings = relationship(
        "TaskPerformerTypeCoding",
        back_populates="performer_type",
        cascade="all, delete-orphan",
    )


class TaskPerformerTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Task.performerType.coding (0..*) grandchild table."""

    __tablename__ = "task_performer_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_performer_type_id = Column(
        BigInteger,
        ForeignKey("task_performer_type.id"),
        nullable=False,
        index=True,
    )

    performer_type = relationship("TaskPerformerType", back_populates="codings")
