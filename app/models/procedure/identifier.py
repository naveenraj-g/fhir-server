from sqlalchemy import BigInteger, Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ProcedureIdentifier(TenantAuditMixin, Base):
    """Procedure.identifier (0..* Identifier) child table."""

    __tablename__ = "procedure_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    procedure_pk = Column(
        BigInteger, ForeignKey("procedure.id", ondelete="CASCADE"), nullable=False, index=True
    )

    use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False),
        nullable=True,
    )
    type_text = Column(String, nullable=True)
    system = Column(String, nullable=True)
    value = Column(String, nullable=True)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    assigner_reference = Column(String, nullable=True)
    assigner_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    assigner_id = Column(BigInteger, nullable=True, index=True)
    assigner_display = Column(String, nullable=True)

    procedure = relationship("ProcedureModel", back_populates="identifiers")
    type_codings = relationship(
        "ProcedureIdentifierTypeCoding",
        back_populates="identifier",
        cascade="all, delete-orphan",
    )


class ProcedureIdentifierTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Procedure.identifier.type.coding (0..* Coding) grandchild table."""

    __tablename__ = "procedure_identifier_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    identifier_id = Column(
        BigInteger,
        ForeignKey("procedure_identifier.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    identifier = relationship("ProcedureIdentifier", back_populates="type_codings")
