from enum import Enum


class PatientLinkType(str, Enum):
    """FHIR R4 Patient.link.type value set —
    https://www.hl7.org/fhir/R4/valueset-link-type.html

    Member name intentionally equals member value (both underscore-only,
    not the true hyphenated FHIR code) — see CLAUDE.md's FHIR DB Model
    Design "Alembic autogenerate enum values are correct (key = value
    convention)" invariant: SQLAlchemy's Enum(PyEnum) stores each member's
    .name in Postgres by default, so key = value ensures consistency.
    The real 'replaced-by' FHIR code is rendered explicitly in
    app/fhir/mappers/patient/fhir.py.
    """

    replaced_by = "replaced_by"
    replaces = "replaces"
    refer = "refer"
    seealso = "seealso"


class PatientLinkOtherType(str, Enum):
    """Allowed resource reference types for Patient.link.other (Patient | RelatedPerson)."""

    Patient = "Patient"
    RelatedPerson = "RelatedPerson"


class PatientGeneralPractitionerReferenceType(str, Enum):
    """Allowed resource reference types for Patient.generalPractitioner
    (Organization | Practitioner | PractitionerRole)."""

    Organization = "Organization"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
