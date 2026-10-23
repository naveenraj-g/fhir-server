from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    Enum,
    Sequence,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin
from app.schemas.enums import AdministrativeGender

practitioner_id_seq = Sequence(
    "practitioner_pub_seq", start=30000, increment=1, metadata=Base.metadata
)


class PractitionerModel(TenantAuditMixin, Base):
    """FHIR R4 Practitioner. No DB-level CHECK constraints — every R4 rule is
    enforced by the FHIR validator layer (base -> country -> profile chain),
    not by the database — same architecture choice as Organization/Location/
    HealthcareService, see OrganizationModel's docstring
    (app/models/organization/core.py) for the full reasoning.

    Unlike Organization/Location/HealthcareService, Practitioner keeps a
    plain `user_id` column alongside the JWT-derived `tenant_id`/
    `created_by`/`updated_by` (TenantAuditMixin) — a Practitioner record is
    naturally scoped to an individual end-user's own account (the
    clinician), unlike those three shared tenant-level entities. This
    mirrors this resource's own pre-existing documented behavior from before
    it was removed in the mass resource cleanup (see CLAUDE.md's
    Multi-Tenancy & Ownership section: "user_id is unchanged for Patient and
    Practitioner").
    """

    __tablename__ = "practitioner"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    practitioner_id = Column(
        BigInteger,
        practitioner_id_seq,
        server_default=practitioner_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    user_id = Column(String, nullable=True, index=True)

    # active (0..1) — R4 removed the R3 default of true; absent means
    # unknown, not false, so this has no default and is nullable.
    active = Column(Boolean, nullable=True)

    # gender (0..1 code, AdministrativeGender) — shared schema-layer enum,
    # same as every other resource's datatype-code columns (ContactPointSystem,
    # AddressUse, ...) — see app/schemas/enums.py, not a model-layer copy.
    gender = Column(Enum(AdministrativeGender, name="administrative_gender"), nullable=True)

    # birthDate (0..1 date) — FHIR `date`, not `dateTime`: no time-of-day,
    # no timezone. SQL DATE matches exactly.
    birth_date = Column(Date, nullable=True)

    # Resource-level extension support. Raw [{url, valueType, value}, ...];
    # validated against registered extension definitions by the
    # (not-yet-built) profile pipeline, not by the database. No explicit
    # ::jsonb cast — Postgres infers it from the column's own type in a
    # DEFAULT clause, and the explicit cast is invalid SQL on SQLite (the
    # test suite's engine), which has no cast syntax at all.
    extension = Column(JSONB, nullable=False, server_default=text("'[]'"))

    # Relationships
    identifiers = relationship(
        "PractitionerIdentifier",
        back_populates="practitioner",
        cascade="all, delete-orphan",
    )
    names = relationship(
        "PractitionerName", back_populates="practitioner", cascade="all, delete-orphan"
    )
    telecoms = relationship(
        "PractitionerTelecom",
        back_populates="practitioner",
        cascade="all, delete-orphan",
    )
    addresses = relationship(
        "PractitionerAddress",
        back_populates="practitioner",
        cascade="all, delete-orphan",
    )
    photos = relationship(
        "PractitionerPhoto", back_populates="practitioner", cascade="all, delete-orphan"
    )
    qualifications = relationship(
        "PractitionerQualification",
        back_populates="practitioner",
        cascade="all, delete-orphan",
    )
    communications = relationship(
        "PractitionerCommunication",
        back_populates="practitioner",
        cascade="all, delete-orphan",
    )
