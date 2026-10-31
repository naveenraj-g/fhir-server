from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class SpecimenTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Specimen.type.coding (0..*)."""

    __tablename__ = "specimen_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_pk = Column(
        BigInteger, ForeignKey("specimen.id"), nullable=False, index=True
    )

    specimen = relationship("SpecimenModel", back_populates="type_codings")
