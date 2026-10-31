from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ObservationDefinitionCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """ObservationDefinition.code.coding (0..*) child table."""

    __tablename__ = "observation_definition_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_definition_pk = Column(
        BigInteger, ForeignKey("observation_definition.id"), nullable=False, index=True
    )

    observation_definition = relationship(
        "ObservationDefinitionModel", back_populates="code_codings"
    )
