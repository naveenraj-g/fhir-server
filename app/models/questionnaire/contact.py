from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirContactPointMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# contact (0..*) child table — ContactDetail: {name: string, telecom: ContactPoint[]}
# ---------------------------------------------------------------------------


class QuestionnaireContact(TenantAuditMixin, Base):
    """Questionnaire.contact (0..*, ContactDetail) — unlike Organization.contact
    (a different FHIR datatype entirely: a BackboneElement with purpose/
    name/telecom/address), ContactDetail is just `{name: string, telecom:
    ContactPoint[]}` — no purpose, no HumanName, no Address."""

    __tablename__ = "questionnaire_contact"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    questionnaire_pk = Column(
        BigInteger, ForeignKey("questionnaire.id"), nullable=False, index=True
    )

    name = Column(String, nullable=True)

    questionnaire = relationship("QuestionnaireModel", back_populates="contacts")
    telecoms = relationship(
        "QuestionnaireContactTelecom",
        back_populates="contact",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------------------
# contact.telecom (0..*) grandchild table
# ---------------------------------------------------------------------------


class QuestionnaireContactTelecom(FhirContactPointMixin, TenantAuditMixin, Base):
    """One entry of Questionnaire.contact.telecom (0..*)."""

    __tablename__ = "questionnaire_contact_telecom"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    questionnaire_contact_id = Column(
        BigInteger, ForeignKey("questionnaire_contact.id"), nullable=False, index=True
    )

    contact = relationship("QuestionnaireContact", back_populates="telecoms")
