from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    Sequence,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.flag.enums import (
    FlagAuthorReferenceType,
    FlagEncounterReferenceType,
    FlagStatus,
    FlagSubjectReferenceType,
)
from app.models.shared import TenantAuditMixin


class FlagModel(TenantAuditMixin, Base):
    """SQLAlchemy ORM model for FHIR R4 Flag resource.

    Prospective warnings of potential issues when providing care to the patient.
    Sequenced public ID block starts at 450000 (flag_pub_seq).
    There is deliberately no user_id: Flag is an org-scoped clinical entity,
    associated with a subject, not scoped to an individual system user.
    """

    __tablename__ = "flag"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    flag_id = Column(
        BigInteger,
        Sequence(
            "flag_pub_seq",
            start=450000,
            increment=1,
            metadata=Base.metadata,
        ),
        unique=True,
        index=True,
        nullable=False,
    )

    # status (1..1 code, binding: flag-status)
    status = Column(
        Enum(
            FlagStatus,
            name="flag_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )

    # code (1..1 CodeableConcept) — code_text stored flat, codings in flag_code_coding
    code_text = Column(String, nullable=True)

    # subject (1..1 Reference(Patient|Location|Group|Organization|Practitioner|PlanDefinition|Medication|Procedure))
    subject_reference = Column(String, nullable=False)
    subject_type = Column(
        Enum(FlagSubjectReferenceType, name="flag_subject_reference_type"),
        nullable=False,
    )
    subject_id = Column(BigInteger, nullable=True, index=True)
    subject_display = Column(String, nullable=True)

    # period (0..1 Period)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # encounter (0..1 Reference(Encounter))
    encounter_reference = Column(String, nullable=True)
    encounter_type = Column(
        Enum(FlagEncounterReferenceType, name="flag_encounter_reference_type"),
        nullable=True,
    )
    encounter_id = Column(BigInteger, nullable=True, index=True)
    encounter_display = Column(String, nullable=True)

    # author (0..1 Reference(Device|Organization|Patient|Practitioner|PractitionerRole))
    author_reference = Column(String, nullable=True)
    author_type = Column(
        Enum(FlagAuthorReferenceType, name="flag_author_reference_type"),
        nullable=True,
    )
    author_id = Column(BigInteger, nullable=True, index=True)
    author_display = Column(String, nullable=True)

    # extension (0..* Extension, JSONB)
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # Relationships
    identifiers = relationship(
        "FlagIdentifier",
        back_populates="flag",
        cascade="all, delete-orphan",
    )
    categories = relationship(
        "FlagCategory",
        back_populates="flag",
        cascade="all, delete-orphan",
    )
    code_codings = relationship(
        "FlagCodeCoding",
        back_populates="flag",
        cascade="all, delete-orphan",
    )
