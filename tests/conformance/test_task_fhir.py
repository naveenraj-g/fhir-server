"""FHIR R4 conformance for `to_fhir_task()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.task import to_fhir_task
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.task import (
    TaskBasedOn,
    TaskBusinessStatusCoding,
    TaskCodeCoding,
    TaskEncounterReferenceType,
    TaskIdentifier,
    TaskIdentifierTypeCoding,
    TaskInput,
    TaskInputTypeCoding,
    TaskInsurance,
    TaskInsuranceReferenceType,
    TaskIntent,
    TaskLocationReferenceType,
    TaskModel,
    TaskNote,
    TaskOutput,
    TaskOutputTypeCoding,
    TaskOwnerReferenceType,
    TaskPartOf,
    TaskPartOfReferenceType,
    TaskPerformerType,
    TaskPerformerTypeCoding,
    TaskPriority,
    TaskReasonCodeCoding,
    TaskRelevantHistory,
    TaskRelevantHistoryReferenceType,
    TaskRequesterReferenceType,
    TaskRestrictionRecipient,
    TaskRestrictionRecipientReferenceType,
    TaskStatus,
    TaskStatusReasonCoding,
)

from .support import assert_valid

task_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.task_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "based_on_list",
    "part_of_list",
    "insurance_list",
    "relevant_history_list",
    "restriction_recipients",
    "performer_types",
    "code_codings",
    "status_reason_codings",
    "business_status_codings",
    "reason_code_codings",
    "notes",
    "inputs",
    "outputs",
)


def _task(**overrides) -> TaskModel:
    fields = {
        "id": 1,
        "task_id": 280001,
        "tenant_id": "org-test",
        "status": TaskStatus.requested,
        "intent": TaskIntent.order,
        "priority": TaskPriority.routine,
        "description": "Please review and approve the medication order.",
        "code_text": "Approve medication request",
        "for_reference": "Patient/10001",
        "for_type": "Patient",
        "for_id": 10001,
        "for_display": "Jane Doe",
        "encounter_reference": "Encounter/20001",
        "encounter_type": TaskEncounterReferenceType.Encounter,
        "encounter_id": 20001,
        "encounter_display": "Outpatient consultation",
        "execution_period_start": D,
        "execution_period_end": D + dt.timedelta(days=1),
        "authored_on": D,
        "last_modified": D,
        "requester_reference": "Practitioner/30001",
        "requester_type": TaskRequesterReferenceType.Practitioner,
        "requester_id": 30001,
        "requester_display": "Dr. Alice Smith",
        "owner_reference": "Practitioner/30002",
        "owner_type": TaskOwnerReferenceType.Practitioner,
        "owner_id": 30002,
        "owner_display": "Dr. Bob Jones",
        "created_by": "u-test",
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = TaskModel(**fields)

    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def test_task_minimal_conformance():
    m = _task()
    fhir = to_fhir_task(m)
    assert_valid(task_pb2.Task, fhir)


def test_task_full_conformance():
    id_coding = TaskIdentifierTypeCoding(
        task_identifier_id=1,
        tenant_id="org-test",
        system="http://terminology.hl7.org/CodeSystem/v2-0203",
        code="FILL",
        display="Filler Identifier",
        created_by="u-test",
    )
    identifier = TaskIdentifier(
        id=1,
        task_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        system="urn:oid:1.2.3.4",
        value="TASK12345",
        period_start=D,
        period_end=D + dt.timedelta(days=365),
        assigner_reference="Organization/190001",
        assigner_type=OrganizationReferenceType.Organization,
        assigner_id=190001,
        assigner_display="Test Clinic",
        created_by="u-test",
    )
    identifier.type_codings = [id_coding]

    code_coding = TaskCodeCoding(
        task_pk=1,
        tenant_id="org-test",
        system="http://hl7.org/fhir/CodeSystem/task-code",
        code="approve",
        display="Activate/approve the focal resource",
        created_by="u-test",
    )

    status_reason_coding = TaskStatusReasonCoding(
        task_pk=1,
        tenant_id="org-test",
        system="http://example.org/status-reason",
        code="standard-review",
        display="Standard clinical review required",
        created_by="u-test",
    )

    business_status_coding = TaskBusinessStatusCoding(
        task_pk=1,
        tenant_id="org-test",
        system="http://example.org/business-status",
        code="waiting-on-review",
        display="Waiting on review",
        created_by="u-test",
    )

    reason_code_coding = TaskReasonCodeCoding(
        task_pk=1,
        tenant_id="org-test",
        system="http://snomed.info/sct",
        code="182888003",
        display="Medication review needed",
        created_by="u-test",
    )

    perf_coding = TaskPerformerTypeCoding(
        task_performer_type_id=1,
        tenant_id="org-test",
        system="http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
        code="RESP",
        display="Responsible Party",
        created_by="u-test",
    )
    perf_type = TaskPerformerType(
        id=1,
        task_pk=1,
        tenant_id="org-test",
        text="Responsible Doctor",
        created_by="u-test",
    )
    perf_type.codings = [perf_coding]

    based_on = TaskBasedOn(
        id=1,
        task_pk=1,
        tenant_id="org-test",
        reference_reference="ServiceRequest/80001",
        reference_type="ServiceRequest",
        reference_id=80001,
        reference_display="Lab order",
        created_by="u-test",
    )

    part_of = TaskPartOf(
        id=1,
        task_pk=1,
        tenant_id="org-test",
        reference_reference="Task/280000",
        reference_type=TaskPartOfReferenceType.Task,
        reference_id=280000,
        reference_display="Parent Task",
        created_by="u-test",
    )

    note = TaskNote(
        id=1,
        task_pk=1,
        tenant_id="org-test",
        author_string="Nurse Kelly",
        time=D,
        text="All vitals checked and normal.",
        created_by="u-test",
    )

    inp_coding = TaskInputTypeCoding(
        task_input_id=1,
        tenant_id="org-test",
        system="http://example.org/task-input",
        code="specification",
        display="Task Specification",
        created_by="u-test",
    )
    task_input = TaskInput(
        id=1,
        task_pk=1,
        tenant_id="org-test",
        type_text="Task Specification",
        value_string="Sample instructions",
        created_by="u-test",
    )
    task_input.type_codings = [inp_coding]

    out_coding = TaskOutputTypeCoding(
        task_output_id=1,
        tenant_id="org-test",
        system="http://example.org/task-output",
        code="result",
        display="Approval Decision",
        created_by="u-test",
    )
    task_output = TaskOutput(
        id=1,
        task_pk=1,
        tenant_id="org-test",
        type_text="Approval Decision",
        value_string="Approved by supervisor",
        created_by="u-test",
    )
    task_output.type_codings = [out_coding]

    restr_recip = TaskRestrictionRecipient(
        id=1,
        task_pk=1,
        tenant_id="org-test",
        reference_reference="Practitioner/30002",
        reference_type=TaskRestrictionRecipientReferenceType.Practitioner,
        reference_id=30002,
        reference_display="Dr. Bob Jones",
        created_by="u-test",
    )

    m = _task(
        instantiates_canonical="http://example.org/ActivityDefinition/ad-1",
        instantiates_uri="http://example.org/protocols/task-proto",
        focus_reference="MedicationRequest/90001",
        focus_type="MedicationRequest",
        focus_id=90001,
        focus_display="Amoxicillin 500mg prescription",
        location_reference="Location/230001",
        location_type=TaskLocationReferenceType.Location,
        location_id=230001,
        location_display="Main Clinic Room 1",
        reason_reference_reference="Condition/120001",
        reason_reference_type="Condition",
        reason_reference_id=120001,
        reason_reference_display="Bacterial infection",
        group_identifier_use=IdentifierUse.official,
        group_identifier_system="http://example.org/requisitions",
        group_identifier_value="REQ-2026-001",
        restriction_repetitions=1,
        restriction_period_start=D,
        restriction_period_end=D + dt.timedelta(days=7),
        identifiers=[identifier],
        code_codings=[code_coding],
        status_reason_codings=[status_reason_coding],
        business_status_codings=[business_status_coding],
        reason_code_codings=[reason_code_coding],
        performer_types=[perf_type],
        based_on_list=[based_on],
        part_of_list=[part_of],
        notes=[note],
        inputs=[task_input],
        outputs=[task_output],
        restriction_recipients=[restr_recip],
    )

    fhir = to_fhir_task(m)
    assert_valid(task_pb2.Task, fhir)
