from app.core.schema_utils import inline_schema
from app.schemas.practitioner.response import (
    FHIRPractitionerAddressesListResponse,
    FHIRPractitionerBundle,
    FHIRPractitionerCommunicationsListResponse,
    FHIRPractitionerIdentifiersListResponse,
    FHIRPractitionerNamesListResponse,
    FHIRPractitionerPhotosListResponse,
    FHIRPractitionerQualificationsListResponse,
    FHIRPractitionerSchema,
    FHIRPractitionerTelecomListResponse,
    PaginatedPractitionerResponse,
    PlainPractitionerResponse,
    PractitionerAddressesListResponse,
    PractitionerCommunicationsListResponse,
    PractitionerIdentifiersListResponse,
    PractitionerNamesListResponse,
    PractitionerPhotosListResponse,
    PractitionerQualificationsListResponse,
    PractitionerTelecomListResponse,
)

_CONTENT_NEG = (
    "Set `Accept: application/fhir+json` to receive the full FHIR R4 representation; "
    "omit or use `Accept: application/json` for the simplified plain-JSON form."
)

_ERR_NOT_FOUND = {404: {"description": "Practitioner not found"}}
_ERR_VALIDATION = {
    422: {"description": "Validation error — request body failed schema validation"}
}

_SINGLE_200 = {
    200: {
        "content": {
            "application/json": {
                "schema": inline_schema(PlainPractitionerResponse.model_json_schema())
            },
            "application/fhir+json": {
                "schema": inline_schema(FHIRPractitionerSchema.model_json_schema())
            },
        }
    }
}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200 = {
    200: {
        "description": "Paginated list of practitioners",
        "content": {
            "application/json": {
                "schema": inline_schema(
                    PaginatedPractitionerResponse.model_json_schema()
                )
            },
            "application/fhir+json": {
                "schema": inline_schema(FHIRPractitionerBundle.model_json_schema())
            },
        },
    }
}

_SUBRES_NAMES_200 = {
    200: {
        "description": "List of HumanName entries",
        "content": {
            "application/json": {
                "schema": inline_schema(
                    PractitionerNamesListResponse.model_json_schema()
                )
            },
            "application/fhir+json": {
                "schema": inline_schema(
                    FHIRPractitionerNamesListResponse.model_json_schema()
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
                    PractitionerIdentifiersListResponse.model_json_schema()
                )
            },
            "application/fhir+json": {
                "schema": inline_schema(
                    FHIRPractitionerIdentifiersListResponse.model_json_schema()
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
                "schema": inline_schema(
                    PractitionerTelecomListResponse.model_json_schema()
                )
            },
            "application/fhir+json": {
                "schema": inline_schema(
                    FHIRPractitionerTelecomListResponse.model_json_schema()
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
                    PractitionerAddressesListResponse.model_json_schema()
                )
            },
            "application/fhir+json": {
                "schema": inline_schema(
                    FHIRPractitionerAddressesListResponse.model_json_schema()
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
                "schema": inline_schema(
                    PractitionerPhotosListResponse.model_json_schema()
                )
            },
            "application/fhir+json": {
                "schema": inline_schema(
                    FHIRPractitionerPhotosListResponse.model_json_schema()
                )
            },
        },
    }
}
_SUBRES_QUALIFICATIONS_200 = {
    200: {
        "description": "List of qualifications",
        "content": {
            "application/json": {
                "schema": inline_schema(
                    PractitionerQualificationsListResponse.model_json_schema()
                )
            },
            "application/fhir+json": {
                "schema": inline_schema(
                    FHIRPractitionerQualificationsListResponse.model_json_schema()
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
                    PractitionerCommunicationsListResponse.model_json_schema()
                )
            },
            "application/fhir+json": {
                "schema": inline_schema(
                    FHIRPractitionerCommunicationsListResponse.model_json_schema()
                )
            },
        },
    }
}
