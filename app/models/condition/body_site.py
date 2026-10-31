from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ConditionBodySite(TenantAuditMixin, Base):
    """One entry of Condition.bodySite (0..* CodeableConcept)."""

    __tablename__ = "condition_body_site"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    condition_pk = Column(
        BigInteger, ForeignKey("condition.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    condition = relationship("ConditionModel", back_populates="body_sites")
    codings = relationship(
        "ConditionBodySiteCoding",
        back_populates="body_site",
        cascade="all, delete-orphan",
    )


class ConditionBodySiteCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Condition.bodySite.coding (0..*)."""

    __tablename__ = "condition_body_site_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    condition_body_site_id = Column(
        BigInteger, ForeignKey("condition_body_site.id"), nullable=False, index=True
    )

    body_site = relationship("ConditionBodySite", back_populates="codings")
