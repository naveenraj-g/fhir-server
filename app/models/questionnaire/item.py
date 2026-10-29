from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.questionnaire.enums import (
    QuestionnaireEnableBehavior,
    QuestionnaireItemType,
)
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# item (0..*, recursive BackboneElement)
# ---------------------------------------------------------------------------


class QuestionnaireItem(TenantAuditMixin, Base):
    """Questionnaire.item (0..*, recursive — item.item nests to unbounded
    depth) — https://www.hl7.org/fhir/R4/questionnaire.html#Questionnaire.item

    See QuestionnaireModel's own docstring for the full reasoning behind
    this table's shape: EVERY row, at every nesting depth, carries both
    `questionnaire_pk` (denormalized straight back to the root — makes a
    whole-tree fetch and a whole-tree bulk delete each a single flat
    query) and `parent_item_id` (self-referential, NULL for a top-level
    item — encodes the actual tree structure). There is deliberately no
    ORM-level self-referential `relationship()` for parent/children
    navigation — the mapper fetches the flat `questionnaire.items`
    collection once (eager-loaded) and reconstructs the nested FHIR
    `item[]` shape in Python by grouping on `parent_item_id`, which is
    simpler than a `remote_side`-based adjacency-list relationship and
    avoids per-level selectinload hops for an unbounded depth.
    """

    __tablename__ = "questionnaire_item"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    questionnaire_pk = Column(
        BigInteger, ForeignKey("questionnaire.id"), nullable=False, index=True
    )
    # Self-referential — NULL means this is a top-level item. No
    # ondelete="CASCADE" (see CLAUDE.md's grandchild-deletion invariant);
    # app/repository/questionnaire/full.py's patch_full() bulk-deletes the
    # whole tree via questionnaire_pk before any FK ordering would matter.
    parent_item_id = Column(
        BigInteger, ForeignKey("questionnaire_item.id"), nullable=True, index=True
    )

    link_id = Column(String, nullable=False)
    definition = Column(String, nullable=True)
    prefix = Column(String, nullable=True)
    text = Column(String, nullable=True)
    type = Column(Enum(QuestionnaireItemType, name="questionnaire_item_type"), nullable=False)
    enable_behavior = Column(
        Enum(QuestionnaireEnableBehavior, name="questionnaire_enable_behavior"),
        nullable=True,
    )
    required = Column(Boolean, nullable=True)
    repeats = Column(Boolean, nullable=True)
    read_only = Column(Boolean, nullable=True)
    max_length = Column(Integer, nullable=True)
    answer_value_set = Column(String, nullable=True)

    questionnaire = relationship("QuestionnaireModel", back_populates="items")
    codings = relationship(
        "QuestionnaireItemCoding", back_populates="item", cascade="all, delete-orphan"
    )
    enable_whens = relationship(
        "QuestionnaireItemEnableWhen",
        back_populates="item",
        cascade="all, delete-orphan",
    )
    answer_options = relationship(
        "QuestionnaireItemAnswerOption",
        back_populates="item",
        cascade="all, delete-orphan",
    )
    initials = relationship(
        "QuestionnaireItemInitial", back_populates="item", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# item.code (0..*) Coding grandchild table — item.code is already a bare
# Coding (not a CodeableConcept), same flat-promotion shape as
# questionnaire.coding.QuestionnaireCoding.
# ---------------------------------------------------------------------------


class QuestionnaireItemCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Questionnaire.item.code (0..* Coding) — e.g. a LOINC
    code for this specific question."""

    __tablename__ = "questionnaire_item_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    questionnaire_item_id = Column(
        BigInteger, ForeignKey("questionnaire_item.id"), nullable=False, index=True
    )

    item = relationship("QuestionnaireItem", back_populates="codings")
