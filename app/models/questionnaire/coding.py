from sqlalchemy import BigInteger, Column, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# code (0..*) Coding child table — Questionnaire.code is already a bare
# Coding (not a CodeableConcept), so this is a flat promoted child table
# with no grandchild coding layer underneath it (nothing to promote
# further — FhirCodingMixin's columns ARE the whole datatype here).
# ---------------------------------------------------------------------------


class QuestionnaireCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Questionnaire.code (0..* Coding) — a concept that
    represents the overall questionnaire (e.g. a LOINC panel code)."""

    __tablename__ = "questionnaire_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    questionnaire_pk = Column(
        BigInteger, ForeignKey("questionnaire.id"), nullable=False, index=True
    )

    questionnaire = relationship("QuestionnaireModel", back_populates="codings")
