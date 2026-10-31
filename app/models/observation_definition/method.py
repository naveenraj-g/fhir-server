from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ObservationDefinitionMethodCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """ObservationDefinition.method.coding (0..*) child table."""

    __tablename__ = "observation_definition_method_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_definition_pk = Column(
        BigInteger, ForeignKey("observation_definition.id"), nullable=False, index=True
    )

    observation_definition = relationship(
        "ObservationDefinitionModel", back_populates="method_codings"
    )
