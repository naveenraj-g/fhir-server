from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    Sequence,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.care_team.enums import (
    CareTeamEncounterReferenceType,
    CareTeamStatus,
    CareTeamSubjectReferenceType,
)
from app.models.shared import TenantAuditMixin

care_team_pub_seq = Sequence(
    "care_team_pub_seq", start=390000, metadata=Base.metadata
)


class CareTeamModel(TenantAuditMixin, Base):
    """FHIR R4 CareTeam model — https://www.hl7.org/fhir/R4/careteam.html

    The Care Team includes all the people and organizations who plan to participate
    in the coordination and delivery of care for a patient.
    """

    __tablename__ = "care_team"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_team_id = Column(
        BigInteger,
        care_team_pub_seq,
        server_default=care_team_pub_seq.next_value(),
        unique=True,
        nullable=False,
        index=True,
    )

    # status (0..1 code, required binding)
    status = Column(
        Enum(CareTeamStatus, name="care_team_status"),
        nullable=True,
    )

    # name (0..1 string)
    name = Column(String, nullable=True)

    # subject (0..1 Reference(Patient | Group)) flattened
    subject_reference = Column(String, nullable=True)
    subject_type = Column(
        Enum(
            CareTeamSubjectReferenceType,
            name="care_team_subject_reference_type",
        ),
        nullable=True,
    )
    subject_id = Column(BigInteger, nullable=True, index=True)
    subject_display = Column(String, nullable=True)

    # encounter (0..1 Reference(Encounter)) flattened
    encounter_reference = Column(String, nullable=True)
    encounter_type = Column(
        Enum(
            CareTeamEncounterReferenceType,
            name="care_team_encounter_reference_type",
        ),
        nullable=True,
    )
    encounter_id = Column(BigInteger, nullable=True, index=True)
    encounter_display = Column(String, nullable=True)

    # period (0..1 Period)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # extension (0..* Extension)
    extension = Column(JSONB, nullable=False, server_default="[]")

    # Relationships
    identifiers = relationship(
        "CareTeamIdentifier",
        back_populates="care_team",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    categories = relationship(
        "CareTeamCategory",
        back_populates="care_team",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    participants = relationship(
        "CareTeamParticipant",
        back_populates="care_team",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    reason_codes = relationship(
        "CareTeamReasonCode",
        back_populates="care_team",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    reason_references = relationship(
        "CareTeamReasonReference",
        back_populates="care_team",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    managing_organizations = relationship(
        "CareTeamManagingOrganization",
        back_populates="care_team",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    telecoms = relationship(
        "CareTeamTelecom",
        back_populates="care_team",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    notes = relationship(
        "CareTeamNote",
        back_populates="care_team",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
