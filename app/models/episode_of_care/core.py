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
from app.models.episode_of_care.enums import (
    EpisodeOfCareCareManagerReferenceType,
    EpisodeOfCareManagingOrganizationReferenceType,
    EpisodeOfCarePatientReferenceType,
    EpisodeOfCareStatus,
)
from app.models.shared import TenantAuditMixin


class EpisodeOfCareModel(TenantAuditMixin, Base):
    """FHIR R4 EpisodeOfCare resource.

    An association between a patient and an organization / healthcare provider(s)
    during which encounters and healthcare services may occur.
    """

    __tablename__ = "episode_of_care"

    id = Column(BigInteger, primary_key=True)
    episode_of_care_id = Column(
        BigInteger,
        Sequence(
            "episode_of_care_pub_seq",
            start=350000,
            increment=1,
            metadata=Base.metadata,
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    # Core scalar fields
    status = Column(
        Enum(
            EpisodeOfCareStatus,
            name="episode_of_care_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
        index=True,
    )

    # patient (1..1 Reference(Patient))
    patient_reference = Column(String, nullable=False)
    patient_type = Column(
        Enum(
            EpisodeOfCarePatientReferenceType,
            name="episode_of_care_patient_reference_type",
        ),
        nullable=True,
    )
    patient_id = Column(BigInteger, nullable=True, index=True)
    patient_display = Column(String, nullable=True)

    # managingOrganization (0..1 Reference(Organization))
    managing_organization_reference = Column(String, nullable=True)
    managing_organization_type = Column(
        Enum(
            EpisodeOfCareManagingOrganizationReferenceType,
            name="episode_of_care_managing_org_reference_type",
        ),
        nullable=True,
    )
    managing_organization_id = Column(BigInteger, nullable=True, index=True)
    managing_organization_display = Column(String, nullable=True)

    # period (0..1 Period)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # careManager (0..1 Reference(Practitioner | PractitionerRole))
    care_manager_reference = Column(String, nullable=True)
    care_manager_type = Column(
        Enum(
            EpisodeOfCareCareManagerReferenceType,
            name="episode_of_care_care_manager_reference_type",
        ),
        nullable=True,
    )
    care_manager_id = Column(BigInteger, nullable=True, index=True)
    care_manager_display = Column(String, nullable=True)

    # extension (0..* Extension)
    extension = Column(JSONB, nullable=False, default=list, server_default="[]")

    # Child relationships (0..*)
    identifiers = relationship(
        "EpisodeOfCareIdentifier",
        back_populates="episode_of_care",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    status_history = relationship(
        "EpisodeOfCareStatusHistory",
        back_populates="episode_of_care",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    types = relationship(
        "EpisodeOfCareType",
        back_populates="episode_of_care",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    diagnoses = relationship(
        "EpisodeOfCareDiagnosis",
        back_populates="episode_of_care",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    referral_requests = relationship(
        "EpisodeOfCareReferralRequest",
        back_populates="episode_of_care",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    teams = relationship(
        "EpisodeOfCareTeam",
        back_populates="episode_of_care",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    accounts = relationship(
        "EpisodeOfCareAccount",
        back_populates="episode_of_care",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
