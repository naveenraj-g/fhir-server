from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin

# ---------------------------------------------------------------------------
# item (0..*, recursive BackboneElement) — mutually recursive with answer
# ---------------------------------------------------------------------------


class QuestionnaireResponseItem(TenantAuditMixin, Base):
    """QuestionnaireResponse.item (0..*, recursive — item.item nests to
    unbounded depth, AND an item's children may instead live under one of
    its own answers' item[] — see QuestionnaireResponseModel's docstring)
    — https://www.hl7.org/fhir/R4/questionnaireresponse-definitions.html#QuestionnaireResponse.item

    Every row, at every depth, carries `questionnaire_response_pk`
    (denormalized straight back to the root — same trick as
    QuestionnaireItem's own `questionnaire_pk`, makes a whole-tree fetch
    and a whole-tree bulk delete each a single flat query).

    Two possible parents, modeled asymmetrically on purpose:

    - `parent_item_id` (self-referential FK, NULL unless this item nests
      directly under another item's `item[]`) — a real FK, exactly like
      Questionnaire.item's own `parent_item_id`. A single bulk `DELETE
      ... WHERE questionnaire_response_pk = :id` against this table alone
      removes the whole self-referential subtree in one statement
      regardless of row order, per the same precedent documented on
      QuestionnaireItem's own `parent_item_id`.
    - `parent_answer_id` (NULL unless this item nests under a specific
      answer's `item[]`) — deliberately NOT a real FK, unlike
      `parent_item_id`. QuestionnaireResponseAnswer.item_id is itself a
      real, required FK pointing the other way (every answer belongs to
      exactly one item) — so if `parent_answer_id` were also a real FK,
      the two tables would form a genuine mutual-reference cycle
      (item -> answer via parent_answer_id, answer -> item via item_id)
      that a plain two-statement bulk delete can't resolve without
      deferred constraints (no row ordering makes both directions valid
      at once). Dropping the FK on this one column only — while keeping
      referential intent documented here and enforced by the FHIR
      validator layer, not Postgres — breaks that cycle cleanly: delete
      every answer row for this response first (one statement, safe since
      nothing still references answer rows once the cycle is broken),
      then every item row (one statement, safe per the self-referential
      precedent above). See
      app.repository.questionnaire_response.core._CoreMixin.delete() and
      .full._FullMixin.patch_full() for the actual delete ordering.

    There is deliberately no ORM-level `relationship()` for either parent
    pointer — the mapper fetches the flat `questionnaire_response.items`
    and `.answers` collections once (both eager-loaded) and reconstructs
    the nested FHIR `item[]`/`answer[].item[]` shape in Python by grouping
    on `parent_item_id` and `parent_answer_id`, same approach as
    Questionnaire.item's own flat-list-plus-grouping reconstruction.
    """

    __tablename__ = "questionnaire_response_item"

    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)
    questionnaire_response_pk = Column(
        BigInteger, ForeignKey("questionnaire_response.id"), nullable=False, index=True
    )
    parent_item_id = Column(
        BigInteger, ForeignKey("questionnaire_response_item.id"), nullable=True, index=True
    )
    # Deliberately NOT a ForeignKey — see class docstring.
    parent_answer_id = Column(BigInteger, nullable=True, index=True)

    link_id = Column(String, nullable=False)
    definition = Column(String, nullable=True)
    text = Column(String, nullable=True)

    questionnaire_response = relationship("QuestionnaireResponseModel", back_populates="items")
    answers = relationship(
        "QuestionnaireResponseAnswer",
        back_populates="item",
        foreign_keys="QuestionnaireResponseAnswer.item_id",
        cascade="all, delete-orphan",
    )
