"""FHIR R4 conformance for `to_fhir_diagnostic_report()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.diagnostic_report import to_fhir_diagnostic_report
from app.models.diagnostic_report import (
    DiagnosticReportActorReferenceType,
    DiagnosticReportCodeCoding,
    DiagnosticReportIdentifier,
    DiagnosticReportIdentifierTypeCoding,
    DiagnosticReportModel,
    DiagnosticReportPerformer,
    DiagnosticReportResult,
    DiagnosticReportStatus,
    DiagnosticReportSubjectReferenceType,
)
from app.models.enums import IdentifierUse, ObservationReferenceType

from .support import assert_valid

diagnostic_report_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.diagnostic_report_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "code_codings",
    "identifiers",
    "based_ons",
    "categories",
    "performers",
    "results_interpreters",
    "specimens",
    "results",
    "imaging_studies",
    "media",
    "conclusion_codes",
    "presented_forms",
)


def _diagnostic_report(**overrides) -> DiagnosticReportModel:
    fields = {
        "id": 1,
        "diagnostic_report_id": 110001,
        "tenant_id": "org-test",
        "status": DiagnosticReportStatus.final,
        "code_text": "Complete blood count",
        "subject_reference": "Patient/10001",
        "subject_type": DiagnosticReportSubjectReferenceType.Patient,
        "subject_id": 10001,
        "subject_display": "Jane Doe",
        "created_by": "u-test",
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = DiagnosticReportModel(**fields)

    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def test_diagnostic_report_minimal_conformance():
    code_coding = DiagnosticReportCodeCoding(
        id=1,
        diagnostic_report_pk=1,
        tenant_id="org-test",
        system="http://loinc.org",
        code="58410-2",
        display="Complete blood count (hemogram) panel",
        created_by="u-test",
        created_at=D,
    )
    m = _diagnostic_report(code_codings=[code_coding])
    fhir = to_fhir_diagnostic_report(m)
    assert_valid(diagnostic_report_pb2.DiagnosticReport, fhir)


def test_diagnostic_report_full_conformance():
    code_coding = DiagnosticReportCodeCoding(
        id=1,
        diagnostic_report_pk=1,
        tenant_id="org-test",
        system="http://loinc.org",
        code="58410-2",
        display="Complete blood count (hemogram) panel",
        created_by="u-test",
        created_at=D,
    )
    ident = DiagnosticReportIdentifier(
        id=1,
        diagnostic_report_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        system="http://hospital.example.org",
        value="DR-001",
        created_by="u-test",
        created_at=D,
    )
    ident.type_codings = [
        DiagnosticReportIdentifierTypeCoding(
            id=1,
            diagnostic_report_identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="FILL",
            display="Filler Identifier",
            created_by="u-test",
            created_at=D,
        )
    ]
    performer = DiagnosticReportPerformer(
        id=1,
        diagnostic_report_pk=1,
        tenant_id="org-test",
        reference_reference="Practitioner/30001",
        reference_type=DiagnosticReportActorReferenceType.Practitioner,
        reference_id=30001,
        reference_display="Dr. Smith",
        created_by="u-test",
        created_at=D,
    )
    res = DiagnosticReportResult(
        id=1,
        diagnostic_report_pk=1,
        tenant_id="org-test",
        reference_reference="Observation/160001",
        reference_type=ObservationReferenceType.Observation,
        reference_id=160001,
        reference_display="Hemoglobin level",
        created_by="u-test",
        created_at=D,
    )
    m = _diagnostic_report(
        effective_date_time=D,
        conclusion="Normal results",
        code_codings=[code_coding],
        identifiers=[ident],
        performers=[performer],
        results=[res],
    )
    fhir = to_fhir_diagnostic_report(m)
    assert_valid(diagnostic_report_pb2.DiagnosticReport, fhir)


def test_diagnostic_report_reference_fallback_identifiers():
    code_coding = DiagnosticReportCodeCoding(
        id=1,
        diagnostic_report_pk=1,
        tenant_id="org-test",
        system="http://loinc.org",
        code="58410-2",
        display="Complete blood count (hemogram) panel",
        created_by="u-test",
        created_at=D,
    )
    ident = DiagnosticReportIdentifier(
        id=1,
        diagnostic_report_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        system="http://hospital.example.org",
        value="DR-001",
        assigner_reference=None,
        assigner_type=None,
        assigner_id=None,
        assigner_identifier_system="http://hospital.example.org/orgs",
        assigner_identifier_value="ORG-1111",
        created_by="u-test",
        created_at=D,
    )
    performer = DiagnosticReportPerformer(
        id=1,
        diagnostic_report_pk=1,
        tenant_id="org-test",
        reference_reference=None,
        reference_type=None,
        reference_id=None,
        reference_identifier_system="http://hospital.example.org/practitioners",
        reference_identifier_value="PRAC-7777",
        created_by="u-test",
        created_at=D,
    )
    m = _diagnostic_report(
        code_codings=[code_coding],
        subject_reference=None,
        subject_type=None,
        subject_id=None,
        subject_identifier_system="http://hospital.example.org/patients",
        subject_identifier_value="PAT-9999",
        subject_identifier_use=IdentifierUse.official,
        encounter_reference=None,
        encounter_type=None,
        encounter_id=None,
        encounter_identifier_system="http://hospital.example.org/encounters",
        encounter_identifier_value="ENC-8888",
        identifiers=[ident],
        performers=[performer],
    )
    out = to_fhir_diagnostic_report(m)
    assert out["subject"]["identifier"]["value"] == "PAT-9999"
    assert out["encounter"]["identifier"]["value"] == "ENC-8888"
    assert out["identifier"][0]["assigner"]["identifier"]["value"] == "ORG-1111"
    assert out["performer"][0]["identifier"]["value"] == "PRAC-7777"
    assert_valid(diagnostic_report_pb2.DiagnosticReport, out)
