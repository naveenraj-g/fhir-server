from sqlalchemy import BigInteger, Column, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.shared import TenantAuditMixin
from app.models.specimen.enums import SpecimenParentReferenceType


class SpecimenParent(TenantAuditMixin, Base):
    """One entry of Specimen.parent (0..* Reference(Specimen))."""

    __tablename__ = "specimen_parent"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_pk = Column(
        BigInteger, ForeignKey("specimen.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            SpecimenParentReferenceType,
            name="specimen_parent_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    # Reference identifier fallback
    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)

    specimen = relationship("SpecimenModel", back_populates="parents")
