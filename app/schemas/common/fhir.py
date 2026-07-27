from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FHIRCoding(BaseModel):
    """FHIR R4 Coding — a reference to a code defined by a terminology system."""

    system: Optional[str] = Field(None, description="Identity of the terminology system that defines this code.")
    version: Optional[str] = Field(
        None, description="Version of the terminology system in which this code was defined."
    )
    code: Optional[str] = Field(None, description="Symbol in the syntax defined by the terminology system.")
    display: Optional[str] = Field(
        None, description="Representation defined by the terminology system for this code."
    )
    userSelected: Optional[bool] = Field(
        None, description="Whether this coding was chosen directly by the user (vs. derived by the system)."
    )


class FHIRCodeableConcept(BaseModel):
    """FHIR R4 CodeableConcept — a concept expressed as one or more coded terms
    plus a plain-text representation."""

    coding: Optional[List[FHIRCoding]] = Field(
        None, description="Code(s) defined by a terminology system for this concept."
    )
    text: Optional[str] = Field(
        None, description="Plain-text representation of the concept, for display when coding is not understood."
    )


class FHIRReference(BaseModel):
    """FHIR R4 Reference — a reference from one resource to another."""

    reference: Optional[str] = Field(
        None, description="A literal reference to another resource, e.g. 'Organization/100'."
    )
    display: Optional[str] = Field(
        None, description="Plain-text display alternative for the referenced resource."
    )


class FHIRPeriod(BaseModel):
    """FHIR R4 Period — a time range defined by start and end dates/times."""

    start: Optional[str] = Field(None, description="Starting ISO 8601 datetime, inclusive, of the period.")
    end: Optional[str] = Field(None, description="Ending ISO 8601 datetime, inclusive, of the period.")


class FHIRHumanName(BaseModel):
    """FHIR R4 HumanName — a name associated with an individual."""

    use: Optional[str] = Field(
        None,
        description="Identifies the purpose of this name. usual|official|temp|nickname|anonymous|old|maiden.",
    )
    text: Optional[str] = Field(
        None, description="Text representation of the full name, as it would normally be displayed."
    )
    family: Optional[str] = Field(None, description="Family name (often called 'surname').")
    given: Optional[List[str]] = Field(
        None, description="Given names (not always 'first'). Includes middle names — order matters."
    )
    prefix: Optional[List[str]] = Field(
        None, description="Parts that come before the name (e.g. Mr., Dr., titles)."
    )
    suffix: Optional[List[str]] = Field(
        None, description="Parts that come after the name (e.g. Jr., MD, qualifications)."
    )
    period: Optional[FHIRPeriod] = Field(
        None, description="The period during which this name was/is in use."
    )


class FHIRIdentifier(BaseModel):
    """FHIR R4 Identifier — a business identifier for a resource, unique within
    some defined namespace."""

    use: Optional[str] = Field(
        None, description="The purpose of this identifier. usual|official|temp|secondary|old."
    )
    type: Optional[FHIRCodeableConcept] = Field(
        None, description="A coded description of the type of identifier (e.g. MR, SSN, passport)."
    )
    system: Optional[str] = Field(
        None, description="The namespace (a URI) that identifies the scope this identifier's value is unique within."
    )
    value: Optional[str] = Field(None, description="The identifier value itself, unique within the given system.")
    period: Optional[FHIRPeriod] = Field(
        None, description="The period during which this identifier is/was valid for use."
    )
    assigner: Optional[Dict[str, str]] = Field(
        None, description="Reference(Organization) — the organization that issued this identifier."
    )


class FHIRContactPoint(BaseModel):
    """FHIR R4 ContactPoint — a contact detail (phone, email, etc.) for a person or organization."""

    system: Optional[str] = Field(
        None, description="Telecommunications form for this contact point. phone|fax|email|pager|url|sms|other."
    )
    value: Optional[str] = Field(
        None, description="The actual contact point details (e.g. a phone number or email address)."
    )
    use: Optional[str] = Field(None, description="Purpose of this contact point. home|work|temp|old|mobile.")
    rank: Optional[int] = Field(
        None, description="Preferred order of use among an individual's contact points — 1 indicates the most preferred."
    )
    period: Optional[FHIRPeriod] = Field(
        None, description="The period during which this contact point was/is in use."
    )


