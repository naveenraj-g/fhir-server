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
from app.models.questionnaire.enums import QuestionnaireQuantityComparator
from app.models.shared import FhirAttachmentMixin, FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# item.initial (0..*) grandchild table
# ---------------------------------------------------------------------------


class QuestionnaireItemInitial(FhirCodingMixin, FhirAttachmentMixin, TenantAuditMixin, Base):
    """Questionnaire.item.initial (0..*) —
    https://www.hl7.org/fhir/R4/questionnaire-definitions.html#Questionnaire.item.initial

    `value[x]` (1..1, choice of boolean|decimal|integer|date|dateTime|time|
    string|uri|Attachment|Coding|Quantity|Reference(Any)) — the most
    polymorphic choice type in this codebase; one column group per
    variant. Coding uses FhirCodingMixin prefixed `value_coding_`;
    Attachment uses FhirAttachmentMixin prefixed `value_attachment_` —
    combining two different Fhir*Mixin types on one row is fine (no
    attribute-name collision between them), only one mixin *per type* is
    the actual constraint (see CLAUDE.md's FHIR DB Model Design Step 5).
    """

    __tablename__ = "questionnaire_item_initial"

    _coding_prefix = "value_coding_"
    _attachment_prefix = "value_attachment_"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    questionnaire_item_id = Column(
        BigInteger, ForeignKey("questionnaire_item.id"), nullable=False, index=True
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
            QuestionnaireQuantityComparator,
            name="questionnaire_quantity_comparator",
            create_type=False,
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

    item = relationship("QuestionnaireItem", back_populates="initials")
