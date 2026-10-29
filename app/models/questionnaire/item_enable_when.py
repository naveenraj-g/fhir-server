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
from app.models.questionnaire.enums import (
    QuestionnaireItemOperator,
    QuestionnaireQuantityComparator,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# item.enableWhen (0..*) grandchild table
# ---------------------------------------------------------------------------


class QuestionnaireItemEnableWhen(FhirCodingMixin, TenantAuditMixin, Base):
    """Questionnaire.item.enableWhen (0..*) —
    https://www.hl7.org/fhir/R4/questionnaire-definitions.html#Questionnaire.item.enableWhen

    `answer[x]` (1..1, choice of boolean|decimal|integer|date|dateTime|
    time|string|Coding|Quantity|Reference(Any)) — one column group per
    variant, all nullable; the mapper picks whichever is populated. The
    Coding variant uses this table's own FhirCodingMixin columns, prefixed
    `answer_coding_` since they share the row with every other variant
    group (bare `system`/`code`/... would otherwise collide in meaning
    with a hypothetical un-prefixed use). `answer_reference_*` uses a
    plain String type column (Reference(Any) — see CLAUDE.md's
    Reference(Any) invariant), not an Enum.
    """

    __tablename__ = "questionnaire_item_enable_when"

    _coding_prefix = "answer_coding_"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    questionnaire_item_id = Column(
        BigInteger, ForeignKey("questionnaire_item.id"), nullable=False, index=True
    )

    question = Column(String, nullable=False)
    operator = Column(
        Enum(QuestionnaireItemOperator, name="questionnaire_item_operator"),
        nullable=False,
    )

    answer_boolean = Column(Boolean, nullable=True)
    answer_decimal = Column(Numeric, nullable=True)
    answer_integer = Column(Integer, nullable=True)
    answer_date = Column(Date, nullable=True)
    answer_date_time = Column(DateTime(timezone=True), nullable=True)
    answer_time = Column(Time, nullable=True)
    answer_string = Column(String, nullable=True)
    # answer_coding_* (system/version/code/display/user_selected) provided
    # by FhirCodingMixin above, via _coding_prefix.
    answer_quantity_value = Column(Numeric, nullable=True)
    answer_quantity_comparator = Column(
        Enum(
            QuestionnaireQuantityComparator,
            name="questionnaire_quantity_comparator",
            create_type=False,
        ),
        nullable=True,
    )
    answer_quantity_unit = Column(String, nullable=True)
    answer_quantity_system = Column(String, nullable=True)
    answer_quantity_code = Column(String, nullable=True)
    answer_reference_reference = Column(String, nullable=True)
    answer_reference_type = Column(String, nullable=True)
    answer_reference_id = Column(BigInteger, nullable=True, index=True)
    answer_reference_display = Column(String, nullable=True)

    item = relationship("QuestionnaireItem", back_populates="enable_whens")
