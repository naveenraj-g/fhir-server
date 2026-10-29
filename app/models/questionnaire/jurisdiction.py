from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# jurisdiction (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class QuestionnaireJurisdiction(TenantAuditMixin, Base):
    """Questionnaire.jurisdiction (0..* CodeableConcept) — mirrors
    app.models.organization.type.OrganizationType's reasoning: `text`
    stays flattened here, `coding[]` is a real 0..* grandchild table."""

    __tablename__ = "questionnaire_jurisdiction"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    questionnaire_pk = Column(
        BigInteger, ForeignKey("questionnaire.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    questionnaire = relationship("QuestionnaireModel", back_populates="jurisdictions")
    codings = relationship(
        "QuestionnaireJurisdictionCoding",
        back_populates="jurisdiction",
        cascade="all, delete-orphan",
    )


class QuestionnaireJurisdictionCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of Questionnaire.jurisdiction.coding (0..*)."""

    __tablename__ = "questionnaire_jurisdiction_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    questionnaire_jurisdiction_id = Column(
        BigInteger, ForeignKey("questionnaire_jurisdiction.id"), nullable=False, index=True
    )

    jurisdiction = relationship("QuestionnaireJurisdiction", back_populates="codings")
