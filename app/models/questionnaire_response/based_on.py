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
from app.models.questionnaire_response.enums import QuestionnaireResponseBasedOnReferenceType
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# basedOn (0..*) Reference(CarePlan|ServiceRequest) child table
# ---------------------------------------------------------------------------


class QuestionnaireResponseBasedOn(TenantAuditMixin, Base):
    """basedOn[] — a plan, proposal, or order fulfilled in whole or in part
    by this QuestionnaireResponse.

    Neither CarePlan nor ServiceRequest is a modeled resource in this
    system, so reference_identifier_* columns are in practice the only
    way to record one — same situation as AppointmentReasonReference /
    AppointmentBasedOn. The existence check is never attempted for this
    field.

    No UniqueConstraint on (questionnaire_response_pk, reference_type,
    reference_id): R4 doesn't forbid listing the same reference twice — a
    deployment that wants that as a rule expresses it as a profile-layer
    invariant, not a base constraint."""

    __tablename__ = "questionnaire_response_based_on"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    questionnaire_response_pk = Column(
        BigInteger, ForeignKey("questionnaire_response.id"), nullable=False, index=True
    )

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            QuestionnaireResponseBasedOnReferenceType,
            name="questionnaire_response_based_on_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    reference_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
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

    questionnaire_response = relationship("QuestionnaireResponseModel", back_populates="based_ons")
