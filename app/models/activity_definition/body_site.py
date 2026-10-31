from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ActivityDefinitionBodySite(TenantAuditMixin, Base):
    """ActivityDefinition.bodySite (0..* CodeableConcept) child table."""

    __tablename__ = "activity_definition_body_site"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_pk = Column(
        BigInteger, ForeignKey("activity_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    activity_definition = relationship("ActivityDefinitionModel", back_populates="body_sites")
    codings = relationship(
        "ActivityDefinitionBodySiteCoding",
        back_populates="body_site",
        cascade="all, delete-orphan",
    )


class ActivityDefinitionBodySiteCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """ActivityDefinition.bodySite.coding (0..*) grandchild table."""

    __tablename__ = "activity_definition_body_site_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_body_site_id = Column(
        BigInteger,
        ForeignKey("activity_definition_body_site.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    body_site = relationship("ActivityDefinitionBodySite", back_populates="codings")
