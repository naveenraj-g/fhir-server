from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.shared import TenantAuditMixin
from app.models.shared.datatypes import FhirCodingMixin

from .enums import ClinicalImpressionPrognosisReferenceType


class ClinicalImpressionPrognosisCodeableConceptModel(TenantAuditMixin, Base):
    """ClinicalImpression.prognosisCodeableConcept (0..* CodeableConcept) child table."""

    __tablename__ = "clinical_impression_prognosis_codeable_concept"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    clinical_impression_pk = Column(
        BigInteger, ForeignKey("clinical_impression.id"), nullable=False, index=True
    )

    text = Column(String, nullable=True)

    clinical_impression = relationship(
        "ClinicalImpressionModel", back_populates="prognosis_codeable_concepts"
    )
    codings = relationship(
        "ClinicalImpressionPrognosisCodingModel",
        back_populates="prognosis_codeable_concept",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ClinicalImpressionPrognosisCodingModel(FhirCodingMixin, TenantAuditMixin, Base):
    """clinical_impression_prognosis_codeable_concept.coding (0..* Coding) grandchild table."""

    __tablename__ = "clinical_impression_prognosis_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    clinical_impression_prognosis_id = Column(
        BigInteger,
        ForeignKey("clinical_impression_prognosis_codeable_concept.id"),
        nullable=False,
        index=True,
    )

    prognosis_codeable_concept = relationship(
        "ClinicalImpressionPrognosisCodeableConceptModel", back_populates="codings"
    )


class ClinicalImpressionPrognosisReferenceModel(TenantAuditMixin, Base):
    """ClinicalImpression.prognosisReference (0..* Reference(RiskAssessment)) child table."""

    __tablename__ = "clinical_impression_prognosis_reference"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    clinical_impression_pk = Column(
        BigInteger, ForeignKey("clinical_impression.id"), nullable=False, index=True
    )

    reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(
            ClinicalImpressionPrognosisReferenceType,
            name="clinical_impression_prognosis_reference_type",
        ),
        nullable=True,
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    display = Column(String, nullable=True)

    # fallback (11 columns)
    identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    identifier_type_system = Column(String, nullable=True)
    identifier_type_version = Column(String, nullable=True)
    identifier_type_code = Column(String, nullable=True)
    identifier_type_display = Column(String, nullable=True)
    identifier_type_user_selected = Column(Boolean, nullable=True)
    identifier_type_text = Column(String, nullable=True)
    identifier_system = Column(String, nullable=True)
    identifier_value = Column(String, nullable=True)
    identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    clinical_impression = relationship(
        "ClinicalImpressionModel", back_populates="prognosis_references"
    )
