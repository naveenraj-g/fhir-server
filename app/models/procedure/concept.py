from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ProcedureReasonCode(TenantAuditMixin, Base):
    """Procedure.reasonCode (0..* CodeableConcept) child table."""

    __tablename__ = "procedure_reason_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    procedure_pk = Column(
        BigInteger, ForeignKey("procedure.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    procedure = relationship("ProcedureModel", back_populates="reason_codes")
    codings = relationship(
        "ProcedureReasonCodeCoding",
        back_populates="reason_code",
        cascade="all, delete-orphan",
    )


class ProcedureReasonCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Procedure.reasonCode.coding (0..* Coding) grandchild table."""

    __tablename__ = "procedure_reason_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    reason_code_id = Column(
        BigInteger,
        ForeignKey("procedure_reason_code.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    reason_code = relationship("ProcedureReasonCode", back_populates="codings")


class ProcedureBodySite(TenantAuditMixin, Base):
    """Procedure.bodySite (0..* CodeableConcept) child table."""

    __tablename__ = "procedure_body_site"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    procedure_pk = Column(
        BigInteger, ForeignKey("procedure.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    procedure = relationship("ProcedureModel", back_populates="body_sites")
    codings = relationship(
        "ProcedureBodySiteCoding",
        back_populates="body_site",
        cascade="all, delete-orphan",
    )


class ProcedureBodySiteCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Procedure.bodySite.coding (0..* Coding) grandchild table."""

    __tablename__ = "procedure_body_site_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    body_site_id = Column(
        BigInteger,
        ForeignKey("procedure_body_site.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    body_site = relationship("ProcedureBodySite", back_populates="codings")


class ProcedureComplication(TenantAuditMixin, Base):
    """Procedure.complication (0..* CodeableConcept) child table."""

    __tablename__ = "procedure_complication"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    procedure_pk = Column(
        BigInteger, ForeignKey("procedure.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    procedure = relationship("ProcedureModel", back_populates="complications")
    codings = relationship(
        "ProcedureComplicationCoding",
        back_populates="complication",
        cascade="all, delete-orphan",
    )


class ProcedureComplicationCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Procedure.complication.coding (0..* Coding) grandchild table."""

    __tablename__ = "procedure_complication_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    complication_id = Column(
        BigInteger,
        ForeignKey("procedure_complication.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    complication = relationship("ProcedureComplication", back_populates="codings")


class ProcedureFollowUp(TenantAuditMixin, Base):
    """Procedure.followUp (0..* CodeableConcept) child table."""

    __tablename__ = "procedure_follow_up"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    procedure_pk = Column(
        BigInteger, ForeignKey("procedure.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    procedure = relationship("ProcedureModel", back_populates="follow_ups")
    codings = relationship(
        "ProcedureFollowUpCoding",
        back_populates="follow_up",
        cascade="all, delete-orphan",
    )


class ProcedureFollowUpCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Procedure.followUp.coding (0..* Coding) grandchild table."""

    __tablename__ = "procedure_follow_up_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    follow_up_id = Column(
        BigInteger,
        ForeignKey("procedure_follow_up.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    follow_up = relationship("ProcedureFollowUp", back_populates="codings")


class ProcedureUsedCode(TenantAuditMixin, Base):
    """Procedure.usedCode (0..* CodeableConcept) child table."""

    __tablename__ = "procedure_used_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    procedure_pk = Column(
        BigInteger, ForeignKey("procedure.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    procedure = relationship("ProcedureModel", back_populates="used_codes")
    codings = relationship(
        "ProcedureUsedCodeCoding",
        back_populates="used_code",
        cascade="all, delete-orphan",
    )


class ProcedureUsedCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Procedure.usedCode.coding (0..* Coding) grandchild table."""

    __tablename__ = "procedure_used_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    used_code_id = Column(
        BigInteger,
        ForeignKey("procedure_used_code.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    used_code = relationship("ProcedureUsedCode", back_populates="codings")
