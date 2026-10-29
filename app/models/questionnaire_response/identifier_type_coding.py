from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# identifier.type.coding (0..*) child table — identifier itself is 0..1 and
# flattened directly onto QuestionnaireResponseModel (see its docstring),
# but its own .type CodeableConcept still gets a real coding[] child table.
# ---------------------------------------------------------------------------


class QuestionnaireResponseIdentifierTypeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of QuestionnaireResponse.identifier.type.coding (0..*).
    FKs directly to the main table (not to a separate identifier child
    table, since there's only ever one identifier per response)."""

    __tablename__ = "questionnaire_response_identifier_type_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    questionnaire_response_pk = Column(
        BigInteger, ForeignKey("questionnaire_response.id"), nullable=False, index=True
    )

    questionnaire_response = relationship(
        "QuestionnaireResponseModel", back_populates="identifier_type_codings"
    )
