from typing import Annotated

from pydantic import StringConstraints

from app.core.schema_utils import inline_schema
from app.schemas.patient.response import (
    FHIRPatientAddressesListResponse,
    FHIRPatientBundle,
    FHIRPatientCommunicationsListResponse,
    FHIRPatientContactsListResponse,
    FHIRPatientCoreSchema,
    FHIRPatientGeneralPractitionersListResponse,
    FHIRPatientIdentifiersListResponse,
    FHIRPatientLinksListResponse,
    FHIRPatientNamesListResponse,
    FHIRPatientPhotosListResponse,
    FHIRPatientSchema,
    FHIRPatientTelecomListResponse,
    PaginatedPatientResponse,
    PatientAddressesListResponse,
    PatientCommunicationsListResponse,
    PatientContactsListResponse,
    PatientGeneralPractitionersListResponse,
    PatientIdentifiersListResponse,
    PatientLinksListResponse,
    PatientNamesListResponse,
    PatientPhotosListResponse,
    PatientTelecomListResponse,
    PlainPatientCoreResponse,
    PlainPatientResponse,
)

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

# FHIR comparator-prefixed date, e.g. "ge2024-01-01" or "2024-01-01T12:00:00Z" —
# see app.core.filters.apply_fhir_date_filter, which does the actual parsing;
# this pattern just rejects an obviously malformed value at parameter-binding
# time instead of letting it reach that helper's manual HTTPException.
# birthdate/death-date are repeatable (list[str]) query params — Query()'s own
# `pattern=` kwarg only constrains scalar params, not list items, so each item
# needs its own StringConstraints via Annotated instead.
_FHIR_DATE_PATTERN = (
    r"^(eq|ne|gt|lt|ge|le)?\d{4}-\d{2}-\d{2}"
    r"(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$"
)
_FhirDateItem = Annotated[str, StringConstraints(pattern=_FHIR_DATE_PATTERN)]

# FHIR reference string, e.g. "Organization/190001" — see
# app.core.filters.parse_reference, which validates the resource-type half
# against the caller-supplied enum; this pattern only rejects the gross shape.
_FHIR_REFERENCE_PATTERN = r"^[A-Za-z]+/\d+$"

_ERR_NOT_FOUND = {404: {"description": "Patient not found"}}
_ERR_VALIDATION = {
    422: {"description": "Validation error — request body failed schema validation"}
}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(PlainPatientResponse.model_json_schema())
            },
            "application/fhir+json": {
                "schema": inline_schema(FHIRPatientSchema.model_json_schema())
            },
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_SINGLE_CORE_200 = {
    200: {
        "description": "Patient core fields retrieved successfully — no sub-resource arrays",
        "content": {
            "application/json": {
                "schema": inline_schema(PlainPatientCoreResponse.model_json_schema())
            },
            "application/fhir+json": {
                "schema": inline_schema(FHIRPatientCoreSchema.model_json_schema())
            },
        },
    }
}
_LIST_200 = {
    200: {
        "description": "Paginated list of patients",
        "content": {
            "application/json": {
                "schema": inline_schema(PaginatedPatientResponse.model_json_schema())
            },
            "application/fhir+json": {
                "schema": inline_schema(FHIRPatientBundle.model_json_schema())
            },
        },
    }
}

_SUBRES_NAMES_200 = {
    200: {
        "description": "List of HumanName entries",
        "content": {
            "application/json": {
                "schema": inline_schema(PatientNamesListResponse.model_json_schema())
            },
            "application/fhir+json": {
                "schema": inline_schema(
                    FHIRPatientNamesListResponse.model_json_schema()
                )
            },
        },
    }
}
_SUBRES_IDENTIFIERS_200 = {
    200: {
        "description": "List of business identifiers",
        "content": {
            "application/json": {
                "schema": inline_schema(
                    PatientIdentifiersListResponse.model_json_schema()
                )
            },
            "application/fhir+json": {
                "schema": inline_schema(
                    FHIRPatientIdentifiersListResponse.model_json_schema()
                )
            },
        },
    }
}
_SUBRES_TELECOM_200 = {
    200: {
        "description": "List of contact points",
        "content": {
            "application/json": {
                "schema": inline_schema(PatientTelecomListResponse.model_json_schema())
            },
            "application/fhir+json": {
                "schema": inline_schema(
                    FHIRPatientTelecomListResponse.model_json_schema()
                )
            },
        },
    }
}
_SUBRES_ADDRESSES_200 = {
    200: {
        "description": "List of addresses",
        "content": {
            "application/json": {
                "schema": inline_schema(
                    PatientAddressesListResponse.model_json_schema()
                )
            },
            "application/fhir+json": {
                "schema": inline_schema(
                    FHIRPatientAddressesListResponse.model_json_schema()
                )
            },
        },
    }
}
_SUBRES_PHOTOS_200 = {
    200: {
        "description": "List of photo attachments",
        "content": {
            "application/json": {
                "schema": inline_schema(PatientPhotosListResponse.model_json_schema())
            },
            "application/fhir+json": {
                "schema": inline_schema(
                    FHIRPatientPhotosListResponse.model_json_schema()
                )
            },
        },
    }
}
_SUBRES_CONTACTS_200 = {
    200: {
        "description": "List of contacts (next-of-kin / guardian)",
        "content": {
            "application/json": {
                "schema": inline_schema(PatientContactsListResponse.model_json_schema())
            },
            "application/fhir+json": {
                "schema": inline_schema(
                    FHIRPatientContactsListResponse.model_json_schema()
                )
            },
        },
    }
}
_SUBRES_COMMUNICATIONS_200 = {
    200: {
        "description": "List of communication language entries",
        "content": {
            "application/json": {
                "schema": inline_schema(
                    PatientCommunicationsListResponse.model_json_schema()
                )
            },
            "application/fhir+json": {
                "schema": inline_schema(
                    FHIRPatientCommunicationsListResponse.model_json_schema()
                )
            },
        },
    }
}
_SUBRES_GPS_200 = {
    200: {
        "description": "List of general practitioner references",
        "content": {
            "application/json": {
                "schema": inline_schema(
                    PatientGeneralPractitionersListResponse.model_json_schema()
                )
            },
            "application/fhir+json": {
                "schema": inline_schema(
                    FHIRPatientGeneralPractitionersListResponse.model_json_schema()
                )
            },
        },
    }
}
_SUBRES_LINKS_200 = {
    200: {
        "description": "List of patient link entries",
        "content": {
            "application/json": {
                "schema": inline_schema(PatientLinksListResponse.model_json_schema())
            },
            "application/fhir+json": {
                "schema": inline_schema(
                    FHIRPatientLinksListResponse.model_json_schema()
                )
            },
        },
    }
}
