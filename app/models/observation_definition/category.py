from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class ObservationDefinitionCategory(TenantAuditMixin, Base):
    """ObservationDefinition.category (0..* CodeableConcept) child table."""

    __tablename__ = "observation_definition_category"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    observation_definition_pk = Column(
        BigInteger, ForeignKey("observation_definition.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    observation_definition = relationship(
        "ObservationDefinitionModel", back_populates="categories"
    )
    codings = relationship(
        "ObservationDefinitionCategoryCoding",
        back_populates="category",
        cascade="all, delete-orphan",
    )


class ObservationDefinitionCategoryCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """ObservationDefinition.category.coding (0..*) grandchild table."""

    __tablename__ = "observation_definition_category_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    category_id = Column(
        BigInteger,
        ForeignKey("observation_definition_category.id"),
        nullable=False,
        index=True,
    )

    category = relationship(
        "ObservationDefinitionCategory", back_populates="codings"
    )
