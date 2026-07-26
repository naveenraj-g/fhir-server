from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PractitionerRoleIdentifierInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: Optional[str] = None
    type_system: Optional[str] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    type_text: Optional[str] = None
    system: Optional[str] = None
    value: str = Field(..., description="Identifier value.")
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    assigner: Optional[str] = None


class PractitionerRoleCodeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PractitionerRoleSpecialtyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class PractitionerRoleLocationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="FHIR reference, e.g. 'Location/123'.")
    reference_display: Optional[str] = None


class PractitionerRoleHealthcareServiceInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="FHIR reference, e.g. 'HealthcareService/150001'.")
    reference_display: Optional[str] = None


class PractitionerRoleTelecomInput(BaseModel):
    """telecom[] (0..*) ContactPoint — required R4 element."""
    model_config = ConfigDict(extra="forbid")
    system: Optional[str] = Field(None, description="phone|fax|email|pager|url|sms|other")
    value: Optional[str] = None
    use: Optional[str] = Field(None, description="home|work|temp|old|mobile")
    rank: Optional[int] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class PractitionerRoleAvailableTimeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    days_of_week: Optional[List[str]] = Field(None, description="e.g. ['mon', 'wed', 'fri']")
    all_day: Optional[bool] = None
    available_start_time: Optional[str] = Field(None, description="HH:mm:ss")
    available_end_time: Optional[str] = Field(None, description="HH:mm:ss")


class PractitionerRoleNotAvailableTimeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: Optional[str] = None
    during_start: Optional[datetime] = None
    during_end: Optional[datetime] = None


class PractitionerRoleEndpointInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="FHIR reference, e.g. 'Endpoint/123'.")
    reference_display: Optional[str] = None


class PractitionerRoleCreateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "user_id": "user-123",
                "org_id": "org-456",
                "practitioner": "Practitioner/30001",
                "practitioner_display": "Dr. Jane Smith",
                "organization": "Organization/190001",
                "organization_display": "General Hospital",
                "active": True,
                "period_start": "2024-01-01T00:00:00Z",
                "period_end": None,
                "availability_exceptions": "Not available on public holidays",
                "code": [
                    {
                        "coding_system": "http://snomed.info/sct",
                        "coding_code": "59058001",
                        "coding_display": "General physician",
                    }
                ],
                "specialty": [
                    {
                        "coding_system": "http://snomed.info/sct",
                        "coding_code": "394814009",
                        "coding_display": "General practice",
                    }
                ],
                "location": [{"reference": "Location/1", "reference_display": "Main Clinic"}],
                "identifier": [],
                "healthcare_service": [],
                "telecom": [
                    {"system": "phone", "value": "+1-555-0100", "use": "work"}
                ],
                "available_time": [
                    {
                        "days_of_week": ["mon", "tue", "wed", "thu", "fri"],
                        "available_start_time": "09:00:00",
                        "available_end_time": "17:00:00",
                    }
                ],
                "not_available": [],
                "endpoint": [],
            }
        },
    )

    user_id: Optional[str] = Field(None, description="JWT sub of the record owner.")
    org_id: Optional[str] = Field(None, description="Active organization ID from JWT.")
    created_by: Optional[str] = None

    practitioner: Optional[str] = Field(None, description="Reference to Practitioner, e.g. 'Practitioner/30001'.")
    practitioner_display: Optional[str] = None
    organization: Optional[str] = Field(None, description="Reference to Organization, e.g. 'Organization/190001'.")
    organization_display: Optional[str] = None

    active: Optional[bool] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    availability_exceptions: Optional[str] = None

    identifier: Optional[List[PractitionerRoleIdentifierInput]] = None
    code: Optional[List[PractitionerRoleCodeInput]] = None
    specialty: Optional[List[PractitionerRoleSpecialtyInput]] = None
    location: Optional[List[PractitionerRoleLocationInput]] = None
    healthcare_service: Optional[List[PractitionerRoleHealthcareServiceInput]] = None
    telecom: Optional[List[PractitionerRoleTelecomInput]] = None
    available_time: Optional[List[PractitionerRoleAvailableTimeInput]] = None
    not_available: Optional[List[PractitionerRoleNotAvailableTimeInput]] = None
    endpoint: Optional[List[PractitionerRoleEndpointInput]] = None


class PractitionerRolePatchSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    active: Optional[bool] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    availability_exceptions: Optional[str] = None
    updated_by: Optional[str] = None
