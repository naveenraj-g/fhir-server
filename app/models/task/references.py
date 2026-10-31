from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.models.task.enums import (
    TaskInsuranceReferenceType,
    TaskPartOfReferenceType,
    TaskRelevantHistoryReferenceType,
    TaskRestrictionRecipientReferenceType,
)


class TaskBasedOn(TenantAuditMixin, Base):
    """Task.basedOn (0..*) child table. Reference(Any).
    No UniqueConstraint on references per FHIR R4 rules.
    """

    __tablename__ = "task_based_on"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_pk = Column(
        BigInteger, ForeignKey("task.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    task = relationship("TaskModel", back_populates="based_on_list")


class TaskPartOf(TenantAuditMixin, Base):
    """Task.partOf (0..*) child table. Reference(Task)."""

    __tablename__ = "task_part_of"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_pk = Column(
        BigInteger, ForeignKey("task.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(TaskPartOfReferenceType, name="task_part_of_reference_type"),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    task = relationship("TaskModel", back_populates="part_of_list")


class TaskInsurance(TenantAuditMixin, Base):
    """Task.insurance (0..*) child table. Reference(Coverage|ClaimResponse)."""

    __tablename__ = "task_insurance"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_pk = Column(
        BigInteger, ForeignKey("task.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(TaskInsuranceReferenceType, name="task_insurance_reference_type"),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    task = relationship("TaskModel", back_populates="insurance_list")


class TaskRelevantHistory(TenantAuditMixin, Base):
    """Task.relevantHistory (0..*) child table. Reference(Provenance)."""

    __tablename__ = "task_relevant_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_pk = Column(
        BigInteger, ForeignKey("task.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            TaskRelevantHistoryReferenceType,
            name="task_relevant_history_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    task = relationship("TaskModel", back_populates="relevant_history_list")


class TaskRestrictionRecipient(TenantAuditMixin, Base):
    """Task.restriction.recipient (0..*) child table.
    Reference(Patient|Practitioner|PractitionerRole|RelatedPerson|Group|Organization).
    """

    __tablename__ = "task_restriction_recipient"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_pk = Column(
        BigInteger, ForeignKey("task.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            TaskRestrictionRecipientReferenceType,
            name="task_restriction_recipient_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    task = relationship("TaskModel", back_populates="restriction_recipients")
