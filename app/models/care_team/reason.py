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
from app.models.care_team.enums import CareTeamReasonReferenceType
from app.models.enums import IdentifierUse
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class CareTeamReasonCode(TenantAuditMixin, Base):
    """CareTeam.reasonCode (0..*) child table."""

    __tablename__ = "care_team_reason_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_team_pk = Column(
        BigInteger, ForeignKey("care_team.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    care_team = relationship("CareTeamModel", back_populates="reason_codes")
    codings = relationship(
        "CareTeamReasonCodeCoding",
        back_populates="reason_code",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CareTeamReasonCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """CareTeam.reasonCode.coding (0..*) grandchild table."""

    __tablename__ = "care_team_reason_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    reason_code_id = Column(
        BigInteger,
        ForeignKey("care_team_reason_code.id"),
        nullable=False,
        index=True,
    )

    reason_code = relationship("CareTeamReasonCode", back_populates="codings")


class CareTeamReasonReference(TenantAuditMixin, Base):
    """CareTeam.reasonReference (0..*) child table."""

    __tablename__ = "care_team_reason_reference"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_team_pk = Column(
        BigInteger, ForeignKey("care_team.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            CareTeamReasonReferenceType,
            name="care_team_reason_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)
    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    care_team = relationship("CareTeamModel", back_populates="reason_references")
