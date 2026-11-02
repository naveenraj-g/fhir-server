from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin

from .enums import ClinicalImpressionFindingReferenceType


class ClinicalImpressionFindingModel(TenantAuditMixin, Base):
    """ClinicalImpression.finding (0..* BackboneElement) child table."""

    __tablename__ = "clinical_impression_finding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    clinical_impression_pk = Column(
        BigInteger, ForeignKey("clinical_impression.id"), nullable=False, index=True
    )

    # itemCodeableConcept (0..1 CodeableConcept)
    item_codeable_concept_text = Column(String, nullable=True)

    # itemReference (0..1 Reference(Condition | Observation | Media))
    item_reference = Column(String, nullable=True)
    item_reference_type = Column(
        Enum(
            ClinicalImpressionFindingReferenceType,
            name="clinical_impression_finding_reference_type",
        ),
        nullable=True,
    )
    item_reference_id = Column(BigInteger, nullable=True, index=True)
    item_reference_display = Column(String, nullable=True)

    # itemReference.identifier fallback (11 columns)
    item_reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    item_reference_identifier_type_system = Column(String, nullable=True)
    item_reference_identifier_type_version = Column(String, nullable=True)
    item_reference_identifier_type_code = Column(String, nullable=True)
    item_reference_identifier_type_display = Column(String, nullable=True)
    item_reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    item_reference_identifier_type_text = Column(String, nullable=True)
    item_reference_identifier_system = Column(String, nullable=True)
    item_reference_identifier_value = Column(String, nullable=True)
    item_reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    item_reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    # basis (0..1 string)
    basis = Column(Text, nullable=True)

    clinical_impression = relationship(
        "ClinicalImpressionModel", back_populates="findings"
    )
    item_codings = relationship(
        "ClinicalImpressionFindingItemCodingModel",
        back_populates="finding",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ClinicalImpressionFindingItemCodingModel(FhirCodingMixin, TenantAuditMixin, Base):
    """clinical_impression_finding.itemCodeableConcept.coding (0..* Coding) grandchild table."""

    __tablename__ = "clinical_impression_finding_item_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    clinical_impression_finding_id = Column(
        BigInteger,
        ForeignKey("clinical_impression_finding.id"),
        nullable=False,
        index=True,
    )

    finding = relationship(
        "ClinicalImpressionFindingModel", back_populates="item_codings"
    )
