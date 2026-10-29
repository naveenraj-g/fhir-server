from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRCoding,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
    PlainCodingRow,
)


class FHIRDuration(BaseModel):
    """FHIR R4 Duration — not in app.schemas.datatypes since Encounter is
    the only resource in this codebase using it so far (same situation as
    FHIRPeriod before Schedule/Slot needed it)."""

    value: float | None = None
    comparator: str | None = None
    unit: str | None = None
    system: str | None = None
    code: str | None = None


# ── FHIR (camelCase) ────────────────────────────────────────────────────────


class FHIREncounterStatusHistory(BaseModel):
    status: str
    period: FHIRPeriod | None = None


class FHIREncounterClassHistory(BaseModel):
    class_: FHIRCoding | None = Field(None, alias="class")
    period: FHIRPeriod | None = None
    model_config = ConfigDict(populate_by_name=True)


class FHIREncounterParticipant(BaseModel):
    type: list[FHIRCodeableConcept] | None = None
    period: FHIRPeriod | None = None
    individual: FHIRReference | None = None


class FHIREncounterDiagnosis(BaseModel):
    condition: FHIRReference
    use: FHIRCodeableConcept | None = None
    rank: int | None = None


class FHIREncounterHospitalization(BaseModel):
    preAdmissionIdentifier: FHIRIdentifier | None = None
    origin: FHIRReference | None = None
    admitSource: FHIRCodeableConcept | None = None
    reAdmission: FHIRCodeableConcept | None = None
    dietPreference: list[FHIRCodeableConcept] | None = None
    specialCourtesy: list[FHIRCodeableConcept] | None = None
    specialArrangement: list[FHIRCodeableConcept] | None = None
    destination: FHIRReference | None = None
    dischargeDisposition: FHIRCodeableConcept | None = None


class FHIREncounterLocation(BaseModel):
    location: FHIRReference
    status: str | None = None
    physicalType: FHIRCodeableConcept | None = None
    period: FHIRPeriod | None = None


class FHIREncounterSchema(BaseModel):
    resourceType: str = Field("Encounter", description="Always 'Encounter'.")
    id: str = Field(..., description="Public encounter_id as a string.")
    meta: FHIRMeta | None = None
    extension: list[dict] | None = None
    identifier: list[FHIRIdentifier] | None = None
    status: str = Field(..., description="planned|arrived|triaged|in-progress|onleave|finished|cancelled|entered-in-error|unknown.")
    class_: FHIRCoding = Field(..., alias="class", description="Classification of the patient encounter.")
    type: list[FHIRCodeableConcept] | None = None
    serviceType: FHIRCodeableConcept | None = None
    priority: FHIRCodeableConcept | None = None
    subject: FHIRReference | None = None
    episodeOfCare: list[FHIRReference] | None = None
    basedOn: list[FHIRReference] | None = None
    participant: list[FHIREncounterParticipant] | None = None
    appointment: list[FHIRReference] | None = None
    period: FHIRPeriod | None = None
    length: FHIRDuration | None = None
    reasonCode: list[FHIRCodeableConcept] | None = None
    reasonReference: list[FHIRReference] | None = None
    diagnosis: list[FHIREncounterDiagnosis] | None = None
    account: list[FHIRReference] | None = None
    hospitalization: FHIREncounterHospitalization | None = None
    location: list[FHIREncounterLocation] | None = None
    serviceProvider: FHIRReference | None = None
    partOf: FHIRReference | None = None
    statusHistory: list[FHIREncounterStatusHistory] | None = None
    classHistory: list[FHIREncounterClassHistory] | None = None

    model_config = ConfigDict(populate_by_name=True)


class FHIREncounterBundleEntry(BaseModel):
    resource: FHIREncounterSchema


class FHIREncounterBundle(FHIRBundle):
    entry: list[FHIREncounterBundleEntry] | None = None


# ── Plain (snake_case) ───────────────────────────────────────────────────────


