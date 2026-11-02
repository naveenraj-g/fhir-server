from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MedicationStatementCategoryCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MedicationStatement.category.coding (0..*) child table."""

    __tablename__ = "medication_statement_category_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    medication_statement_pk = Column(
        BigInteger, ForeignKey("medication_statement.id"), nullable=False, index=True
    )

    medication_statement = relationship(
        "MedicationStatementModel", back_populates="category_codings"
    )
