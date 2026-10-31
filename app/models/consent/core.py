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
from app.models.consent.enums import (
    ConsentPatientReferenceType,
    ConsentSourceReferenceType,
    ConsentStatus,
)
from app.models.shared import TenantAuditMixin


class ConsentModel(TenantAuditMixin, Base):
    """SQLAlchemy ORM model for FHIR R4 Consent resource."""

    __tablename__ = "consent"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    consent_id = Column(
        BigInteger,
        Sequence(
            "consent_pub_seq",
            start=440000,
            increment=1,
            metadata=Base.metadata,
        ),
        unique=True,
        index=True,
        nullable=False,
    )

    status = Column(
        Enum(
            ConsentStatus,
            name="consent_status",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )
    scope_text = Column(String, nullable=True)

    patient_reference = Column(String, nullable=True)
    patient_type = Column(
        Enum(
            ConsentPatientReferenceType,
            name="consent_patient_reference_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )
    patient_id = Column(BigInteger, nullable=True)
    patient_display = Column(String, nullable=True)

    date_time = Column(DateTime(timezone=True), nullable=True)

    # Choice source[x]: sourceAttachment vs sourceReference
    source_reference_reference = Column(String, nullable=True)
    source_reference_type = Column(
        Enum(
            ConsentSourceReferenceType,
            name="consent_source_reference_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )
    source_reference_id = Column(BigInteger, nullable=True)
    source_reference_display = Column(String, nullable=True)
    source_attachment = Column(JSONB, nullable=True)

    policy_rule_text = Column(String, nullable=True)

    extension = Column(JSONB, nullable=False, server_default="[]")

    # Relationships
    identifiers = relationship(
        "ConsentIdentifier",
        back_populates="consent",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    scope_codings = relationship(
        "ConsentScopeCoding",
        back_populates="consent",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    categories = relationship(
        "ConsentCategory",
        back_populates="consent",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    performers = relationship(
        "ConsentPerformer",
        back_populates="consent",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    organizations = relationship(
        "ConsentOrganization",
        back_populates="consent",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    policies = relationship(
        "ConsentPolicy",
        back_populates="consent",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    policy_rule_codings = relationship(
        "ConsentPolicyRuleCoding",
        back_populates="consent",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    verifications = relationship(
        "ConsentVerification",
        back_populates="consent",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    provisions = relationship(
        "ConsentProvision",
        back_populates="consent",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
