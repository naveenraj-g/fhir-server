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
from app.models.care_team.enums import (
    CareTeamParticipantMemberReferenceType,
    CareTeamParticipantOnBehalfOfReferenceType,
)
from app.models.enums import IdentifierUse
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class CareTeamParticipant(TenantAuditMixin, Base):
    """CareTeam.participant (0..*) child table."""

    __tablename__ = "care_team_participant"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_team_pk = Column(
        BigInteger, ForeignKey("care_team.id"), nullable=False, index=True
    )

    # member (0..1 Reference(Practitioner | PractitionerRole | RelatedPerson | Patient | Organization | CareTeam))
    member_reference = Column(String, nullable=True)
    member_type = Column(
        Enum(
            CareTeamParticipantMemberReferenceType,
            name="care_team_participant_member_reference_type",
        ),
        nullable=True,
    )
    member_id = Column(BigInteger, nullable=True, index=True)
    member_display = Column(String, nullable=True)
    member_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    member_identifier_type_system = Column(String, nullable=True)
    member_identifier_type_version = Column(String, nullable=True)
    member_identifier_type_code = Column(String, nullable=True)
    member_identifier_type_display = Column(String, nullable=True)
    member_identifier_type_user_selected = Column(Boolean, nullable=True)
    member_identifier_type_text = Column(String, nullable=True)
    member_identifier_system = Column(String, nullable=True)
    member_identifier_value = Column(String, nullable=True)
    member_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    member_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # onBehalfOf (0..1 Reference(Organization))
    on_behalf_of_reference = Column(String, nullable=True)
    on_behalf_of_type = Column(
        Enum(
            CareTeamParticipantOnBehalfOfReferenceType,
            name="care_team_participant_on_behalf_of_reference_type",
        ),
        nullable=True,
    )
    on_behalf_of_id = Column(BigInteger, nullable=True, index=True)
    on_behalf_of_display = Column(String, nullable=True)
    on_behalf_of_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    on_behalf_of_identifier_type_system = Column(String, nullable=True)
    on_behalf_of_identifier_type_version = Column(String, nullable=True)
    on_behalf_of_identifier_type_code = Column(String, nullable=True)
    on_behalf_of_identifier_type_display = Column(String, nullable=True)
    on_behalf_of_identifier_type_user_selected = Column(Boolean, nullable=True)
    on_behalf_of_identifier_type_text = Column(String, nullable=True)
    on_behalf_of_identifier_system = Column(String, nullable=True)
    on_behalf_of_identifier_value = Column(String, nullable=True)
    on_behalf_of_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    on_behalf_of_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # period (0..1 Period)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    care_team = relationship("CareTeamModel", back_populates="participants")
    roles = relationship(
        "CareTeamParticipantRole",
        back_populates="participant",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CareTeamParticipantRole(TenantAuditMixin, Base):
    """CareTeam.participant.role (0..*) grandchild table."""

    __tablename__ = "care_team_participant_role"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    participant_id = Column(
        BigInteger,
        ForeignKey("care_team_participant.id"),
        nullable=False,
        index=True,
    )
    text = Column(String, nullable=True)

    participant = relationship("CareTeamParticipant", back_populates="roles")
    codings = relationship(
        "CareTeamParticipantRoleCoding",
        back_populates="role",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CareTeamParticipantRoleCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """CareTeam.participant.role.coding (0..*) great-grandchild table."""

    __tablename__ = "care_team_participant_role_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    role_id = Column(
        BigInteger,
        ForeignKey("care_team_participant_role.id"),
        nullable=False,
        index=True,
    )

    role = relationship("CareTeamParticipantRole", back_populates="codings")