class FHIRAddress(BaseModel):
    """FHIR R4 Address — a postal or physical address."""

    use: Optional[str] = Field(None, description="The purpose of this address. home|work|temp|old|billing.")
    type: Optional[str] = Field(
        None, description="Distinguishes physical locations from mailing addresses. postal|physical|both."
    )
    text: Optional[str] = Field(
        None, description="Text representation of the address, as it would normally be displayed on a mailing label."
    )
    line: Optional[List[str]] = Field(
        None, description="Street name, number, direction, P.O. Box, or similar — one entry per address line, in order."
    )
    city: Optional[str] = Field(None, description="Name of the city, town, suburb, village, or other community.")
    district: Optional[str] = Field(None, description="County or administrative district.")
    state: Optional[str] = Field(None, description="Sub-unit of country — state, province, etc.")
    postalCode: Optional[str] = Field(None, description="Postal/ZIP code for the area.")
    country: Optional[str] = Field(None, description="Country — e.g. an ISO 3166 2- or 3-letter code.")
    period: Optional[FHIRPeriod] = Field(
        None, description="The period during which this address was/is in use."
    )


class FHIRBundleEntry(BaseModel):
    """FHIR R4 Bundle.entry — a single resource entry within a Bundle."""

    resource: Any = Field(..., description="The resource contained in this bundle entry.")


class FHIRBundle(BaseModel):
    """FHIR R4 Bundle — a container for a collection of resources, here always a 'searchset'."""

    resourceType: str = Field("Bundle", description="Always 'Bundle'.")
    type: str = Field("searchset", description="The purpose of this bundle. Always 'searchset' in this API.")
    total: int = Field(..., description="Total number of resources matching the search, across all pages.")
    entry: Optional[List[FHIRBundleEntry]] = Field(
        None, description="Resources matching the search, one per entry, for the current page."
    )


# ── Shared plain (snake_case) sub-types ──────────────────────────────────────


class PlainCoding(BaseModel):
    """Plain-JSON Coding — a reference to a code defined by a terminology system."""

    system: Optional[str] = Field(None, description="Identity of the terminology system that defines this code.")
    version: Optional[str] = Field(
        None, description="Version of the terminology system in which this code was defined."
    )
    code: Optional[str] = Field(None, description="Symbol in the syntax defined by the terminology system.")
    display: Optional[str] = Field(
        None, description="Representation defined by the terminology system for this code."
    )
    user_selected: Optional[bool] = Field(
        None, description="Whether this coding was chosen directly by the user (vs. derived by the system)."
    )


class PlainIdentifierType(BaseModel):
    """Plain-JSON rendering of Identifier.type — a coded description of the identifier's type."""

    text: Optional[str] = Field(None, description="Plain-text rendering of the identifier-type concept.")
    coding: Optional[List[PlainCoding]] = Field(None, description="Coded value(s) for the identifier type.")


class PlainIdentifier(BaseModel):
    """Plain-JSON Identifier — a business identifier, unique within some defined namespace."""

    use: Optional[str] = Field(
        None, description="The purpose of this identifier. usual|official|temp|secondary|old."
    )
    system: Optional[str] = Field(
        None, description="The namespace (a URI) that identifies the scope this identifier's value is unique within."
    )
    value: Optional[str] = Field(None, description="The identifier value itself, unique within the given system.")
    period_start: Optional[str] = Field(None, description="ISO 8601 datetime string.")
    period_end: Optional[str] = Field(None, description="ISO 8601 datetime string.")
    assigner: Optional[str] = Field(None, description="Display name of the organization that issued this identifier.")
    type: Optional[PlainIdentifierType] = Field(None, description="A coded description of the type of identifier.")


class PlainReasonCode(BaseModel):
    """Plain-JSON CodeableConcept used for reason-code style fields."""

    coding_system: Optional[str] = Field(None, description="Coding system that defines this reason code.")
    coding_code: Optional[str] = Field(None, description="Code for the reason.")
    coding_display: Optional[str] = Field(None, description="Human-readable display for the reason code.")
    text: Optional[str] = Field(None, description="Plain-text rendering of the reason CodeableConcept.")
