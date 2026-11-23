from sqlalchemy import BigInteger, Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class QuestionnaireContextQuantity(Base):
    """Search index for `context-quantity` (and the `context-type-quantity` composite): one row
    per `useContext` whose value[x] is a Quantity or a Range. Derived from
    QuestionnaireModel.content - never read to build a response.

    The quantity is held as a lower and an upper bound with one shared (system, code, unit): a
    Quantity is a point (low == high), a Range runs from `low` to `high`, an open end is NULL. It
    is matched with `quantity_range_match`. `slot` is the n-th useContext (1-based), the same
    numbering QuestionnaireToken uses, so a composite can pair the context's code with its
    quantity."""

    __tablename__ = "questionnaire_context_quantity"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    questionnaire_pk = Column(
        BigInteger, ForeignKey("questionnaire.id"), nullable=False, index=True
    )
    slot = Column(Integer, nullable=False)
    quantity_low = Column(Numeric, nullable=True)
    quantity_high = Column(Numeric, nullable=True)
    quantity_system = Column(String, nullable=True)
    quantity_code = Column(String, nullable=True)
    quantity_unit = Column(String, nullable=True)

    questionnaire = relationship(
        "QuestionnaireModel", back_populates="context_quantities"
    )
