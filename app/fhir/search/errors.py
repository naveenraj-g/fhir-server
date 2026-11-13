from app.errors.fhir_codes import IssueType
from app.errors.validation import InputValidationError


class SearchError(InputValidationError):
    """A search request the server must refuse — HTTP 400 with an
    OperationOutcome (R4 §2.21.1.1: "Servers SHALL reject any search request
    that contains a search parameter with an unsupported modifier", and an
    unparseable value is likewise an error). `field` is the query parameter
    (or value) at fault."""

    def __init__(self, field: str, message: str, issue_type: IssueType = IssueType.INVALID):
        super().__init__([{"field": field, "message": message, "issue_type": issue_type}])


class UnsupportedSearchError(SearchError):
    def __init__(self, field: str, message: str):
        super().__init__(field, message, IssueType.NOT_SUPPORTED)
