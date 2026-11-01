from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.consent.enums import ConsentStatus
from app.schemas.consent.input.codeable_concept import (
    ConsentCodeableConceptInput,
)
from app.schemas.consent.input.identifier import ConsentIdentifierInput
from app.schemas.consent.input.policy import (
    ConsentPolicyInput,
    ConsentReferenceInput,
)
from app.schemas.consent.input.provision import ConsentProvisionInput
from app.schemas.consent.input.verification import ConsentVerificationInput
from app.schemas.enums import IdentifierUse


class ConsentCreateSchema(BaseModel):
    """Payload for POST /api/fhir/v1/consents.

    Tenant scoping (org_id) and created_by come from the verified JWT (actor.org_id / actor.sub).
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "active",
                "scope": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/consentscope",
                            "code": "patient-privacy",
                            "display": "Privacy Consent",
                        }
                    ],
                    "text": "Privacy Consent",
                },
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                                "code": "INFA",
                                "display": "information access",
                            }
                        ],
                        "text": "Information Access",
                    }
                ],
                "patient": "Patient/10001",
                "patient_display": "John Doe",
                "date_time": "2026-01-01T10:00:00Z",
                "performer": [
                    {
                        "reference": "Patient/10001",
                        "display": "John Doe",
                    }
                ],
                "organization": [
                    {
                        "reference": "Organization/190001",
                        "display": "General Hospital",
                    }
                ],
                "policy": [
                    {
                        "authority": "http://example.org/fhir/ConsentPolicy",
                        "uri": "http://example.org/fhir/ConsentPolicy/1",
                    }
                ],
                "policy_rule": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                            "code": "OPTIN",
                            "display": "opt-in",
                        }
                    ],
                    "text": "opt-in",
                },
                "verification": [
                    {
                        "verified": True,
                        "verified_with": "Patient/10001",
                        "verified_with_display": "John Doe",
                        "verification_date": "2026-01-01T10:00:00Z",
                    }
                ],
                "provision": {
                    "type": "permit",
                    "period_start": "2026-01-01T00:00:00Z",
                    "period_end": "2026-12-31T23:59:59Z",
                    "actor": [
                        {
                            "role": {
                                "coding": [
                                    {
                                        "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                                        "code": "PRCP",
                                        "display": "primary recipient",
                                    }
                                ],
                                "text": "Primary Recipient",
                            },
                            "reference": "Practitioner/30001",
                            "reference_display": "Dr. Alice Smith",
                        }
                    ],
                    "action": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/consentaction",
                                    "code": "access",
                                    "display": "Access",
                                }
                            ],
                            "text": "Access",
                        }
                    ],
                },
                "identifier": [
                    {
                        "system": "http://example.org/consents",
                        "value": "CONSENT-001",
                    }
                ],
            }
        },
    )

    status: ConsentStatus = Field(
        ...,
        description="draft | proposed | active | rejected | inactive | entered-in-error.",
    )
    scope: ConsentCodeableConceptInput = Field(
        ..., description="Which problem code this consent applies to."
    )
    category: list[ConsentCodeableConceptInput] = Field(
        ...,
        min_length=1,
        description="Classification of the consent statement - for indexing/retrieval.",
    )
    patient: str | None = Field(
        None,
        description="Who the consent applies to (Patient, e.g. 'Patient/10001').",
    )
    patient_display: str | None = Field(
        None, description="Display name for patient reference."
    )
    patient_identifier_use: IdentifierUse | None = Field(None)
    patient_identifier_type_system: str | None = Field(None)
    patient_identifier_type_version: str | None = Field(None)
    patient_identifier_type_code: str | None = Field(None)
    patient_identifier_type_display: str | None = Field(None)
    patient_identifier_type_text: str | None = Field(None)
    patient_identifier_type_user_selected: bool | None = Field(None)
    patient_identifier_system: str | None = Field(None)
    patient_identifier_value: str | None = Field(None)
    patient_identifier_period_start: datetime | None = Field(None)
    patient_identifier_period_end: datetime | None = Field(None)

    date_time: datetime | None = Field(
        None, description="When this Consent was created or indexed."
    )
    performer: list[ConsentReferenceInput] | None = Field(
        None, description="Who is agreeing to the policy and rules."
    )
    organization: list[ConsentReferenceInput] | None = Field(
        None, description="Custodian of the consent."
    )
    source_attachment: dict[str, Any] | None = Field(
        None, description="Source from which this consent is taken (Attachment)."
    )
    source_reference: str | None = Field(
        None,
        description="Source from which this consent is taken (Consent | DocumentReference | Contract | QuestionnaireResponse).",
    )
    source_reference_display: str | None = Field(
        None, description="Display name for source reference."
    )
    source_reference_identifier_use: IdentifierUse | None = Field(None)
    source_reference_identifier_type_system: str | None = Field(None)
    source_reference_identifier_type_version: str | None = Field(None)
    source_reference_identifier_type_code: str | None = Field(None)
    source_reference_identifier_type_display: str | None = Field(None)
    source_reference_identifier_type_text: str | None = Field(None)
    source_reference_identifier_type_user_selected: bool | None = Field(None)
    source_reference_identifier_system: str | None = Field(None)
    source_reference_identifier_value: str | None = Field(None)
    source_reference_identifier_period_start: datetime | None = Field(None)
    source_reference_identifier_period_end: datetime | None = Field(None)

    policy: list[ConsentPolicyInput] | None = Field(
        None, description="Policies that this consent's rule conforms to."
    )
    policy_rule: ConsentCodeableConceptInput | None = Field(
        None, description="Regulation that this consent conforms to."
    )
    verification: list[ConsentVerificationInput] | None = Field(
        None, description="Consent verification by patient or guardian."
    )
    provision: ConsentProvisionInput | None = Field(
        None, description="Constraints to the base Consent.provision rule."
    )
    identifier: list[ConsentIdentifierInput] | None = Field(
        None, description="Identifier for this record with context."
    )
    extension: list[dict[str, Any]] | None = Field(
        None, description="May be used to represent additional information."
    )


class ConsentPatchSchema(BaseModel):
    """Payload for PATCH /api/fhir/v1/consents/{consent_id}. All fields optional."""

    model_config = ConfigDict(extra="forbid")

    status: ConsentStatus | None = Field(
        None,
        description="draft | proposed | active | rejected | inactive | entered-in-error.",
    )
    scope: ConsentCodeableConceptInput | None = Field(
        None, description="Which problem code this consent applies to."
    )
    category: list[ConsentCodeableConceptInput] | None = Field(
        None,
        min_length=1,
        description="Classification of the consent statement - for indexing/retrieval.",
    )
    patient: str | None = Field(
        None,
        description="Who the consent applies to (Patient, e.g. 'Patient/10001').",
    )
    patient_display: str | None = Field(
        None, description="Display name for patient reference."
    )
    patient_identifier_use: IdentifierUse | None = Field(None)
    patient_identifier_type_system: str | None = Field(None)
    patient_identifier_type_version: str | None = Field(None)
    patient_identifier_type_code: str | None = Field(None)
    patient_identifier_type_display: str | None = Field(None)
    patient_identifier_type_text: str | None = Field(None)
    patient_identifier_type_user_selected: bool | None = Field(None)
    patient_identifier_system: str | None = Field(None)
    patient_identifier_value: str | None = Field(None)
    patient_identifier_period_start: datetime | None = Field(None)
    patient_identifier_period_end: datetime | None = Field(None)

    date_time: datetime | None = Field(
        None, description="When this Consent was created or indexed."
    )
    performer: list[ConsentReferenceInput] | None = Field(
        None, description="Who is agreeing to the policy and rules."
    )
    organization: list[ConsentReferenceInput] | None = Field(
        None, description="Custodian of the consent."
    )
    source_attachment: dict[str, Any] | None = Field(
        None, description="Source from which this consent is taken (Attachment)."
    )
    source_reference: str | None = Field(
        None,
        description="Source from which this consent is taken (Consent | DocumentReference | Contract | QuestionnaireResponse).",
    )
    source_reference_display: str | None = Field(
        None, description="Display name for source reference."
    )
    source_reference_identifier_use: IdentifierUse | None = Field(None)
    source_reference_identifier_type_system: str | None = Field(None)
    source_reference_identifier_type_version: str | None = Field(None)
    source_reference_identifier_type_code: str | None = Field(None)
    source_reference_identifier_type_display: str | None = Field(None)
    source_reference_identifier_type_text: str | None = Field(None)
    source_reference_identifier_type_user_selected: bool | None = Field(None)
    source_reference_identifier_system: str | None = Field(None)
    source_reference_identifier_value: str | None = Field(None)
    source_reference_identifier_period_start: datetime | None = Field(None)
    source_reference_identifier_period_end: datetime | None = Field(None)

    policy: list[ConsentPolicyInput] | None = Field(
        None, description="Policies that this consent's rule conforms to."
    )
    policy_rule: ConsentCodeableConceptInput | None = Field(
        None, description="Regulation that this consent conforms to."
    )
    verification: list[ConsentVerificationInput] | None = Field(
        None, description="Consent verification by patient or guardian."
    )
    provision: ConsentProvisionInput | None = Field(
        None, description="Constraints to the base Consent.provision rule."
    )
    identifier: list[ConsentIdentifierInput] | None = Field(
        None, description="Identifier for this record with context."
    )
    extension: list[dict[str, Any]] | None = Field(
        None, description="May be used to represent additional information."
    )
