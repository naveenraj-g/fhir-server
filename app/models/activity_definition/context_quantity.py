from sqlalchemy import BigInteger, Column, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class ActivityDefinitionContextQuantity(Base):
    """Search index for `context-quantity` (and the `context-type-quantity` composite): one row
    per `useContext` whose value[x] is a Quantity or a Range. Derived from
    ActivityDefinitionModel.content - never read to build a response.

    The quantity is held as a lower and an upper bound with one shared (system, code, unit): a
    Quantity is a point (low == high), a Range runs from `low` to `high`, an open end is NULL. It
    is matched with `quantity_range_match`. `slot` is the n-th useContext (1-based), the same
    numbering ActivityDefinitionToken uses, so a composite can pair the context's code with its
    quantity."""

    __tablename__ = "activity_definition_context_quantity"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_pk = Column(
        BigInteger, ForeignKey("activity_definition.id"), nullable=False, index=True
    )
    slot = Column(Integer, nullable=False)
    quantity_low = Column(Numeric, nullable=True)
    quantity_high = Column(Numeric, nullable=True)
    quantity_system = Column(String, nullable=True)
    quantity_code = Column(String, nullable=True)
    quantity_unit = Column(String, nullable=True)

    activity_definition = relationship(
        "ActivityDefinitionModel", back_populates="context_quantities"
    )
