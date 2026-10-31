from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import OrganizationReferenceType
from app.models.procedure.enums import ProcedurePerformerActorReferenceType
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ProcedurePerformer(TenantAuditMixin, Base):
    """Procedure.performer (0..* BackboneElement) child table."""

    __tablename__ = "procedure_performer"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    procedure_pk = Column(
        BigInteger, ForeignKey("procedure.id", ondelete="CASCADE"), nullable=False, index=True
    )

    function_text = Column(String, nullable=True)

    actor_reference = Column(String, nullable=True)
    actor_type = Column(
        Enum(
            ProcedurePerformerActorReferenceType,
            name="procedure_performer_actor_reference_type",
        ),
        nullable=False,
    )
    actor_id = Column(BigInteger, nullable=True, index=True)
    actor_display = Column(String, nullable=True)

    on_behalf_of_reference = Column(String, nullable=True)
    on_behalf_of_type = Column(
        Enum(
            OrganizationReferenceType,
            name="organization_reference_type",
            create_type=False,
        ),
        nullable=True,
    )
    on_behalf_of_id = Column(BigInteger, nullable=True, index=True)
    on_behalf_of_display = Column(String, nullable=True)

    procedure = relationship("ProcedureModel", back_populates="performers")
    function_codings = relationship(
        "ProcedurePerformerFunctionCoding",
        back_populates="performer",
        cascade="all, delete-orphan",
    )


class ProcedurePerformerFunctionCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Procedure.performer.function.coding (0..* Coding) grandchild table."""

    __tablename__ = "procedure_performer_function_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    performer_id = Column(
        BigInteger,
        ForeignKey("procedure_performer.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    performer = relationship("ProcedurePerformer", back_populates="function_codings")
