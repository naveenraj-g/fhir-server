from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class FlagCategory(TenantAuditMixin, Base):
    """Flag.category (0..*) child table for CodeableConcept entries."""

    __tablename__ = "flag_category"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    flag_pk = Column(
        BigInteger, ForeignKey("flag.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    flag = relationship("FlagModel", back_populates="categories")
    codings = relationship(
        "FlagCategoryCoding",
        back_populates="category",
        cascade="all, delete-orphan",
    )


class FlagCategoryCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Flag.category.coding (0..*)."""

    __tablename__ = "flag_category_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    flag_category_id = Column(
        BigInteger,
        ForeignKey("flag_category.id"),
        nullable=False,
        index=True,
    )

    category = relationship("FlagCategory", back_populates="codings")
