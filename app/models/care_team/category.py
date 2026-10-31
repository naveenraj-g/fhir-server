from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class CareTeamCategory(TenantAuditMixin, Base):
    """CareTeam.category (0..*) child table."""

    __tablename__ = "care_team_category"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_team_pk = Column(
        BigInteger, ForeignKey("care_team.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    care_team = relationship("CareTeamModel", back_populates="categories")
    codings = relationship(
        "CareTeamCategoryCoding",
        back_populates="category",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class CareTeamCategoryCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """CareTeam.category.coding (0..*) grandchild table."""

    __tablename__ = "care_team_category_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    category_id = Column(
        BigInteger,
        ForeignKey("care_team_category.id"),
        nullable=False,
        index=True,
    )

    category = relationship("CareTeamCategory", back_populates="codings")
