"""FHIR R4 conformance for `to_fhir_procedure()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.procedure import to_fhir_procedure
from app.models.enums import (
    EncounterReferenceType,
    IdentifierUse,
    LocationReferenceType,
    OrganizationReferenceType,
)
from app.models.procedure import (
    ProcedureAsserterReferenceType,
    ProcedureAuthorReferenceType,
    ProcedureBasedOn,
    ProcedureBasedOnReferenceType,
    ProcedureBodySite,
    ProcedureBodySiteCoding,
    ProcedureCategoryCoding,
    ProcedureCodeCoding,
    ProcedureComplication,
    ProcedureComplicationCoding,
    ProcedureComplicationDetail,
    ProcedureComplicationDetailReferenceType,
    ProcedureFocalDevice,
    ProcedureFocalDeviceActionCoding,
    ProcedureFocalDeviceManipulatedReferenceType,
    ProcedureFollowUp,
    ProcedureFollowUpCoding,
    ProcedureIdentifier,
    ProcedureIdentifierTypeCoding,
    ProcedureModel,
    ProcedureNote,
    ProcedureOutcomeCoding,
    ProcedurePartOf,
    ProcedurePartOfReferenceType,
    ProcedurePerformer,
    ProcedurePerformerActorReferenceType,
    ProcedurePerformerFunctionCoding,
    ProcedureReasonCode,
    ProcedureReasonCodeCoding,
    ProcedureReasonReference,
    ProcedureReasonReferenceReferenceType,
    ProcedureRecorderReferenceType,
    ProcedureReport,
    ProcedureReportReferenceType,
    ProcedureStatus,
    ProcedureStatusReasonCoding,
    ProcedureSubjectReferenceType,
    ProcedureUsedCode,
    ProcedureUsedCodeCoding,
    ProcedureUsedReference,
    ProcedureUsedReferenceReferenceType,
)

from .support import assert_valid

procedure_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.procedure_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "based_on",
    "part_of",
    "status_reason_codings",
    "category_codings",
    "code_codings",
    "performers",
    "reason_codes",
    "reason_references",
    "body_sites",
    "outcome_codings",
    "reports",
    "complications",
    "complication_details",
    "follow_ups",
    "notes",
    "focal_devices",
    "used_references",
    "used_codes",
)


def _procedure(**overrides) -> ProcedureModel:
    fields = {
        "id": 1,
        "procedure_id": 100001,
        "tenant_id": "org-test",
        "status": ProcedureStatus.completed,
        "subject_reference": "Patient/10001",
        "subject_type": ProcedureSubjectReferenceType.Patient,
        "subject_id": 10001,
        "subject_display": "Test Patient",
        "created_by": "u-test",
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = ProcedureModel(**fields)
    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def test_procedure_minimal_conformance():
    m = _procedure()
    fhir = to_fhir_procedure(m)
    assert_valid(procedure_pb2.Procedure, fhir)


def test_procedure_performed_choices():
    # performedDateTime
    m = _procedure(performed_date_time=D)
    assert_valid(procedure_pb2.Procedure, to_fhir_procedure(m))

    # performedPeriod
    m = _procedure(performed_period_start=D, performed_period_end=D + dt.timedelta(hours=2))
    assert_valid(procedure_pb2.Procedure, to_fhir_procedure(m))

    # performedString
    m = _procedure(performed_string="approximately 2 hours ago")
    assert_valid(procedure_pb2.Procedure, to_fhir_procedure(m))

    # performedAge
    m = _procedure(performed_age={"value": 45, "unit": "years", "system": "http://unitsofmeasure.org", "code": "a"})
    assert_valid(procedure_pb2.Procedure, to_fhir_procedure(m))

    # performedRange
    m = _procedure(performed_range={"low": {"value": 1, "unit": "hours"}, "high": {"value": 2, "unit": "hours"}})
    assert_valid(procedure_pb2.Procedure, to_fhir_procedure(m))


def test_procedure_identifiers_conformance():
    ident = ProcedureIdentifier(
        procedure_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        type_text="Medical Record Number",
        system="http://hospital.example.org/proc",
        value="PROC-12345",
        period_start=D,
        period_end=D,
        assigner_reference="Organization/190001",
        assigner_type=OrganizationReferenceType.Organization,
        assigner_id=190001,
        assigner_display="Test Org",
        created_by="u-test",
    )
    ident.type_codings = [
        ProcedureIdentifierTypeCoding(
            identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="MR",
            display="Medical Record Number",
            created_by="u-test",
        )
    ]
    m = _procedure(identifiers=[ident])
    assert_valid(procedure_pb2.Procedure, to_fhir_procedure(m))


def test_procedure_single_concepts_conformance():
    m = _procedure(
        status_reason_text="Patient condition improved",
        status_reason_codings=[
            ProcedureStatusReasonCoding(
                procedure_pk=1,
                tenant_id="org-test",
                system="http://snomed.info/sct",
                code="397779007",
                display="Condition improved",
                created_by="u-test",
            )
        ],
        category_text="Surgical procedure",
        category_codings=[
            ProcedureCategoryCoding(
                procedure_pk=1,
                tenant_id="org-test",
                system="http://snomed.info/sct",
                code="387713003",
                display="Surgical procedure",
                created_by="u-test",
            )
        ],
        code_text="Appendectomy",
        code_codings=[
            ProcedureCodeCoding(
                procedure_pk=1,
                tenant_id="org-test",
                system="http://snomed.info/sct",
                code="80146002",
                display="Appendectomy",
                created_by="u-test",
            )
        ],
        outcome_text="Successful",
        outcome_codings=[
            ProcedureOutcomeCoding(
                procedure_pk=1,
                tenant_id="org-test",
                system="http://snomed.info/sct",
                code="385669000",
                display="Successful",
                created_by="u-test",
            )
        ],
    )
    assert_valid(procedure_pb2.Procedure, to_fhir_procedure(m))


def test_procedure_performers_conformance():
    p = ProcedurePerformer(
        procedure_pk=1,
        tenant_id="org-test",
        function_text="Primary surgeon",
        actor_reference="Practitioner/30001",
        actor_type=ProcedurePerformerActorReferenceType.Practitioner,
        actor_id=30001,
        actor_display="Dr. Smith",
        on_behalf_of_reference="Organization/190001",
        on_behalf_of_type=OrganizationReferenceType.Organization,
        on_behalf_of_id=190001,
        on_behalf_of_display="General Hospital",
        created_by="u-test",
    )
    p.function_codings = [
        ProcedurePerformerFunctionCoding(
            performer_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="304292004",
            display="Surgeon",
            created_by="u-test",
        )
    ]
    m = _procedure(performers=[p])
    assert_valid(procedure_pb2.Procedure, to_fhir_procedure(m))


def test_procedure_focal_device_conformance():
    fd = ProcedureFocalDevice(
        procedure_pk=1,
        tenant_id="org-test",
        action_text="Implanted",
        manipulated_reference="Device/130001",
        manipulated_type=ProcedureFocalDeviceManipulatedReferenceType.Device,
        manipulated_id=130001,
        manipulated_display="Cardiac pacemaker",
        created_by="u-test",
    )
    fd.action_codings = [
        ProcedureFocalDeviceActionCoding(
            focal_device_id=1,
            tenant_id="org-test",
            system="http://hl7.org/fhir/device-action",
            code="implanted",
            display="Implanted",
            created_by="u-test",
        )
    ]
    m = _procedure(focal_devices=[fd])
    assert_valid(procedure_pb2.Procedure, to_fhir_procedure(m))


def test_procedure_notes_conformance():
    n = ProcedureNote(
        procedure_pk=1,
        tenant_id="org-test",
        author_reference_reference="Practitioner/30001",
        author_reference_type=ProcedureAuthorReferenceType.Practitioner,
        author_reference_id=30001,
        author_reference_display="Dr. Smith",
        time=D,
        text="Procedure completed without complication.",
        created_by="u-test",
    )
    m = _procedure(notes=[n])
    assert_valid(procedure_pb2.Procedure, to_fhir_procedure(m))


def test_procedure_full_collections_conformance():
    # 0..* concepts
    rc = ProcedureReasonCode(procedure_pk=1, tenant_id="org-test", text="Acute appendicitis", created_by="u-test")
    rc.codings = [
        ProcedureReasonCodeCoding(
            reason_code_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="85189001",
            display="Acute appendicitis",
            created_by="u-test",
        )
    ]

    bs = ProcedureBodySite(procedure_pk=1, tenant_id="org-test", text="Appendix structure", created_by="u-test")
    bs.codings = [
        ProcedureBodySiteCoding(
            body_site_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="66754008",
            display="Appendix structure",
            created_by="u-test",
        )
    ]

    comp = ProcedureComplication(procedure_pk=1, tenant_id="org-test", text="Bleeding", created_by="u-test")
    comp.codings = [
        ProcedureComplicationCoding(
            complication_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="131148009",
            display="Bleeding",
            created_by="u-test",
        )
    ]

    fu = ProcedureFollowUp(procedure_pk=1, tenant_id="org-test", text="Suture removal in 10 days", created_by="u-test")
    fu.codings = [
        ProcedureFollowUpCoding(
            follow_up_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="30549001",
            display="Suture removal",
            created_by="u-test",
        )
    ]

    uc = ProcedureUsedCode(procedure_pk=1, tenant_id="org-test", text="Absorbable suture", created_by="u-test")
    uc.codings = [
        ProcedureUsedCodeCoding(
            used_code_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="111075005",
            display="Absorbable suture",
            created_by="u-test",
        )
    ]

    m = _procedure(
        instantiates_canonical=["http://example.org/fhir/PlanDefinition/420001"],
        instantiates_uri=["http://example.org/procedure/standard-protocol"],
        based_on=[
            ProcedureBasedOn(
                procedure_pk=1,
                tenant_id="org-test",
                reference_reference="CarePlan/290001",
                reference_type=ProcedureBasedOnReferenceType.CarePlan,
                reference_id=290001,
                created_by="u-test",
            )
        ],
        part_of=[
            ProcedurePartOf(
                procedure_pk=1,
                tenant_id="org-test",
                reference_reference="Procedure/100000",
                reference_type=ProcedurePartOfReferenceType.Procedure,
                reference_id=100000,
                created_by="u-test",
            )
        ],
        encounter_reference="Encounter/20001",
        encounter_type=EncounterReferenceType.Encounter,
        encounter_id=20001,
        encounter_display="Emergency encounter",
        recorder_reference="Practitioner/30001",
        recorder_type=ProcedureRecorderReferenceType.Practitioner,
        recorder_id=30001,
        recorder_display="Dr. Smith",
        asserter_reference="Practitioner/30001",
        asserter_type=ProcedureAsserterReferenceType.Practitioner,
        asserter_id=30001,
        asserter_display="Dr. Smith",
        location_reference="Location/230001",
        location_type=LocationReferenceType.Location,
        location_id=230001,
        location_display="OR 1",
        reason_codes=[rc],
        reason_references=[
            ProcedureReasonReference(
                procedure_pk=1,
                tenant_id="org-test",
                reference_reference="Condition/120001",
                reference_type=ProcedureReasonReferenceReferenceType.Condition,
                reference_id=120001,
                created_by="u-test",
            )
        ],
        body_sites=[bs],
        reports=[
            ProcedureReport(
                procedure_pk=1,
                tenant_id="org-test",
                reference_reference="DiagnosticReport/110001",
                reference_type=ProcedureReportReferenceType.DiagnosticReport,
                reference_id=110001,
                created_by="u-test",
            )
        ],
        complications=[comp],
        complication_details=[
            ProcedureComplicationDetail(
                procedure_pk=1,
                tenant_id="org-test",
                reference_reference="Condition/120002",
                reference_type=ProcedureComplicationDetailReferenceType.Condition,
                reference_id=120002,
                created_by="u-test",
            )
        ],
        follow_ups=[fu],
        used_references=[
            ProcedureUsedReference(
                procedure_pk=1,
                tenant_id="org-test",
                reference_reference="Device/130001",
                reference_type=ProcedureUsedReferenceReferenceType.Device,
                reference_id=130001,
                created_by="u-test",
            )
        ],
        used_codes=[uc],
    )
    assert_valid(procedure_pb2.Procedure, to_fhir_procedure(m))
