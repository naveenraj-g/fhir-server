from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class GroupCharacteristic(TenantAuditMixin, Base):
    """Child table for Group.characteristic[]."""

    __tablename__ = "group_characteristic"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    group_pk = Column(
        BigInteger,
        ForeignKey("group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    code_text = Column(String, nullable=True)
    exclude = Column(Boolean, nullable=False, default=False)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # Choice value[x]
    value_boolean = Column(Boolean, nullable=True)
    value_codeable_concept_text = Column(String, nullable=True)
    value_quantity = Column(JSONB, nullable=True)
    value_range = Column(JSONB, nullable=True)
    value_reference_reference = Column(String, nullable=True)
    value_reference_type = Column(String, nullable=True)
    value_reference_id = Column(BigInteger, nullable=True)
    value_reference_display = Column(String, nullable=True)

    group = relationship("GroupModel", back_populates="characteristics")
    code_codings = relationship(
        "GroupCharacteristicCodeCoding",
        back_populates="characteristic",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    value_codeable_concept_codings = relationship(
        "GroupCharacteristicValueCoding",
        back_populates="characteristic",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class GroupCharacteristicCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Grandchild table for Group.characteristic[].code.coding[]."""

    __tablename__ = "group_characteristic_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    characteristic_id = Column(
        BigInteger,
        ForeignKey("group_characteristic.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    characteristic = relationship("GroupCharacteristic", back_populates="code_codings")


class GroupCharacteristicValueCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Grandchild table for Group.characteristic[].valueCodeableConcept.coding[]."""

    __tablename__ = "group_characteristic_value_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    characteristic_id = Column(
        BigInteger,
        ForeignKey("group_characteristic.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    characteristic = relationship("GroupCharacteristic", back_populates="value_codeable_concept_codings")
