"""FHIR R4 conformance for `to_fhir_measure()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.measure import to_fhir_measure
from app.models.enums import IdentifierUse
from app.schemas.enums import ContactPointSystem, ContactPointUse
from app.models.measure import (
    MeasureCompositeScoringCoding,
    MeasureContact,
    MeasureContactRole,
    MeasureContactTelecom,
    MeasureGroup,
    MeasureGroupCodeCoding,
    MeasureGroupPopulation,
    MeasureGroupPopulationCodeCoding,
    MeasureGroupStratifier,
    MeasureGroupStratifierCodeCoding,
    MeasureGroupStratifierComponent,
    MeasureGroupStratifierComponentCodeCoding,
    MeasureIdentifier,
    MeasureIdentifierTypeCoding,
    MeasureImprovementNotationCoding,
    MeasureJurisdiction,
    MeasureJurisdictionCoding,
    MeasureModel,
    MeasureQuantityComparator,
    MeasureRelatedArtifact,
    MeasureRelatedArtifactType,
    MeasureScoringCoding,
    MeasureStatus,
    MeasureSubjectCoding,
    MeasureSubjectReferenceType,
    MeasureSupplementalData,
    MeasureSupplementalDataCodeCoding,
    MeasureSupplementalDataUsage,
    MeasureSupplementalDataUsageCoding,
    MeasureTopic,
    MeasureTopicCoding,
    MeasureType,
    MeasureTypeCoding,
    MeasureUseContext,
    MeasureUseContextValueCoding,
    MeasureUseContextValueReferenceType,
)

from .support import assert_valid

measure_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.measure_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 2, 1, 10, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "subject_codings",
    "contacts",
    "use_contexts",
    "jurisdictions",
    "topics",
    "related_artifacts",
    "scoring_codings",
    "composite_scoring_codings",
    "types",
    "improvement_notation_codings",
    "groups",
    "supplemental_data",
)


def _measure(**overrides) -> MeasureModel:
    fields = {
        "id": 1,
        "measure_id": 560001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "status": MeasureStatus.draft,
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = MeasureModel(**fields)

    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def test_minimal_measure_conforms():
    m = _measure()
    resource = to_fhir_measure(m)
    assert_valid(measure_pb2.Measure, resource)


def test_full_measure_conforms():
    id_coding = MeasureIdentifierTypeCoding(
        system="http://terminology.hl7.org/CodeSystem/v2-0203",
        code="FILL",
        display="Filler Identifier",
    )
    ident = MeasureIdentifier(
        use=IdentifierUse.official,
        system="http://example.org/fhir/measure",
        value="meas-12345",
        period_start=D,
        period_end=D,
        assigner_reference="Organization/190001",
        type_text="Filler",
    )
    ident.type_codings = [id_coding]

    subj_coding = MeasureSubjectCoding(
        system="http://hl7.org/fhir/resource-types",
        code="Patient",
        display="Patient",
    )

    t = MeasureContactTelecom(
        system=ContactPointSystem.phone,
        value="555-1234",
        use=ContactPointUse.work,
        rank=1,
    )
    c_contact = MeasureContact(
        role=MeasureContactRole.contact,
        name="Clinical Quality Lead",
    )
    c_contact.telecoms = [t]

    c_author = MeasureContact(
        role=MeasureContactRole.author,
        name="Dr. Author",
    )
    c_editor = MeasureContact(
        role=MeasureContactRole.editor,
        name="Dr. Editor",
    )
    c_reviewer = MeasureContact(
        role=MeasureContactRole.reviewer,
        name="Dr. Reviewer",
    )
    c_endorser = MeasureContact(
        role=MeasureContactRole.endorser,
        name="Quality Board",
    )

    uc1 = MeasureUseContext(
        system="http://terminology.hl7.org/CodeSystem/usage-context-type",
        code="focus",
        display="Clinical Focus",
        value_codeable_concept_text="Cardiology",
    )
    uc1.value_codings = [
        MeasureUseContextValueCoding(
            system="http://snomed.info/sct",
            code="394579002",
            display="Cardiology",
        )
    ]

    uc2 = MeasureUseContext(
        system="http://terminology.hl7.org/CodeSystem/usage-context-type",
        code="age",
        display="Age",
        value_quantity_value=18,
        value_quantity_comparator=MeasureQuantityComparator.ge,
        value_quantity_unit="a",
        value_quantity_system="http://unitsofmeasure.org",
        value_quantity_code="a",
    )

    uc3 = MeasureUseContext(
        system="http://terminology.hl7.org/CodeSystem/usage-context-type",
        code="age",
        display="Age Range",
        value_range_low_value=18,
        value_range_low_unit="a",
        value_range_high_value=65,
        value_range_high_unit="a",
    )

    uc4 = MeasureUseContext(
        system="http://terminology.hl7.org/CodeSystem/usage-context-type",
        code="venue",
        display="Clinical Venue",
        value_reference_type=MeasureUseContextValueReferenceType.Location,
        value_reference_id=230001,
        value_reference_display="Cardiology Clinic",
    )

    jur = MeasureJurisdiction(text="US")
    jur.codings = [
        MeasureJurisdictionCoding(
            system="urn:iso:std:iso:3166",
            code="US",
            display="United States of America",
        )
    ]

    top = MeasureTopic(text="Hypertension")
    top.codings = [
        MeasureTopicCoding(
            system="http://snomed.info/sct",
            code="38341003",
            display="Hypertensive disorder",
        )
    ]

    ra = MeasureRelatedArtifact(
        type=MeasureRelatedArtifactType.depends_on,
        label="CQM Logic",
        display="Clinical Quality Measure Logic Library",
        url="http://example.org/fhir/Library/example-logic",
    )

    scoring_coding = MeasureScoringCoding(
        system="http://terminology.hl7.org/CodeSystem/measure-scoring",
        code="proportion",
        display="Proportion",
    )

    comp_scoring_coding = MeasureCompositeScoringCoding(
        system="http://terminology.hl7.org/CodeSystem/composite-measure-scoring",
        code="linear",
        display="Linear",
    )

    mtype = MeasureType(text="Process")
    mtype.codings = [
        MeasureTypeCoding(
            system="http://terminology.hl7.org/CodeSystem/measure-type",
            code="process",
            display="Process",
        )
    ]

    imp_not_coding = MeasureImprovementNotationCoding(
        system="http://terminology.hl7.org/CodeSystem/measure-improvement-notation",
        code="increase",
        display="Increased score indicates improvement",
    )

    # Group
    grp = MeasureGroup(
        description="Main Population Group",
        code_text="Hypertension Control",
    )
    grp.code_codings = [
        MeasureGroupCodeCoding(
            system="http://example.org/fhir/measure-group",
            code="htn-control",
            display="Hypertension Control",
        )
    ]

    pop = MeasureGroupPopulation(
        description="Initial Population",
        code_text="Initial Population",
        criteria_language="text/cql",
        criteria_expression="Initial Population",
    )
    pop.code_codings = [
        MeasureGroupPopulationCodeCoding(
            system="http://terminology.hl7.org/CodeSystem/measure-population",
            code="initial-population",
            display="Initial Population",
        )
    ]
    grp.populations = [pop]

    comp = MeasureGroupStratifierComponent(
        description="Gender Component",
        code_text="Gender",
        criteria_language="text/cql",
        criteria_expression="Patient.gender",
    )
    comp.code_codings = [
        MeasureGroupStratifierComponentCodeCoding(
            system="http://example.org/fhir/stratifier-component",
            code="gender",
            display="Gender",
        )
    ]

    strat = MeasureGroupStratifier(
        description="Age Stratifier",
        code_text="Age Group",
        criteria_language="text/cql",
        criteria_expression="Age Stratifier",
    )
    strat.code_codings = [
        MeasureGroupStratifierCodeCoding(
            system="http://example.org/fhir/stratifier",
            code="age-group",
            display="Age Group",
        )
    ]
    strat.components = [comp]
    grp.stratifiers = [strat]

    # Supplemental Data
    sd = MeasureSupplementalData(
        description="Payer Information",
        code_text="Payer",
        criteria_language="text/cql",
        criteria_expression="Coverage.payer",
    )
    sd.code_codings = [
        MeasureSupplementalDataCodeCoding(
            system="http://example.org/fhir/supplemental-data",
            code="payer",
            display="Payer",
        )
    ]
    sd_usage = MeasureSupplementalDataUsage(text="Risk Adjustment")
    sd_usage.codings = [
        MeasureSupplementalDataUsageCoding(
            system="http://terminology.hl7.org/CodeSystem/measure-data-usage",
            code="risk-adjustment-factor",
            display="Risk Adjustment Factor",
        )
    ]
    sd.usages = [sd_usage]

    m = _measure(
        url="http://example.org/fhir/Measure/example",
        version="1.0.0",
        name="ExampleMeasure",
        title="Example Measure",
        subtitle="Subtitle for Example Measure",
        experimental=True,
        date=D,
        publisher="Example Health System",
        description="A measure for testing hypertension control.",
        purpose="To track hypertension control in patients.",
        usage="Used annually by primary care physicians.",
        copyright="Copyright 2026 Example Health System",
        approval_date=dt.date(2026, 1, 15),
        last_review_date=dt.date(2026, 1, 20),
        effective_period_start=D,
        effective_period_end=D,
        library=["http://example.org/fhir/Library/example-logic"],
        disclaimer="None",
        scoring_text="Proportion",
        composite_scoring_text="Linear",
        risk_adjustment="None",
        rate_aggregation="None",
        rationale="Hypertension is a major risk factor for cardiovascular disease.",
        clinical_recommendation_statement="Screen adults for hypertension.",
        improvement_notation_text="Increase",
        definition=["Hypertension: Systolic BP >= 140 or Diastolic BP >= 90"],
        guidance="Follow clinical practice guidelines.",
        identifiers=[ident],
        subject_codings=[subj_coding],
        subject_codeable_concept_text="Patient",
        contacts=[c_contact, c_author, c_editor, c_reviewer, c_endorser],
        use_contexts=[uc1, uc2, uc3, uc4],
        jurisdictions=[jur],
        topics=[top],
        related_artifacts=[ra],
        scoring_codings=[scoring_coding],
        composite_scoring_codings=[comp_scoring_coding],
        types=[mtype],
        improvement_notation_codings=[imp_not_coding],
        groups=[grp],
        supplemental_data=[sd],
    )

    resource = to_fhir_measure(m)
    assert_valid(measure_pb2.Measure, resource)
