"""FHIR R4 OperationOutcome.issue code enums — IssueSeverity and IssueType —
pulled verbatim from HL7's own CodeSystems
(http://hl7.org/fhir/issue-severity, http://hl7.org/fhir/issue-type), not
hand-typed from memory. See docs/structure-definitions/ for how this
project verifies FHIR spec facts against real data rather than
recollection; this module is the equivalent discipline applied to error
handling.

IssueType is a HIERARCHICAL CodeSystem in the real spec (e.g. "invariant"
is a child of "invalid", "forbidden" a child of "security", "conflict" and
"business-rule" are children of "processing") — flattened here into one
enum of valid code strings, since FHIR permits using either a parent or a
child code and nothing in this codebase needs to reason about the
hierarchy itself, only emit/validate a legal code string. Each member's
inline comment is HL7's own definition text, not a paraphrase.
"""

from enum import Enum


class IssueSeverity(str, Enum):
    FATAL = "fatal"
    ERROR = "error"
    WARNING = "warning"
    INFORMATION = "information"


class IssueType(str, Enum):
    # --- invalid ---
    INVALID = "invalid"  # Content invalid against the specification or a profile.
    STRUCTURE = "structure"  # A structural issue in the content such as wrong namespace, unable to parse the content completely, or invalid json/xml syntax.
    REQUIRED = "required"  # A required element is missing.
    VALUE = "value"  # An element or header value is invalid.
    INVARIANT = "invariant"  # A content validation rule failed - e.g. a schematron rule.

    # --- security ---
    SECURITY = "security"  # An authentication/authorization/permissions issue of some kind.
    LOGIN = "login"  # The client needs to initiate an authentication process.
    UNKNOWN = "unknown"  # The user or system was not able to be authenticated (either there is no process, or the proferred token is unacceptable).
    EXPIRED = "expired"  # User session expired; a login may be required.
    FORBIDDEN = "forbidden"  # The user does not have the rights to perform this action.
    SUPPRESSED = "suppressed"  # Some information was not or might not have been returned due to business rules, consent or privacy rules.

    # --- processing ---
    PROCESSING = "processing"  # Processing issues. These are expected to be final, i.e. there is no point resubmitting the same content unchanged.
    NOT_SUPPORTED = "not-supported"  # The interaction, operation, resource or profile is not supported.
    DUPLICATE = "duplicate"  # An attempt was made to create a duplicate record.
    MULTIPLE_MATCHES = "multiple-matches"  # Multiple matching records were found when the operation required only one match.
    NOT_FOUND = "not-found"  # The reference provided was not found. In a pure RESTful environment, this would be an HTTP 404 error, but this code may be used where the content is not found further into the application architecture.
    DELETED = "deleted"  # The reference pointed to content (usually a resource) that has been deleted.
    TOO_LONG = "too-long"  # Provided content is too long (typically, this is a denial of service protection type of error).
    CODE_INVALID = "code-invalid"  # The code or system could not be understood, or it was not valid in the context of a particular ValueSet.code.
    EXTENSION = "extension"  # An extension was found that was not acceptable, could not be resolved, or a modifierExtension was not recognized.
    TOO_COSTLY = "too-costly"  # The operation was stopped to protect server resources; e.g. a request for a value set expansion on all of SNOMED CT.
    BUSINESS_RULE = "business-rule"  # The content/operation failed to pass some business rule, and so could not proceed.
    CONFLICT = "conflict"  # Content could not be accepted because of an edit conflict (i.e. version aware updates) (i.e. if-match requirements fail).

    # --- transient ---
    TRANSIENT = "transient"  # Transient processing issues. The system receiving the message may be able to resubmit the same content once an underlying issue is resolved.
    LOCK_ERROR = "lock-error"  # A resource/record locking failure (usually in an underlying database).
    NO_STORE = "no-store"  # The persistent store is unavailable; e.g. the database is down for maintenance or similar action.
    EXCEPTION = "exception"  # An unexpected internal error has occurred.
    TIMEOUT = "timeout"  # An internal timeout has occurred.
    INCOMPLETE = "incomplete"  # Not all data sources typically accessed could be reached, or responded in time, so the returned information might not be complete.
    THROTTLED = "throttled"  # The system is not prepared to handle this request due to load management.

    # --- informational ---
    INFORMATIONAL = "informational"  # A message unrelated to the processing success of the completed operation.
