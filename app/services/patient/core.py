from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.patient import (
    merge_patch_fragment,
    patch_fragment_to_fhir_patient,
    payload_to_fhir_patient,
    to_fhir_patient,
    to_plain_patient,
)
from app.fhir.validation import validate_resource
from app.models.patient import PatientModel
from app.repository.patient import PatientRepository
from app.schemas.patient import PatientCreateSchema, PatientPatchSchema

logger = get_logger(__name__)


class _CoreMixin:
    """All Patient business logic. Auth matches other modern resources:
    tenant scoping comes from the verified JWT's activeOrganizationId claim (actor.org_id),
    never a client-suppliable field, and there's no org-less/super-admin bypass —
    every operation requires an org-scoped actor. Like Practitioner, Patient also
    keeps `user_id`, so `get_me()` additionally scopes to the acting end-user."""

    def __init__(self, repository: PatientRepository):
        self.repository = repository

    # ── Formatters ────────────────────────────────────────────────────────

    def _to_fhir(self, p: PatientModel) -> dict:
        return to_fhir_patient(p)

    def _to_plain(self, p: PatientModel) -> dict:
        return to_plain_patient(p)

    # ── Read ──────────────────────────────────────────────────────────────

    async def get_patient_scoped(
        self, patient_id: int, org_id: str | None
    ) -> PatientModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "Patient operation requires an org-scoped token"
            )
        p = await self.repository.get_by_patient_id_in_org(patient_id, org_id)
        if not p:
            raise NotFoundError("Patient not found")
        return p

    async def list_patients(
        self,
        org_id: str | None = None,
        active: bool | None = None,
        gender=None,
        birthdate=None,
        birthdate_from=None,
        birthdate_to=None,
        deceased: bool | None = None,
        family: str | None = None,
        given: str | None = None,
        name: str | None = None,
        phonetic: str | None = None,
        identifier: str | None = None,
        telecom: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        address: str | None = None,
        address_city: str | None = None,
        address_state: str | None = None,
        address_postal_code: str | None = None,
        address_country: str | None = None,
        address_use=None,
        general_practitioner: str | None = None,
        organization: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[PatientModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token — same
        invariant as get_patient_scoped()."""
        if not org_id:
            raise PermissionDeniedError(
                "Patient operation requires an org-scoped token"
            )
        return await self.repository.list(
            org_id=org_id,
            active=active,
            gender=gender,
            birthdate=birthdate,
            birthdate_from=birthdate_from,
            birthdate_to=birthdate_to,
            deceased=deceased,
            family=family,
            given=given,
            name=name,
            phonetic=phonetic,
            identifier=identifier,
            telecom=telecom,
            phone=phone,
            email=email,
            address=address,
            address_city=address_city,
            address_state=address_state,
            address_postal_code=address_postal_code,
            address_country=address_country,
            address_use=address_use,
            general_practitioner=general_practitioner,
            organization=organization,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def get_me(
        self,
        user_id: str,
        org_id: str,
        **filters,
    ) -> tuple[list[PatientModel], int | None]:
        """Scopes list() to the authenticated end-user's own user_id, always
        combined with the org-scoped actor's org_id."""
        if not org_id:
            raise PermissionDeniedError(
                "Patient operation requires an org-scoped token"
            )
        return await self.repository.get_me(user_id=user_id, org_id=org_id, **filters)

    # ── Write ─────────────────────────────────────────────────────────────

    async def create_patient(
        self,
        payload: PatientCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> PatientModel:
        """org_id comes from the verified JWT's actor.org_id, not a client-
        supplied field — there is no bypass, so an org-less/platform token
        cannot create a Patient at all."""
        if not org_id:
            raise PermissionDeniedError(
                "Patient creation requires an org-scoped token"
            )
        await self._validate_base_r4(payload_to_fhir_patient(payload), org_id)
        p = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "Patient created",
            extra={"event": "patient.created", "patient_id": p.patient_id},
        )
        return p

    async def patch_patient(
        self,
        patient_id: int,
        payload: PatientPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> PatientModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass: a
        missing org_id or a patient belonging to a different org both
        raise NotFoundError (404), never 403, so existence isn't leaked.

        The current row is fetched because base R4 validation needs it: a PATCH
        payload is partial by nature, so it's merged onto the resource's current
        full FHIR representation before validating."""
        if not org_id:
            self._log_org_scope_miss("patch", patient_id, org_id)
            raise NotFoundError("Patient not found")
        existing = await self.repository.get_by_patient_id_in_org(
            patient_id, org_id
        )
        if not existing:
            self._log_org_scope_miss("patch", patient_id, org_id)
            raise NotFoundError("Patient not found")

        fragment, touched = patch_fragment_to_fhir_patient(payload)
        merged = merge_patch_fragment(to_fhir_patient(existing), fragment, touched)
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(patient_id, payload, updated_by)
        if not updated:
            raise NotFoundError("Patient not found")
        logger.info(
            "Patient updated",
            extra={
                "event": "patient.updated",
                "patient_id": patient_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_patient(
        self, patient_id: int, org_id: str | None = None
    ) -> None:
        """Same org_id ownership gate as patch_patient."""
        if not org_id or not await self.repository.patient_belongs_to_org(
            patient_id, org_id
        ):
            self._log_org_scope_miss("delete", patient_id, org_id)
            raise NotFoundError("Patient not found")
        deleted = await self.repository.delete(patient_id)
        if not deleted:
            raise NotFoundError("Patient not found")
        logger.info(
            "Patient deleted",
            extra={"event": "patient.deleted", "patient_id": patient_id},
        )

    # ── Validation helpers ────────────────────────────────────────────────

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        """Raises FhirValidationError (422) if `fhir_resource` fails validation."""
        errors = await validate_resource("Patient", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "Patient failed base R4 validation",
                extra={"event": "patient.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

    # ── Logging helpers ───────────────────────────────────────────────────

    @staticmethod
    def _log_org_scope_miss(
        operation: str, patient_id: int, org_id: str | None
    ) -> None:
        """The tenant gate rejected a write."""
        logger.warning(
            "Patient write rejected by org scope",
            extra={
                "event": "patient.org_scope_miss",
                "operation": operation,
                "patient_id": patient_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )
