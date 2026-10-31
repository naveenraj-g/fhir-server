from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ObservationDefinitionQuantitativeDetailsCustomaryUnitCoding(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """ObservationDefinition.quantitativeDetails.customaryUnit.coding (0..*) child table."""

    __tablename__ = "observation_definition_quantitative_details_customary_unit_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_definition_pk = Column(
        BigInteger, ForeignKey("observation_definition.id"), nullable=False, index=True
    )

    observation_definition = relationship(
        "ObservationDefinitionModel",
        back_populates="quantitative_details_customary_unit_codings",
    )


class ObservationDefinitionQuantitativeDetailsUnitCoding(
    FhirCodingMixin, TenantAuditMixin, Base
):
    """ObservationDefinition.quantitativeDetails.unit.coding (0..*) child table."""

    __tablename__ = "observation_definition_quantitative_details_unit_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_definition_pk = Column(
        BigInteger, ForeignKey("observation_definition.id"), nullable=False, index=True
    )

    observation_definition = relationship(
        "ObservationDefinitionModel",
        back_populates="quantitative_details_unit_codings",
    )
