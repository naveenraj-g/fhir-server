from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    ForeignKey,
    Integer,
    String,
    Time,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# item.answerOption (0..*) grandchild table
# ---------------------------------------------------------------------------


class QuestionnaireItemAnswerOption(FhirCodingMixin, TenantAuditMixin, Base):
    """Questionnaire.item.answerOption (0..*) —
    https://www.hl7.org/fhir/R4/questionnaire-definitions.html#Questionnaire.item.answerOption

    `value[x]` (1..1, choice of integer|date|time|string|Coding|
    Reference(Any)) — one column group per variant. The Coding variant
    uses this table's own FhirCodingMixin columns, prefixed `value_coding_`
    since they share the row with the other variant groups."""

    __tablename__ = "questionnaire_item_answer_option"

    _coding_prefix = "value_coding_"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    questionnaire_item_id = Column(
        BigInteger, ForeignKey("questionnaire_item.id"), nullable=False, index=True
    )

    value_integer = Column(Integer, nullable=True)
    value_date = Column(Date, nullable=True)
    value_time = Column(Time, nullable=True)
    value_string = Column(String, nullable=True)
    # value_coding_* (system/version/code/display/user_selected) provided
    # by FhirCodingMixin above, via _coding_prefix.
    value_reference_reference = Column(String, nullable=True)
    value_reference_type = Column(String, nullable=True)
    value_reference_id = Column(BigInteger, nullable=True, index=True)
    value_reference_display = Column(String, nullable=True)

    initial_selected = Column(Boolean, nullable=True)

    item = relationship("QuestionnaireItem", back_populates="answer_options")
