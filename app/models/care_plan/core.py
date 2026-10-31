from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    Sequence,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.care_plan.enums import (
    CarePlanAuthorReferenceType,
    CarePlanEncounterReferenceType,
    CarePlanIntent,
    CarePlanStatus,
    CarePlanSubjectReferenceType,
)
from app.models.shared import TenantAuditMixin

care_plan_pub_seq = Sequence(
    "care_plan_pub_seq", start=290000, metadata=Base.metadata
)


class CarePlanModel(TenantAuditMixin, Base):
    """FHIR R4 CarePlan model — https://www.hl7.org/fhir/R4/careplan.html

    Describes the intention of how one or more practitioners intend to deliver care
    for a particular patient, group or community for a period of time, possibly
    limited to care for a specific condition or strategy.
    """

    __tablename__ = "care_plan"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_plan_id = Column(
        BigInteger,
        care_plan_pub_seq,
        server_default=care_plan_pub_seq.next_value(),
        unique=True,
        nullable=False,
        index=True,
    )

    # instantiatesCanonical (0..* canonical)
    instantiates_canonical = Column(ARRAY(String), nullable=True)

    # instantiatesUri (0..* uri)
    instantiates_uri = Column(ARRAY(String), nullable=True)

    # status (1..1 code, required)
    status = Column(
        Enum(CarePlanStatus, name="care_plan_status"),
        nullable=False,
    )

    # intent (1..1 code, required)
    intent = Column(
        Enum(CarePlanIntent, name="care_plan_intent"),
        nullable=False,
    )

    # title (0..1 string)
    title = Column(String, nullable=True)

    # description (0..1 string)
    description = Column(String, nullable=True)

    # subject (1..1 Reference(Patient | Group)) flattened
    subject_reference = Column(String, nullable=True)
    subject_type = Column(
        Enum(
            CarePlanSubjectReferenceType,
            name="care_plan_subject_reference_type",
        ),
        nullable=False,
    )
    subject_id = Column(BigInteger, nullable=True, index=True)
    subject_display = Column(String, nullable=True)

    # encounter (0..1 Reference(Encounter)) flattened
    encounter_reference = Column(String, nullable=True)
    encounter_type = Column(
        Enum(
            CarePlanEncounterReferenceType,
            name="care_plan_encounter_reference_type",
        ),
        nullable=True,
    )
    encounter_id = Column(BigInteger, nullable=True, index=True)
    encounter_display = Column(String, nullable=True)

    # period (0..1 Period)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # created (0..1 dateTime)
    created = Column(DateTime(timezone=True), nullable=True)

    # author (0..1 Reference(Patient | Practitioner | PractitionerRole | RelatedPerson | Organization | CareTeam)) flattened
    author_reference = Column(String, nullable=True)
    author_type = Column(
        Enum(
            CarePlanAuthorReferenceType,
            name="care_plan_author_reference_type",
        ),
        nullable=True,
    )
    author_id = Column(BigInteger, nullable=True, index=True)
    author_display = Column(String, nullable=True)

    # extension (0..* Extension)
    extension = Column(JSONB, nullable=False, server_default="[]")

    # Relationships
    identifiers = relationship(
        "CarePlanIdentifier",
        back_populates="care_plan",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    based_on = relationship(
        "CarePlanBasedOn",
        back_populates="care_plan",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    replaces = relationship(
        "CarePlanReplaces",
        back_populates="care_plan",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    part_of = relationship(
        "CarePlanPartOf",
        back_populates="care_plan",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    categories = relationship(
        "CarePlanCategory",
        back_populates="care_plan",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    contributors = relationship(
        "CarePlanContributor",
        back_populates="care_plan",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    care_teams = relationship(
        "CarePlanCareTeam",
        back_populates="care_plan",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    addresses = relationship(
        "CarePlanAddresses",
        back_populates="care_plan",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    goals = relationship(
        "CarePlanGoal",
        back_populates="care_plan",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    activities = relationship(
        "CarePlanActivity",
        back_populates="care_plan",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    notes = relationship(
        "CarePlanNote",
        back_populates="care_plan",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
