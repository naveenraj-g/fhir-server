"""The shared write-time reference check: which references it finds, and which types it checks."""

import pytest

from app.repository._reference_check import checkable_types, find_local_references

TYPES = frozenset({"Patient", "CareTeam", "Organization", "Observation"})


def _found(document):
    return find_local_references(document, TYPES)


def test_finds_a_top_level_reference_with_its_path():
    assert _found({"subject": {"reference": "Patient/10001"}}) == [
        ("subject", "Patient", 10001)
    ]


def test_finds_references_in_nested_lists_with_indexes():
    document = {
        "activity": [
            {"reference": {"reference": "Observation/5"}},
            {"detail": {"performer": [{"reference": "CareTeam/390001"}]}},
        ]
    }
    assert _found(document) == [
        ("activity[0].reference", "Observation", 5),
        ("activity[1].detail.performer[0]", "CareTeam", 390001),
    ]


def test_finds_identifier_assigner_note_authors_and_extension_references():
    document = {
        "identifier": [{"assigner": {"reference": "Organization/190001"}}],
        "note": [{"authorReference": {"reference": "Patient/1"}, "text": "x"}],
        "extension": [{"url": "u", "valueReference": {"reference": "Organization/2"}}],
    }
    assert {(p, t, i) for p, t, i in _found(document)} == {
        ("identifier[0].assigner", "Organization", 190001),
        ("note[0].authorReference", "Patient", 1),
        ("extension[0].valueReference", "Organization", 2),
    }


def test_finds_references_inside_contained_resources():
    document = {
        "contained": [
            {"resourceType": "Observation", "subject": {"reference": "Patient/3"}}
        ]
    }
    assert _found(document) == [("contained[0].subject", "Patient", 3)]


@pytest.mark.parametrize(
    "reference",
    [
        "https://other.example.org/fhir/Patient/1",  # absolute URL: another system
        "#contained-1",  # contained
        "Patient/abc",  # not a numeric public id
        "Patient/",  # empty id
        "patient/1",  # not a resource type name
        "Goal/460001",  # a type this server does not have (here: not in TYPES)
        "Device/5",  # likewise
        "just text",
        "",
    ],
)
def test_leaves_everything_else_alone(reference):
    assert _found({"subject": {"reference": reference}}) == []


def test_a_reference_with_only_type_display_or_identifier_is_left_alone():
    document = {
        "subject": {"type": "Patient", "display": "Jane"},
        "performer": [{"identifier": {"system": "urn:x", "value": "1"}}],
    }
    assert _found(document) == []


def test_a_version_specific_relative_reference_is_found():
    assert _found({"subject": {"reference": "Patient/1/_history/2"}}) == [
        ("subject", "Patient", 1)
    ]


def test_a_non_string_reference_is_ignored_not_crashed_on():
    assert _found({"subject": {"reference": 5}, "x": {"reference": None}}) == []


def test_the_same_target_is_reported_at_every_path():
    document = {
        "subject": {"reference": "Patient/1"},
        "note": [{"authorReference": {"reference": "Patient/1"}}],
    }
    assert [p for p, *_ in _found(document)] == ["subject", "note[0].authorReference"]


def test_checkable_types_are_the_rebuilt_content_based_resources():
    types = checkable_types()
    # rebuilt resources are checked, including the ones added recently
    assert {
        "Patient",
        "Observation",
        "CareTeam",
        "CarePlan",
        "Group",
        "EpisodeOfCare",
        "DocumentReference",
        "Goal",
        "Task",
        "Flag",
        "Consent",
        "Communication",
        "CommunicationRequest",
        "ActivityDefinition",
        "PlanDefinition",
        "ObservationDefinition",
    } <= types
    # the registry still lists old resources whose routes are off: not checked yet
    # not a resource this server has at all
    assert "Device" not in types
