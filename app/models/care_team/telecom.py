from sqlalchemy import (
    BigInteger,
    Column,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirContactPointMixin, TenantAuditMixin


class CareTeamTelecom(FhirContactPointMixin, TenantAuditMixin, Base):
    """CareTeam.telecom (0..*) ContactPoint child table."""

    __tablename__ = "care_team_telecom"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    care_team_pk = Column(
        BigInteger, ForeignKey("care_team.id"), nullable=False, index=True
    )

    care_team = relationship("CareTeamModel", back_populates="telecoms")
