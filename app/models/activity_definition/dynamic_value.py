from sqlalchemy import BigInteger, Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import TenantAuditMixin


class ActivityDefinitionDynamicValue(TenantAuditMixin, Base):
    """ActivityDefinition.dynamicValue (0..*) child table."""

    __tablename__ = "activity_definition_dynamic_value"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    activity_definition_pk = Column(
        BigInteger, ForeignKey("activity_definition.id", ondelete="CASCADE"), nullable=False, index=True
    )

    path = Column(String, nullable=False)
    expression_description = Column(String, nullable=True)
    expression_name = Column(String, nullable=True)
    expression_language = Column(String, nullable=True)
    expression_expression = Column(Text, nullable=True)
    expression_reference = Column(String, nullable=True)

    activity_definition = relationship("ActivityDefinitionModel", back_populates="dynamic_values")
