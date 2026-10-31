from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class SpecimenCollectionMethodCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Specimen.collection.method.coding (0..*)."""

    __tablename__ = "specimen_collection_method_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_pk = Column(
        BigInteger, ForeignKey("specimen.id"), nullable=False, index=True
    )

    specimen = relationship("SpecimenModel", back_populates="collection_method_codings")


class SpecimenCollectionBodySiteCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Specimen.collection.bodySite.coding (0..*)."""

    __tablename__ = "specimen_collection_body_site_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_pk = Column(
        BigInteger, ForeignKey("specimen.id"), nullable=False, index=True
    )

    specimen = relationship("SpecimenModel", back_populates="collection_body_site_codings")


class SpecimenCollectionFastingStatusCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Specimen.collection.fastingStatusCodeableConcept.coding (0..*)."""

    __tablename__ = "specimen_collection_fasting_status_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_pk = Column(
        BigInteger, ForeignKey("specimen.id"), nullable=False, index=True
    )

    specimen = relationship("SpecimenModel", back_populates="collection_fasting_status_codings")
