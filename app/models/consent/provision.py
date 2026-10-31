from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.consent.enums import (
    ConsentDataMeaning,
    ConsentProvisionActorReferenceType,
    ConsentProvisionType,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ConsentProvision(TenantAuditMixin, Base):
    """Consent.provision (0..1 BackboneElement, can contain nested provisions) child table."""

    __tablename__ = "consent_provision"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    consent_pk = Column(
        BigInteger, ForeignKey("consent.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_provision_id = Column(
        BigInteger,
        ForeignKey("consent_provision.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    type = Column(
        Enum(
            ConsentProvisionType,
            name="consent_provision_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)
    data_period_start = Column(DateTime(timezone=True), nullable=True)
    data_period_end = Column(DateTime(timezone=True), nullable=True)

    consent = relationship("ConsentModel", back_populates="provisions")
    sub_provisions = relationship(
        "ConsentProvision",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    actors = relationship(
        "ConsentProvisionActor",
        back_populates="provision",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    actions = relationship(
        "ConsentProvisionAction",
        back_populates="provision",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    security_labels = relationship(
        "ConsentProvisionSecurityLabel",
        back_populates="provision",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    purposes = relationship(
        "ConsentProvisionPurpose",
        back_populates="provision",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    classes = relationship(
        "ConsentProvisionClass",
        back_populates="provision",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    codes = relationship(
        "ConsentProvisionCode",
        back_populates="provision",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    data_entries = relationship(
        "ConsentProvisionData",
        back_populates="provision",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ConsentProvisionActor(TenantAuditMixin, Base):
    """Consent.provision.actor (0..* BackboneElement) child table."""

    __tablename__ = "consent_provision_actor"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    provision_id = Column(
        BigInteger,
        ForeignKey("consent_provision.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role_text = Column(String, nullable=True)
    reference_reference = Column(String, nullable=False)
    reference_type = Column(
        Enum(
            ConsentProvisionActorReferenceType,
            name="consent_provision_actor_reference_type",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True)
    reference_display = Column(String, nullable=True)

    provision = relationship("ConsentProvision", back_populates="actors")
    role_codings = relationship(
        "ConsentProvisionActorRoleCoding",
        back_populates="actor",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ConsentProvisionActorRoleCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Consent.provision.actor.role.coding (0..* Coding) grandchild table."""

    __tablename__ = "consent_provision_actor_role_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    provision_actor_id = Column(
        BigInteger,
        ForeignKey("consent_provision_actor.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    actor = relationship("ConsentProvisionActor", back_populates="role_codings")


class ConsentProvisionAction(TenantAuditMixin, Base):
    """Consent.provision.action (0..* CodeableConcept) child table."""

    __tablename__ = "consent_provision_action"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    provision_id = Column(
        BigInteger,
        ForeignKey("consent_provision.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    text = Column(String, nullable=True)

    provision = relationship("ConsentProvision", back_populates="actions")
    codings = relationship(
        "ConsentProvisionActionCoding",
        back_populates="action",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ConsentProvisionActionCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Consent.provision.action.coding (0..* Coding) grandchild table."""

    __tablename__ = "consent_provision_action_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    action_id = Column(
        BigInteger,
        ForeignKey("consent_provision_action.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    action = relationship("ConsentProvisionAction", back_populates="codings")


class ConsentProvisionSecurityLabel(FhirCodingMixin, TenantAuditMixin, Base):
    """Consent.provision.securityLabel (0..* Coding) child table."""

    __tablename__ = "consent_provision_security_label"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    provision_id = Column(
        BigInteger,
        ForeignKey("consent_provision.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    provision = relationship("ConsentProvision", back_populates="security_labels")


class ConsentProvisionPurpose(FhirCodingMixin, TenantAuditMixin, Base):
    """Consent.provision.purpose (0..* Coding) child table."""

    __tablename__ = "consent_provision_purpose"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    provision_id = Column(
        BigInteger,
        ForeignKey("consent_provision.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    provision = relationship("ConsentProvision", back_populates="purposes")


class ConsentProvisionClass(FhirCodingMixin, TenantAuditMixin, Base):
    """Consent.provision.class (0..* Coding) child table."""

    __tablename__ = "consent_provision_class"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    provision_id = Column(
        BigInteger,
        ForeignKey("consent_provision.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    provision = relationship("ConsentProvision", back_populates="classes")


class ConsentProvisionCode(TenantAuditMixin, Base):
    """Consent.provision.code (0..* CodeableConcept) child table."""

    __tablename__ = "consent_provision_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    provision_id = Column(
        BigInteger,
        ForeignKey("consent_provision.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    text = Column(String, nullable=True)

    provision = relationship("ConsentProvision", back_populates="codes")
    codings = relationship(
        "ConsentProvisionCodeCoding",
        back_populates="provision_code",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ConsentProvisionCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Consent.provision.code.coding (0..* Coding) grandchild table."""

    __tablename__ = "consent_provision_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code_id = Column(
        BigInteger,
        ForeignKey("consent_provision_code.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    provision_code = relationship("ConsentProvisionCode", back_populates="codings")


class ConsentProvisionData(TenantAuditMixin, Base):
    """Consent.provision.data (0..* BackboneElement) child table."""

    __tablename__ = "consent_provision_data"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    provision_id = Column(
        BigInteger,
        ForeignKey("consent_provision.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    meaning = Column(
        Enum(
            ConsentDataMeaning,
            name="consent_data_meaning",
            values_callable=lambda enum_cls: [m.value for m in enum_cls],
        ),
        nullable=False,
    )
    reference_reference = Column(String, nullable=False)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_display = Column(String, nullable=True)

    provision = relationship("ConsentProvision", back_populates="data_entries")
