from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.patient.enums import PatientLinkOtherType, PatientLinkType


class PatientLink(Base):
    """link[] BackboneElement — links to related Patient or RelatedPerson records.

    other (1..1 Reference), type (1..1 code).
    """

    __tablename__ = "patient_link"
    __table_args__ = (
        UniqueConstraint(
            "patient_id",
            "other_type",
            "other_id",
            name="uq_patient_link_other",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_id = Column(
        BigInteger, ForeignKey("patient.id"), nullable=False, index=True
    )
    org_id = Column(String, nullable=False)

    other_type = Column(
        Enum(PatientLinkOtherType, name="patient_link_other_type"),
        nullable=True,  # was nullable=False — a literal internal reference is
        # now optional since other_identifier_* below can carry an external one
    )
    other_id = Column(BigInteger, nullable=True, index=True)  # was nullable=False, same reason
    other_display = Column(String, nullable=True)

    # link.other.identifier (0..1 Identifier) — logical-reference fallback for
    # when the other Patient/RelatedPerson isn't a resource in this system
    # (e.g. a duplicate record in an external EMR)
    other_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    other_identifier_type_system = Column(String, nullable=True)
    other_identifier_type_version = Column(String, nullable=True)
    other_identifier_type_code = Column(String, nullable=True)
    other_identifier_type_display = Column(String, nullable=True)
    other_identifier_type_text = Column(String, nullable=True)
    other_identifier_type_user_selected = Column(Boolean, nullable=True)
    other_identifier_system = Column(String, nullable=True)
    other_identifier_value = Column(String, nullable=True)
    other_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    other_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    type = Column(
        Enum(PatientLinkType, name="patient_link_type"),
        nullable=False,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    patient = relationship("PatientModel", back_populates="links")
