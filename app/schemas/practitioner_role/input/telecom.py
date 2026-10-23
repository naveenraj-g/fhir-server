from app.schemas.datatypes import ContactPointInput


class PractitionerRoleTelecomInput(ContactPointInput):
    """PractitionerRole.telecom — contact details specific to the role
    (ContactPoint). Unlike the base ContactPointInput (FHIR's own 0..1
    cardinality for system/value), both remain optional here — the model
    column is nullable, matching FHIR's actual ContactPoint cardinality."""