class PlainEncounterIdentifier(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    use: str | None = None
    type_codings: list[PlainCodingRow] | None = None
    type_text: str | None = None
    system: str | None = None
    value: str | None = None
    period_start: str | None = None
    period_end: str | None = None
    assigner: str | None = None
    assigner_type: str | None = None
    assigner_id: int | None = None
    assigner_display: str | None = None


class PlainEncounterStatusHistory(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    status: str | None = None
    period_start: str | None = None
    period_end: str | None = None


class PlainEncounterClassHistory(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    class_system: str | None = None
    class_version: str | None = None
    class_code: str | None = None
    class_display: str | None = None
    class_user_selected: bool | None = None
    period_start: str | None = None
    period_end: str | None = None


class _PlainCodeableConceptRow(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    codings: list[PlainCodingRow] | None = None
    text: str | None = None


class PlainEncounterType(_PlainCodeableConceptRow):
    pass


class PlainEncounterReasonCode(_PlainCodeableConceptRow):
    pass


class PlainEncounterParticipantType(_PlainCodeableConceptRow):
    pass


class PlainEncounterHospitalizationDietPreference(_PlainCodeableConceptRow):
    pass


class PlainEncounterHospitalizationSpecialCourtesy(_PlainCodeableConceptRow):
    pass


class PlainEncounterHospitalizationSpecialArrangement(_PlainCodeableConceptRow):
    pass


class _PlainReferenceRow(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    reference: str | None = None
    reference_type: str | None = None
    reference_id: int | None = None
    reference_display: str | None = None


class PlainEncounterEpisodeOfCare(_PlainReferenceRow):
    pass


class PlainEncounterBasedOn(_PlainReferenceRow):
    pass


class PlainEncounterAppointment(_PlainReferenceRow):
    pass


class PlainEncounterReasonReference(_PlainReferenceRow):
    pass


class PlainEncounterAccount(_PlainReferenceRow):
    pass


class PlainEncounterParticipant(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    types: list[PlainEncounterParticipantType] | None = None
    period_start: str | None = None
    period_end: str | None = None
    individual: str | None = None
    individual_type: str | None = None
    individual_id: int | None = None
    individual_display: str | None = None


class PlainEncounterDiagnosis(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    condition: str | None = None
    condition_type: str | None = None
    condition_id: int | None = None
    condition_display: str | None = None
    use_codings: list[PlainCodingRow] | None = None
    use_text: str | None = None
    rank: int | None = None


class PlainEncounterHospitalization(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    pre_admission_identifier_use: str | None = None
    pre_admission_identifier_type_codings: list[PlainCodingRow] | None = None
    pre_admission_identifier_type_text: str | None = None
    pre_admission_identifier_system: str | None = None
    pre_admission_identifier_value: str | None = None
    pre_admission_identifier_period_start: str | None = None
    pre_admission_identifier_period_end: str | None = None
    pre_admission_identifier_assigner: str | None = None
    pre_admission_identifier_assigner_display: str | None = None
    origin: str | None = None
    origin_type: str | None = None
    origin_id: int | None = None
    origin_display: str | None = None
    admit_source_codings: list[PlainCodingRow] | None = None
    admit_source_text: str | None = None
    re_admission_codings: list[PlainCodingRow] | None = None
    re_admission_text: str | None = None
    diet_preference: list[PlainEncounterHospitalizationDietPreference] | None = None
    special_courtesy: list[PlainEncounterHospitalizationSpecialCourtesy] | None = None
    special_arrangement: list[PlainEncounterHospitalizationSpecialArrangement] | None = None
    destination: str | None = None
    destination_type: str | None = None
    destination_id: int | None = None
    destination_display: str | None = None
    discharge_disposition_codings: list[PlainCodingRow] | None = None
    discharge_disposition_text: str | None = None


class PlainEncounterLocation(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    location: str | None = None
    location_type: str | None = None
    location_id: int | None = None
    location_display: str | None = None
    status: str | None = None
    physical_type_codings: list[PlainCodingRow] | None = None
    physical_type_text: str | None = None
    period_start: str | None = None
    period_end: str | None = None


class PlainEncounterResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Public encounter_id.")
    extension: list[dict] | None = None
    status: str | None = None
    class_system: str | None = None
    class_version: str | None = None
    class_code: str | None = None
    class_display: str | None = None
    class_user_selected: bool | None = None
    service_type_codings: list[PlainCodingRow] | None = None
    service_type_text: str | None = None
    priority_codings: list[PlainCodingRow] | None = None
    priority_text: str | None = None
    subject: str | None = None
    subject_type: str | None = None
    subject_id: int | None = None
    subject_display: str | None = None
    period_start: str | None = None
    period_end: str | None = None
    length_value: str | None = None
    length_comparator: str | None = None
    length_unit: str | None = None
    length_system: str | None = None
    length_code: str | None = None
    service_provider: str | None = None
    service_provider_type: str | None = None
    service_provider_id: int | None = None
    service_provider_display: str | None = None
    part_of: str | None = None
    part_of_type: str | None = None
    part_of_id: int | None = None
    part_of_display: str | None = None
    identifier: list[PlainEncounterIdentifier] | None = None
    status_history: list[PlainEncounterStatusHistory] | None = None
    class_history: list[PlainEncounterClassHistory] | None = None
    type: list[PlainEncounterType] | None = None
    episode_of_care: list[PlainEncounterEpisodeOfCare] | None = None
    based_on: list[PlainEncounterBasedOn] | None = None
    appointment: list[PlainEncounterAppointment] | None = None
    reason_code: list[PlainEncounterReasonCode] | None = None
    reason_reference: list[PlainEncounterReasonReference] | None = None
    account: list[PlainEncounterAccount] | None = None
    participant: list[PlainEncounterParticipant] | None = None
    diagnosis: list[PlainEncounterDiagnosis] | None = None
    hospitalization: PlainEncounterHospitalization | None = None
    location: list[PlainEncounterLocation] | None = None
    org_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    created_by: str | None = None
    updated_by: str | None = None


class PaginatedEncounterResponse(BaseModel):
    total: int | None = None
    limit: int
    offset: int
    data: list[PlainEncounterResponse]
