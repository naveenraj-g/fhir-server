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
from app.models.encounter.enums import EncounterEpisodeOfCareReferenceType
from app.models.enums import IdentifierUse
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# episodeOfCare (0..*) Reference(EpisodeOfCare) child table
# ---------------------------------------------------------------------------


class EncounterEpisodeOfCare(TenantAuditMixin, Base):
    """episodeOfCare[] — the EpisodeOfCare(s) this encounter is part of.

    EpisodeOfCare is not a modeled resource in this system, so
    reference_identifier_* columns are in practice the only way to record
    one. The existence check is never attempted for this field.

    No UniqueConstraint on (encounter_pk, reference_type, reference_id):
    R4 doesn't forbid listing the same reference twice — a deployment
    that wants that as a rule expresses it as a profile-layer invariant,
    not a base constraint."""

    __tablename__ = "encounter_episode_of_care"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    encounter_pk = Column(
        BigInteger, ForeignKey("encounter.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            EncounterEpisodeOfCareReferenceType,
            name="encounter_episode_of_care_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use"), nullable=True
    )
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    encounter = relationship("EncounterModel", back_populates="episode_of_cares")
