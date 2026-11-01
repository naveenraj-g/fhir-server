from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.care_plan.enums import CarePlanAuthorReferenceType
from app.models.shared import TenantAuditMixin


class CarePlanNote(TenantAuditMixin, Base):
    """CarePlan.note (0..*) Annotation child table."""

    __tablename__ = "care_plan_note"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_plan_pk = Column(
        BigInteger, ForeignKey("care_plan.id"), nullable=False, index=True
    )

    text = Column(String, nullable=False)
    time = Column(DateTime(timezone=True), nullable=True)
    author_string = Column(String, nullable=True)
    author_reference_reference = Column(String, nullable=True)
    author_reference_type = Column(
        Enum(
            CarePlanAuthorReferenceType,
            name="care_plan_author_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    author_reference_id = Column(BigInteger, nullable=True)
    author_reference_display = Column(String, nullable=True)
    author_reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    author_reference_identifier_type_system = Column(String, nullable=True)
    author_reference_identifier_type_version = Column(String, nullable=True)
    author_reference_identifier_type_code = Column(String, nullable=True)
    author_reference_identifier_type_display = Column(String, nullable=True)
    author_reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    author_reference_identifier_type_text = Column(String, nullable=True)
    author_reference_identifier_system = Column(String, nullable=True)
    author_reference_identifier_value = Column(String, nullable=True)
    author_reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    author_reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    care_plan = relationship("CarePlanModel", back_populates="notes")
