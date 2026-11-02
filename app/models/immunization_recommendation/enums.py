from enum import Enum


class ImmunizationRecommendationPatientReferenceType(str, Enum):
    """ImmunizationRecommendation.patient Reference(Patient)."""

    Patient = "Patient"


class ImmunizationRecommendationAuthorityReferenceType(str, Enum):
    """ImmunizationRecommendation.authority Reference(Organization)."""

    Organization = "Organization"


class ImmunizationRecommendationSupportingImmunizationReferenceType(str, Enum):
    """ImmunizationRecommendation.recommendation.supportingImmunization Reference(Immunization | ImmunizationEvaluation)."""

    Immunization = "Immunization"
    ImmunizationEvaluation = "ImmunizationEvaluation"


class ImmunizationRecommendationSupportingPatientInformationReferenceType(str, Enum):
    """ImmunizationRecommendation.recommendation.supportingPatientInformation Reference(Resource)."""

    Condition = "Condition"
    Observation = "Observation"
    AllergyIntolerance = "AllergyIntolerance"
    DiagnosticReport = "DiagnosticReport"
    DocumentReference = "DocumentReference"
    Encounter = "Encounter"
    MedicationStatement = "MedicationStatement"
    FamilyMemberHistory = "FamilyMemberHistory"
    Procedure = "Procedure"
    Immunization = "Immunization"
    Resource = "Resource"
