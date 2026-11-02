from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.immunization.enums import ImmunizationReactionDetailReferenceType
from app.models.shared import TenantAuditMixin


class ImmunizationReactionModel(TenantAuditMixin, Base):
    """Immunization.reaction (0..* BackboneElement) child table."""

    __tablename__ = "immunization_reaction"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    immunization_pk = Column(
        BigInteger, ForeignKey("immunization.id"), nullable=False, index=True
    )

    date = Column(DateTime(timezone=True), nullable=True)
    reported = Column(Boolean, nullable=True)

    # detail (0..1 Reference(Observation))
    detail_reference = Column(String, nullable=True)
    detail_type = Column(
        Enum(
            ImmunizationReactionDetailReferenceType,
            name="immunization_reaction_detail_reference_type",
        ),
        nullable=True,
    )
    detail_id = Column(BigInteger, nullable=True, index=True)
    detail_display = Column(String, nullable=True)

    # detail.identifier fallback (11 columns)
    detail_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    detail_identifier_type_system = Column(String, nullable=True)
    detail_identifier_type_version = Column(String, nullable=True)
    detail_identifier_type_code = Column(String, nullable=True)
    detail_identifier_type_display = Column(String, nullable=True)
    detail_identifier_type_user_selected = Column(Boolean, nullable=True)
    detail_identifier_type_text = Column(String, nullable=True)
    detail_identifier_system = Column(String, nullable=True)
    detail_identifier_value = Column(String, nullable=True)
    detail_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    detail_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    immunization = relationship("ImmunizationModel", back_populates="reactions")
