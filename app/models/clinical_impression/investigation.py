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
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin


class ClinicalImpressionInvestigationModel(TenantAuditMixin, Base):
    """ClinicalImpression.investigation (0..* BackboneElement) child table."""

    __tablename__ = "clinical_impression_investigation"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    clinical_impression_pk = Column(
        BigInteger, ForeignKey("clinical_impression.id"), nullable=False, index=True
    )

    code_text = Column(String, nullable=True)

    clinical_impression = relationship(
        "ClinicalImpressionModel", back_populates="investigations"
    )
    code_codings = relationship(
        "ClinicalImpressionInvestigationCodeCodingModel",
        back_populates="investigation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    items = relationship(
        "ClinicalImpressionInvestigationItemModel",
        back_populates="investigation",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ClinicalImpressionInvestigationCodeCodingModel(FhirCodingMixin, TenantAuditMixin, Base):
    """clinical_impression_investigation.code.coding (0..* Coding) grandchild table."""

    __tablename__ = "clinical_impression_investigation_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    clinical_impression_investigation_id = Column(
        BigInteger,
        ForeignKey("clinical_impression_investigation.id"),
        nullable=False,
        index=True,
    )

    investigation = relationship(
        "ClinicalImpressionInvestigationModel", back_populates="code_codings"
    )


class ClinicalImpressionInvestigationItemModel(TenantAuditMixin, Base):
    """clinical_impression_investigation.item (0..* Reference(Any)) grandchild table."""

    __tablename__ = "clinical_impression_investigation_item"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    clinical_impression_investigation_id = Column(
        BigInteger,
        ForeignKey("clinical_impression_investigation.id"),
        nullable=False,
        index=True,
    )

    item_reference = Column(String, nullable=True)
    item_type = Column(String, nullable=True)
    item_id = Column(BigInteger, nullable=True, index=True)
    item_display = Column(String, nullable=True)

    # item.identifier fallback (11 columns)
    item_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    item_identifier_type_system = Column(String, nullable=True)
    item_identifier_type_version = Column(String, nullable=True)
    item_identifier_type_code = Column(String, nullable=True)
    item_identifier_type_display = Column(String, nullable=True)
    item_identifier_type_user_selected = Column(Boolean, nullable=True)
    item_identifier_type_text = Column(String, nullable=True)
    item_identifier_system = Column(String, nullable=True)
    item_identifier_value = Column(String, nullable=True)
    item_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    item_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    investigation = relationship(
        "ClinicalImpressionInvestigationModel", back_populates="items"
    )
