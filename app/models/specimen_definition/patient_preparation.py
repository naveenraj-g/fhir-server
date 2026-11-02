from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class SpecimenDefinitionPatientPreparation(TenantAuditMixin, Base):
    """SpecimenDefinition.patientPreparation (0..* CodeableConcept)."""

    __tablename__ = "specimen_definition_patient_preparation"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    specimen_definition_pk = Column(
        BigInteger, ForeignKey("specimen_definition.id"), nullable=False, index=True
    )
    text = Column(String, nullable=True)

    specimen_definition = relationship(
        "SpecimenDefinitionModel", back_populates="patient_preparations"
    )
    codings = relationship(
        "SpecimenDefinitionPatientPreparationCoding",
        back_populates="patient_preparation",
        cascade="all, delete-orphan",
    )


class SpecimenDefinitionPatientPreparationCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """Coding within SpecimenDefinition.patientPreparation."""

    __tablename__ = "specimen_definition_patient_preparation_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    patient_preparation_pk = Column(
        BigInteger,
        ForeignKey("specimen_definition_patient_preparation.id"),
        nullable=False,
        index=True,
    )

    patient_preparation = relationship(
        "SpecimenDefinitionPatientPreparation", back_populates="codings"
    )
