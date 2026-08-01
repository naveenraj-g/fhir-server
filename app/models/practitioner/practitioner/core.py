from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Integer,
    Sequence,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import FHIRBase as Base
from app.schemas.enums import AdministrativeGender

practitioner_id_seq = Sequence(
    "practitioner_pub_seq", start=30000, increment=1, metadata=Base.metadata
)


class PractitionerModel(Base):
    __tablename__ = "practitioner"
    __table_args__ = (
        UniqueConstraint("user_id", "org_id", name="uq_practitioner_user_id_org_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    practitioner_id = Column(
        Integer,
        practitioner_id_seq,
        server_default=practitioner_id_seq.next_value(),
        unique=True,
        index=True,
        nullable=False,
    )

    user_id = Column(String, nullable=True, index=True)
    org_id = Column(String, nullable=False, index=True)
    active = Column(Boolean, nullable=False, default=False)
    gender = Column(
        Enum(AdministrativeGender, name="administrative_gender"), nullable=False
    )
    birth_date = Column(Date, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(String, nullable=False)
    updated_by = Column(String, nullable=True)

    names = relationship(
        "PractitionerName", back_populates="practitioner", cascade="all, delete-orphan"
    )
    identifiers = relationship(
        "PractitionerIdentifier",
        back_populates="practitioner",
        cascade="all, delete-orphan",
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
