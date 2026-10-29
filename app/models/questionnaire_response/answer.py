from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Time,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.questionnaire_response.enums import QuestionnaireResponseQuantityComparator
from app.models.shared import FhirAttachmentMixin, FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# item.answer (0..*) — mutually recursive with item (see
# QuestionnaireResponseItem's docstring for the full shape)
# ---------------------------------------------------------------------------


class QuestionnaireResponseAnswer(FhirCodingMixin, FhirAttachmentMixin, TenantAuditMixin, Base):
    """QuestionnaireResponse.item.answer (0..*) —
    https://www.hl7.org/fhir/R4/questionnaireresponse-definitions.html#QuestionnaireResponse.item.answer

    `value[x]` (0..1, choice of boolean|decimal|integer|date|dateTime|
    time|string|uri|Attachment|Coding|Quantity|Reference(Any)) — the same
    12-variant shape as Questionnaire.item.initial's own value[x]; one
    column group per variant, Coding/Attachment via this table's own
    mixins (prefixed, since they share the row with every other variant
    group). `value_reference_*` is a plain String type column
    (Reference(Any) — no identifier fallback, mirroring
    QuestionnaireItemInitial's own value_reference exactly, since this is
    one variant among twelve crammed onto a single row rather than a
    dedicated top-level Reference field).

    `item_id` is a real, required FK — every answer belongs to exactly
    one item. `questionnaire_response_pk` is denormalized straight back
    to the root, same trick as every other table in this resource.
    `item` (0..*, recursive) may nest under a *specific answer* instead of
    directly under the parent item — see QuestionnaireResponseItem's
    `parent_answer_id` and its docstring for why that column is NOT a
    real FK even though this one (the other direction of the same
    relationship) is.
    """

    __tablename__ = "questionnaire_response_answer"

    _coding_prefix = "value_coding_"
    _attachment_prefix = "value_attachment_"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    questionnaire_response_pk = Column(
        BigInteger, ForeignKey("questionnaire_response.id"), nullable=False, index=True
    )
    item_id = Column(
        BigInteger, ForeignKey("questionnaire_response_item.id"), nullable=False, index=True
    )

    value_boolean = Column(Boolean, nullable=True)
    value_decimal = Column(Numeric, nullable=True)
    value_integer = Column(Integer, nullable=True)
    value_date = Column(Date, nullable=True)
    value_date_time = Column(DateTime(timezone=True), nullable=True)
    value_time = Column(Time, nullable=True)
    value_string = Column(String, nullable=True)
    value_uri = Column(String, nullable=True)
    # value_attachment_* (content_type/language/data/url/size/hash/title/
    # creation) provided by FhirAttachmentMixin above, via _attachment_prefix.
    # value_coding_* (system/version/code/display/user_selected) provided
    # by FhirCodingMixin above, via _coding_prefix.
    value_quantity_value = Column(Numeric, nullable=True)
    value_quantity_comparator = Column(
        Enum(
            QuestionnaireResponseQuantityComparator,
            name="questionnaire_response_quantity_comparator",
        ),
        nullable=True,
    )
    value_quantity_unit = Column(String, nullable=True)
    value_quantity_system = Column(String, nullable=True)
    value_quantity_code = Column(String, nullable=True)
    value_reference_reference = Column(String, nullable=True)
    value_reference_type = Column(String, nullable=True)
    value_reference_id = Column(BigInteger, nullable=True, index=True)
    value_reference_display = Column(String, nullable=True)

    questionnaire_response = relationship("QuestionnaireResponseModel", back_populates="answers")
    item = relationship(
        "QuestionnaireResponseItem", back_populates="answers", foreign_keys=[item_id]
    )
