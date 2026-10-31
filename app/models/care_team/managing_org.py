from sqlalchemy import (
    BigInteger,
    Column,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.care_team.enums import CareTeamManagingOrganizationReferenceType
from app.models.shared import TenantAuditMixin


class CareTeamManagingOrganization(TenantAuditMixin, Base):
    """CareTeam.managingOrganization (0..*) child table."""

    __tablename__ = "care_team_managing_organization"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_team_pk = Column(
        BigInteger, ForeignKey("care_team.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            CareTeamManagingOrganizationReferenceType,
            name="care_team_managing_organization_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    care_team = relationship("CareTeamModel", back_populates="managing_organizations")
