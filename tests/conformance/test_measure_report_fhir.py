"""FHIR R4 conformance for `to_fhir_measure_report()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.measure_report import to_fhir_measure_report
from app.models.enums import IdentifierUse
from app.models.measure_report import (
    MeasureReportEvaluatedResource,
    MeasureReportGroup,
    MeasureReportGroupCodeCoding,
    MeasureReportGroupPopulation,
    MeasureReportGroupPopulationCodeCoding,
    MeasureReportGroupStratifier,
    MeasureReportGroupStratifierCode,
    MeasureReportGroupStratifierCodeCoding,
    MeasureReportGroupStratifierStratum,
    MeasureReportGroupStratifierStratumComponent,
    MeasureReportGroupStratifierStratumComponentCodeCoding,
    MeasureReportGroupStratifierStratumComponentValueCoding,
    MeasureReportGroupStratifierStratumPopulation,
    MeasureReportGroupStratifierStratumPopulationCodeCoding,
    MeasureReportGroupStratifierStratumValueCoding,
    MeasureReportIdentifier,
    MeasureReportIdentifierTypeCoding,
    MeasureReportImprovementNotationCoding,
    MeasureReportModel,
    MeasureReportQuantityComparator,
    MeasureReportReporterReferenceType,
    MeasureReportStatus,
    MeasureReportSubjectReferenceType,
    MeasureReportSubjectResultsReferenceType,
    MeasureReportType,
)

from .support import assert_valid

measure_report_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.measure_report_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 2, 1, 10, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "improvement_notation_coding",
    "evaluated_resources",
    "groups",
)


def _measure_report(**overrides) -> MeasureReportModel:
    fields = {
        "id": 1,
        "measure_report_id": 570001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "status": MeasureReportStatus.complete,
        "type": MeasureReportType.summary,
        "measure": "http://example.org/fhir/Measure/exclusive-breastfeeding-measure",
        "period_start": D,
        "period_end": D,
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = MeasureReportModel(**fields)

    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def test_minimal_measure_report_conforms():
    mr = _measure_report()
    resource = to_fhir_measure_report(mr)
    assert_valid(measure_report_pb2.MeasureReport, resource)


def test_full_measure_report_conforms():
    id_coding = MeasureReportIdentifierTypeCoding(
        system="http://terminology.hl7.org/CodeSystem/v2-0203",
        code="FILL",
        display="Filler Identifier",
    )
    ident = MeasureReportIdentifier(
        use=IdentifierUse.official,
        system="http://example.org/fhir/measurereport",
        value="mr-12345",
        period_start=D,
        period_end=D,
        assigner_reference="Organization/190001",
        type_text="Filler",
    )
    ident.type_coding = [id_coding]

    imp_coding = MeasureReportImprovementNotationCoding(
        system="http://terminology.hl7.org/CodeSystem/measure-improvement-notation",
        code="increase",
        display="Increased score indicates improvement",
    )

    eval_res = MeasureReportEvaluatedResource(
        evaluated_resource_reference="Observation/160001",
        evaluated_resource_display="Newborn birth weight",
    )

    grp_coding = MeasureReportGroupCodeCoding(
        system="http://example.org/group-codes",
        code="grp-1",
        display="Primary Group",
    )

    pop_coding = MeasureReportGroupPopulationCodeCoding(
        system="http://terminology.hl7.org/CodeSystem/measure-population",
        code="initial-population",
        display="Initial Population",
    )
    pop = MeasureReportGroupPopulation(
        code_text="Initial Population",
        count=100,
        subject_results_reference="List/123",
    )
    pop.code_coding = [pop_coding]

    strat_code_coding = MeasureReportGroupStratifierCodeCoding(
        system="http://example.org/stratifier-code",
        code="gender",
        display="Gender Stratifier",
    )
    strat_code = MeasureReportGroupStratifierCode(
        code_text="Gender",
    )
    strat_code.coding = [strat_code_coding]

    stratum_val_coding = MeasureReportGroupStratifierStratumValueCoding(
        system="http://hl7.org/fhir/administrative-gender",
        code="male",
        display="Male",
    )

    comp_c_coding = MeasureReportGroupStratifierStratumComponentCodeCoding(
        system="http://example.org/comp-code",
        code="age-group",
        display="Age Group",
    )
    comp_v_coding = MeasureReportGroupStratifierStratumComponentValueCoding(
        system="http://example.org/age-ranges",
        code="newborn",
        display="Newborn",
    )
    comp = MeasureReportGroupStratifierStratumComponent(
        code_text="Age Group",
        value_text="Newborn",
    )
    comp.code_coding = [comp_c_coding]
    comp.value_coding = [comp_v_coding]

    strat_pop_coding = MeasureReportGroupStratifierStratumPopulationCodeCoding(
        system="http://terminology.hl7.org/CodeSystem/measure-population",
        code="initial-population",
        display="Initial Population",
    )
    strat_pop = MeasureReportGroupStratifierStratumPopulation(
        code_text="Initial Population",
        count=50,
        subject_results_reference="List/124",
    )
    strat_pop.code_coding = [strat_pop_coding]

    stratum = MeasureReportGroupStratifierStratum(
        value_text="Male",
        measure_score_value=0.85,
        measure_score_comparator=MeasureReportQuantityComparator.ge,
        measure_score_unit="%",
        measure_score_system="http://unitsofmeasure.org",
        measure_score_code="%",
    )
    stratum.value_coding = [stratum_val_coding]
    stratum.components = [comp]
    stratum.populations = [strat_pop]

    stratifier = MeasureReportGroupStratifier()
    stratifier.codes = [strat_code]
    stratifier.strata = [stratum]

    grp = MeasureReportGroup(
        code_text="Primary Group",
        measure_score_value=0.8,
        measure_score_comparator=MeasureReportQuantityComparator.ge,
        measure_score_unit="%",
        measure_score_system="http://unitsofmeasure.org",
        measure_score_code="%",
    )
    grp.code_coding = [grp_coding]
    grp.populations = [pop]
    grp.stratifiers = [stratifier]

    mr = _measure_report(
        subject_reference="Patient/10001",
        subject_type=MeasureReportSubjectReferenceType.Patient,
        subject_id=10001,
        subject_display="Baby Boy",
        reporter_reference="Practitioner/30001",
        reporter_type=MeasureReportReporterReferenceType.Practitioner,
        reporter_id=30001,
        reporter_display="Dr. Lead",
        date=D,
        improvement_notation_text="Increased score indicates improvement",
        identifiers=[ident],
        improvement_notation_coding=[imp_coding],
        evaluated_resources=[eval_res],
        groups=[grp],
    )

    resource = to_fhir_measure_report(mr)
    assert_valid(measure_report_pb2.MeasureReport, resource)
