from pydantic import BaseModel, ConfigDict


class _PlainReferenceRow(BaseModel):
    """List-item Reference rows — real 0..* child-table rows, so each
    carries its own `id`."""

    model_config = ConfigDict(extra="allow")
    id: int
    reference: str | None = None
    reference_type: str | None = None
    reference_id: int | None = None
    reference_display: str | None = None


class PlainMedicationRequestBasedOn(_PlainReferenceRow):
    pass


class PlainMedicationRequestReasonReference(_PlainReferenceRow):
    pass


class PlainMedicationRequestInsurance(_PlainReferenceRow):
    pass


class PlainMedicationRequestSupportingInformation(_PlainReferenceRow):
    pass


class PlainMedicationRequestDetectedIssue(_PlainReferenceRow):
    pass


class PlainMedicationRequestEventHistory(_PlainReferenceRow):
    pass


class _PlainSingleReferenceRow(BaseModel):
    """Single 0..1 Reference fields — flattened directly onto the owning
    row, so no `id` here."""

    model_config = ConfigDict(extra="allow")
    reference: str | None = None
    reference_type: str | None = None
    reference_id: int | None = None
    reference_display: str | None = None


class PlainMedicationRequestSubject(_PlainSingleReferenceRow):
    pass


class PlainMedicationRequestEncounter(_PlainSingleReferenceRow):
    pass


class PlainMedicationRequestReportedReference(_PlainSingleReferenceRow):
    pass


class PlainMedicationRequestMedicationReference(_PlainSingleReferenceRow):
    pass


class PlainMedicationRequestRequester(_PlainSingleReferenceRow):
    pass


class PlainMedicationRequestPerformer(_PlainSingleReferenceRow):
    pass


class PlainMedicationRequestRecorder(_PlainSingleReferenceRow):
    pass


class PlainMedicationRequestDispenseRequestPerformer(_PlainSingleReferenceRow):
    pass


class PlainMedicationRequestPriorPrescription(_PlainSingleReferenceRow):
    pass
