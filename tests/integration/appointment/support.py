from datetime import datetime, timezone

BASE = "/api/fhir/v1/appointments"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}
PLAIN_ACCEPT = {"Accept": "application/json"}

D = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc).isoformat()
D2 = datetime(2026, 6, 1, 9, 30, tzinfo=timezone.utc).isoformat()


def minimal_appointment() -> dict:
    return {
        "status": "booked",
        "start": D,
        "end": D2,
        "participant": [
            {
                "status": "accepted",
                "actor": "Practitioner/30001",
                "actor_display": "Dr. Smith",
            }
        ],
    }


def appointment_with_fallbacks() -> dict:
    return {
        "status": "booked",
        "start": D,
        "end": D2,
        "description": "Consultation with external provider",
        "identifier": [
            {
                "system": "http://hospital.example.org/appointments",
                "value": "APP-EXT-001",
                "assigner_display": "Regional Health Authority",
                "assigner_identifier_system": "http://gov.example.org/agencies",
                "assigner_identifier_value": "RHA-101",
                "assigner_identifier_use": "official",
            }
        ],
        "participant": [
            {
                "status": "accepted",
                "required": "required",
                "actor_display": "Dr. External Attender",
                "actor_identifier_system": "http://npi.example.org",
                "actor_identifier_value": "NPI-555666",
                "actor_identifier_use": "official",
            }
        ],
        "reason_reference": [
            {
                "reference_display": "External Diagnosis",
                "reference_identifier_system": "http://diagnoses.example.org",
                "reference_identifier_value": "DIAG-1234",
            }
        ],
        "supporting_information": [
            {
                "reference_display": "External Chart Summary",
                "reference_identifier_system": "http://records.example.org",
                "reference_identifier_value": "REC-987",
            }
        ],
        "based_on": [
            {
                "reference_display": "External Service Request",
                "reference_identifier_system": "http://referrals.example.org",
                "reference_identifier_value": "SR-4455",
            }
        ],
    }
