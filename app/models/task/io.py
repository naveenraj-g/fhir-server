from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class TaskInput(TenantAuditMixin, Base):
    """Task.input (0..*) child table."""

    __tablename__ = "task_input"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_pk = Column(
        BigInteger, ForeignKey("task.id"), nullable=False, index=True
    )

    type_text = Column(String, nullable=True)

    value_string = Column(Text, nullable=True)
    value_boolean = Column(Boolean, nullable=True)
    value_integer = Column(Integer, nullable=True)
    value_decimal = Column(Numeric, nullable=True)
    value_date = Column(Date, nullable=True)
    value_date_time = Column(DateTime(timezone=True), nullable=True)
    value_time = Column(Time, nullable=True)
    value_uri = Column(String, nullable=True)
    value_code = Column(String, nullable=True)
    value_reference_reference = Column(String, nullable=True)
    value_reference_type = Column(String, nullable=True)
    value_reference_id = Column(BigInteger, nullable=True, index=True)
    value_reference_display = Column(String, nullable=True)
    value_json = Column(JSONB, nullable=True)

    task = relationship("TaskModel", back_populates="inputs")
    type_codings = relationship(
        "TaskInputTypeCoding",
        back_populates="task_input",
        cascade="all, delete-orphan",
    )


class TaskInputTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Task.input.type.coding (0..*) grandchild table."""

    __tablename__ = "task_input_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_input_id = Column(
        BigInteger,
        ForeignKey("task_input.id"),
        nullable=False,
        index=True,
    )

    task_input = relationship("TaskInput", back_populates="type_codings")


class TaskOutput(TenantAuditMixin, Base):
    """Task.output (0..*) child table."""

    __tablename__ = "task_output"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_pk = Column(
        BigInteger, ForeignKey("task.id"), nullable=False, index=True
    )

    type_text = Column(String, nullable=True)

    value_string = Column(Text, nullable=True)
    value_boolean = Column(Boolean, nullable=True)
    value_integer = Column(Integer, nullable=True)
    value_decimal = Column(Numeric, nullable=True)
    value_date = Column(Date, nullable=True)
    value_date_time = Column(DateTime(timezone=True), nullable=True)
    value_time = Column(Time, nullable=True)
    value_uri = Column(String, nullable=True)
    value_code = Column(String, nullable=True)
    value_reference_reference = Column(String, nullable=True)
    value_reference_type = Column(String, nullable=True)
    value_reference_id = Column(BigInteger, nullable=True, index=True)
    value_reference_display = Column(String, nullable=True)
    value_json = Column(JSONB, nullable=True)

    task = relationship("TaskModel", back_populates="outputs")
    type_codings = relationship(
        "TaskOutputTypeCoding",
        back_populates="task_output",
        cascade="all, delete-orphan",
    )


class TaskOutputTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Task.output.type.coding (0..*) grandchild table."""

    __tablename__ = "task_output_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    task_output_id = Column(
        BigInteger,
        ForeignKey("task_output.id"),
        nullable=False,
        index=True,
    )

    task_output = relationship("TaskOutput", back_populates="type_codings")
