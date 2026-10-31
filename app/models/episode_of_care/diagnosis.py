from sqlalchemy import (
    BigInteger,
    Column,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.episode_of_care.enums import EpisodeOfCareDiagnosisConditionReferenceType
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class EpisodeOfCareDiagnosis(TenantAuditMixin, Base):
    """EpisodeOfCare.diagnosis (0..*) child table."""

    __tablename__ = "episode_of_care_diagnosis"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    episode_of_care_pk = Column(
        BigInteger, ForeignKey("episode_of_care.id"), nullable=False, index=True
    )

    # condition (1..1 Reference(Condition))
    condition_reference = Column(String, nullable=False)
    condition_type = Column(
        Enum(
            EpisodeOfCareDiagnosisConditionReferenceType,
            name="episode_of_care_diag_condition_reference_type",
        ),
        nullable=True,
    )
    condition_id = Column(BigInteger, nullable=True, index=True)
    condition_display = Column(String, nullable=True)

    # role (0..1 CodeableConcept)
    role_text = Column(String, nullable=True)

    # rank (0..1 positiveInt)
    rank = Column(Integer, nullable=True)

    episode_of_care = relationship("EpisodeOfCareModel", back_populates="diagnoses")
    role_codings = relationship(
        "EpisodeOfCareDiagnosisRoleCoding",
        back_populates="diagnosis",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class EpisodeOfCareDiagnosisRoleCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """EpisodeOfCare.diagnosis.role.coding (0..*) grandchild table."""

    __tablename__ = "episode_of_care_diagnosis_role_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    diagnosis_id = Column(
        BigInteger,
        ForeignKey("episode_of_care_diagnosis.id"),
        nullable=False,
        index=True,
    )

    diagnosis = relationship("EpisodeOfCareDiagnosis", back_populates="role_codings")
