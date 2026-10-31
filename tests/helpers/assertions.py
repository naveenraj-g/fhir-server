"""Shared assertion helpers for FHIR patient responses."""


def assert_plain_plan_definition(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) plan_definition response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected plan_definition.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_plan_definition(data: dict, **expected) -> None:
    """Assert fields on a FHIR plan_definition response."""
    assert data.get("resourceType") == "PlanDefinition", (
        f"expected resourceType=PlanDefinition, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected plan_definition.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_activity_definition(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) activity_definition response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected activity_definition.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_activity_definition(data: dict, **expected) -> None:
    """Assert fields on a FHIR activity_definition response."""
    assert data.get("resourceType") == "ActivityDefinition", (
        f"expected resourceType=ActivityDefinition, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected activity_definition.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_observation_definition(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) observation_definition response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected observation_definition.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_observation_definition(data: dict, **expected) -> None:
    """Assert fields on a FHIR observation_definition response."""
    assert data.get("resourceType") == "ObservationDefinition", (
        f"expected resourceType=ObservationDefinition, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected observation_definition.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_episode_of_care(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) episode_of_care response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected episode_of_care.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_episode_of_care(data: dict, **expected) -> None:
    """Assert fields on a FHIR episode_of_care response."""
    assert data.get("resourceType") == "EpisodeOfCare", (
        f"expected resourceType=EpisodeOfCare, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected episode_of_care.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_care_team(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) care_team response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected care_team.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_care_team(data: dict, **expected) -> None:
    """Assert fields on a FHIR care_team response."""
    assert data.get("resourceType") == "CareTeam", (
        f"expected resourceType=CareTeam, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected care_team.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_care_plan(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) care_plan response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected care_plan.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_care_plan(data: dict, **expected) -> None:
    """Assert fields on a FHIR care_plan response."""
    assert data.get("resourceType") == "CarePlan", (
        f"expected resourceType=CarePlan, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected care_plan.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_document_reference(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) document_reference response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected document_reference.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_document_reference(data: dict, **expected) -> None:
    """Assert fields on a FHIR document_reference response."""
    assert data.get("resourceType") == "DocumentReference", (
        f"expected resourceType=DocumentReference, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected document_reference.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_specimen(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) specimen response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected specimen.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_specimen(data: dict, **expected) -> None:
    """Assert fields on a FHIR specimen response."""
    assert data.get("resourceType") == "Specimen", (
        f"expected resourceType=Specimen, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected specimen.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_condition(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) condition response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected condition.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_condition(data: dict, **expected) -> None:
    """Assert fields on a FHIR condition response."""
    assert data.get("resourceType") == "Condition", (
        f"expected resourceType=Condition, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected condition.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_patient(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) patient response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected patient.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_patient(data: dict, **expected) -> None:
    """Assert fields on a FHIR patient response."""
    assert data.get("resourceType") == "Patient", (
        f"expected resourceType=Patient, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected patient.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_practitioner(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) practitioner response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected practitioner.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_practitioner(data: dict, **expected) -> None:
    """Assert fields on a FHIR practitioner response."""
    assert data.get("resourceType") == "Practitioner", (
        f"expected resourceType=Practitioner, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected practitioner.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_appointment(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) appointment response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected appointment.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_appointment(data: dict, **expected) -> None:
    """Assert fields on a FHIR appointment response."""
    assert data.get("resourceType") == "Appointment", (
        f"expected resourceType=Appointment, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected appointment.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_organization(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) organization response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected organization.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_organization(data: dict, **expected) -> None:
    """Assert fields on a FHIR organization response."""
    assert data.get("resourceType") == "Organization", (
        f"expected resourceType=Organization, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected organization.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_healthcare_service(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) healthcare service response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected healthcare_service.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_healthcare_service(data: dict, **expected) -> None:
    """Assert fields on a FHIR healthcare service response."""
    assert data.get("resourceType") == "HealthcareService", (
        f"expected resourceType=HealthcareService, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected healthcare_service.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_practitioner_role(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) practitioner role response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected practitioner_role.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_practitioner_role(data: dict, **expected) -> None:
    """Assert fields on a FHIR practitioner role response."""
    assert data.get("resourceType") == "PractitionerRole", (
        f"expected resourceType=PractitionerRole, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected practitioner_role.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_schedule(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) schedule response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected schedule.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_schedule(data: dict, **expected) -> None:
    """Assert fields on a FHIR schedule response."""
    assert data.get("resourceType") == "Schedule", (
        f"expected resourceType=Schedule, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected schedule.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_slot(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) slot response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected slot.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_slot(data: dict, **expected) -> None:
    """Assert fields on a FHIR slot response."""
    assert data.get("resourceType") == "Slot", (
        f"expected resourceType=Slot, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected slot.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_procedure(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) procedure response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected procedure.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_procedure(data: dict, **expected) -> None:
    """Assert fields on a FHIR procedure response."""
    assert data.get("resourceType") == "Procedure", (
        f"expected resourceType=Procedure, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected procedure.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_group(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) group response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected group.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_allergy_intolerance(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) allergy_intolerance response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected allergy_intolerance.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_allergy_intolerance(data: dict, **expected) -> None:
    """Assert fields on a FHIR allergy_intolerance response."""
    assert data.get("resourceType") == "AllergyIntolerance", (
        f"expected resourceType=AllergyIntolerance, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected allergy_intolerance.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_consent(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) consent response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected consent.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_consent(data: dict, **expected) -> None:
    """Assert fields on a FHIR consent response."""
    assert data.get("resourceType") == "Consent", (
        f"expected resourceType=Consent, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected consent.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_group(data: dict, **expected) -> None:
    """Assert fields on a FHIR group response."""
    assert data.get("resourceType") == "Group", (
        f"expected resourceType=Group, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected group.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_related_person(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) related_person response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected related_person.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_related_person(data: dict, **expected) -> None:
    """Assert fields on a FHIR related_person response."""
    assert data.get("resourceType") == "RelatedPerson", (
        f"expected resourceType=RelatedPerson, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected related_person.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_flag(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) flag response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected flag.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_flag(data: dict, **expected) -> None:
    """Assert fields on a FHIR flag response."""
    assert data.get("resourceType") == "Flag", (
        f"expected resourceType=Flag, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected flag.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_task(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) task response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected task.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_task(data: dict, **expected) -> None:
    """Assert fields on a FHIR task response."""
    assert data.get("resourceType") == "Task", (
        f"expected resourceType=Task, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected task.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_paginated(data: dict, *, min_total: int = 1) -> None:
    """Assert structure of a plain paginated list response."""
    assert "total" in data, "paginated response must have 'total'"
    assert "limit" in data, "paginated response must have 'limit'"
    assert "offset" in data, "paginated response must have 'offset'"
    assert "data" in data, "paginated response must have 'data'"
    assert isinstance(data["data"], list), "'data' must be a list"
    assert data["total"] >= min_total, (
        f"expected total >= {min_total}, got {data['total']}"
    )


def assert_fhir_bundle(data: dict, *, min_total: int = 1) -> None:
    """Assert structure of a FHIR Bundle response."""
    assert data.get("resourceType") == "Bundle", (
        f"expected resourceType=Bundle, got {data.get('resourceType')!r}"
    )
    assert data.get("type") == "searchset"
    assert "entry" in data, "Bundle must have 'entry'"
    assert isinstance(data["entry"], list)
    assert data.get("total", 0) >= min_total, (
        f"expected total >= {min_total}, got {data.get('total')}"
    )


def assert_operation_outcome(data: dict, expected_status: int, response_status: int) -> None:
    """Assert that an error response is a valid FHIR OperationOutcome."""
    assert response_status == expected_status, (
        f"expected HTTP {expected_status}, got {response_status}"
    )
    assert data.get("resourceType") == "OperationOutcome", (
        f"expected OperationOutcome, got {data.get('resourceType')!r}"
    )
    assert len(data.get("issue", [])) > 0, "OperationOutcome must have at least one issue"


def assert_plain_goal(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) goal response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected goal.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_goal(data: dict, **expected) -> None:
    """Assert fields on a FHIR goal response."""
    assert data.get("resourceType") == "Goal", (
        f"expected resourceType=Goal, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected goal.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_plain_communication_request(data: dict, **expected) -> None:
    """Assert fields on a plain (snake_case) communication_request response."""
    assert data.get("id") is not None, "plain response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected communication_request.{field}={value!r}, got {data.get(field)!r}"
        )


def assert_fhir_communication_request(data: dict, **expected) -> None:
    """Assert fields on a FHIR communication_request response."""
    assert data.get("resourceType") == "CommunicationRequest", (
        f"expected resourceType=CommunicationRequest, got {data.get('resourceType')!r}"
    )
    assert data.get("id") is not None, "FHIR response must have 'id'"
    for field, value in expected.items():
        assert data.get(field) == value, (
            f"expected communication_request.{field}={value!r}, got {data.get(field)!r}"
        )
