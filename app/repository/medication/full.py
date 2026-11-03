from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import delete
from sqlalchemy.future import select

from app.models.enums import IdentifierUse as IdentifierUseModel
from app.models.medication import (
    MedicationCodeCoding,
    MedicationFormCoding,
    MedicationIdentifier,
    MedicationIdentifierAssignerReferenceType,
    MedicationIdentifierTypeCoding,
    MedicationIngredient,
    MedicationIngredientItemCoding,
    MedicationIngredientItemReferenceType,
    MedicationManufacturerReferenceType,
    MedicationModel,
    MedicationQuantityComparator as MedicationQuantityComparatorModel,
    MedicationStatus as MedicationStatusModel,
)

from ._shared import (
    _single_reference_kwargs,
    _validate_ref,
    _with_relationships,
)

if TYPE_CHECKING:
    from app.schemas.medication import (
        MedicationCreateSchema,
        MedicationPatchSchema,
    )
    from app.schemas.medication.input.identifier import (
        MedicationIdentifierInput,
    )
    from app.schemas.medication.input.ingredient import (
        MedicationIngredientInput,
    )

_MANUFACTURER_FIELDS = {
    "manufacturer",
    "manufacturer_display",
    "manufacturer_identifier_use",
    "manufacturer_identifier_type_system",
    "manufacturer_identifier_type_version",
    "manufacturer_identifier_type_code",
    "manufacturer_identifier_type_display",
    "manufacturer_identifier_type_user_selected",
    "manufacturer_identifier_type_text",
    "manufacturer_identifier_system",
    "manufacturer_identifier_value",
    "manufacturer_identifier_period_start",
    "manufacturer_identifier_period_end",
}


def _coding_kwargs(coding, org_id: str, created_by: str) -> dict:
    return {
        "tenant_id": org_id,
        "created_by": created_by,
        "system": coding.system,
        "version": coding.version,
        "code": coding.code,
        "display": coding.display,
        "user_selected": coding.user_selected,
    }


def _ratio_kwargs(ratio, prefix: str) -> dict:
    if not ratio:
        return {
            f"{prefix}_numerator_value": None,
            f"{prefix}_numerator_comparator": None,
            f"{prefix}_numerator_unit": None,
            f"{prefix}_numerator_system": None,
            f"{prefix}_numerator_code": None,
            f"{prefix}_denominator_value": None,
            f"{prefix}_denominator_comparator": None,
            f"{prefix}_denominator_unit": None,
            f"{prefix}_denominator_system": None,
            f"{prefix}_denominator_code": None,
        }
    num = ratio.numerator
    den = ratio.denominator
    return {
        f"{prefix}_numerator_value": num.value if num else None,
        f"{prefix}_numerator_comparator": (
            MedicationQuantityComparatorModel[num.comparator.name]
            if num and num.comparator
            else None
        ),
        f"{prefix}_numerator_unit": num.unit if num else None,
        f"{prefix}_numerator_system": num.system if num else None,
        f"{prefix}_numerator_code": num.code if num else None,
        f"{prefix}_denominator_value": den.value if den else None,
        f"{prefix}_denominator_comparator": (
            MedicationQuantityComparatorModel[den.comparator.name]
            if den and den.comparator
            else None
        ),
        f"{prefix}_denominator_unit": den.unit if den else None,
        f"{prefix}_denominator_system": den.system if den else None,
        f"{prefix}_denominator_code": den.code if den else None,
    }


async def _add_identifiers(
    session,
    med_pk: int,
    org_id: str,
    identifiers: list[MedicationIdentifierInput] | None,
    created_by: str,
) -> None:
    if not identifiers:
        return
    for item in identifiers:
        assigner_kwargs = _single_reference_kwargs(
            "assigner", item, MedicationIdentifierAssignerReferenceType
        )
        await _validate_ref(
            session,
            org_id,
            "identifier.assigner",
            assigner_kwargs.get("assigner_type"),
            assigner_kwargs.get("assigner_id"),
        )
        ident = MedicationIdentifier(
            medication_pk=med_pk,
            tenant_id=org_id,
            created_by=created_by,
            use=IdentifierUseModel[item.use.name] if item.use else None,
            type_text=item.type.text if item.type else None,
            system=item.system,
            value=item.value,
            period_start=item.period_start,
            period_end=item.period_end,
            **assigner_kwargs,
        )
        session.add(ident)
        if item.type and item.type.coding:
            await session.flush()
            for c in item.type.coding:
                session.add(
                    MedicationIdentifierTypeCoding(
                        medication_identifier_id=ident.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_code_codings(
    session,
    med_pk: int,
    org_id: str,
    codings: list | None,
    created_by: str,
) -> None:
    for c in codings or []:
        session.add(
            MedicationCodeCoding(
                medication_pk=med_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


async def _add_form_codings(
    session,
    med_pk: int,
    org_id: str,
    codings: list | None,
    created_by: str,
) -> None:
    for c in codings or []:
        session.add(
            MedicationFormCoding(
                medication_pk=med_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


async def _add_ingredients(
    session,
    med_pk: int,
    org_id: str,
    ingredients: list[MedicationIngredientInput] | None,
    created_by: str,
) -> None:
    if not ingredients:
        return
    for ing in ingredients:
        item_ref_kwargs = _single_reference_kwargs(
            "item", ing, MedicationIngredientItemReferenceType
        )
        await _validate_ref(
            session,
            org_id,
            "ingredient.item",
            item_ref_kwargs.get("item_type"),
            item_ref_kwargs.get("item_id"),
        )
        strength_kwargs = _ratio_kwargs(ing.strength, "strength")
        ing_row = MedicationIngredient(
            medication_pk=med_pk,
            tenant_id=org_id,
            created_by=created_by,
            item_codeable_concept_text=(
                ing.item_codeable_concept.text if ing.item_codeable_concept else None
            ),
            is_active=ing.is_active,
            **item_ref_kwargs,
            **strength_kwargs,
        )
        session.add(ing_row)
        if ing.item_codeable_concept and ing.item_codeable_concept.coding:
            await session.flush()
            for c in ing.item_codeable_concept.coding:
                session.add(
                    MedicationIngredientItemCoding(
                        medication_ingredient_id=ing_row.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


class _FullMixin:
    """Atomic full-graph creation and patch for Medication."""

    async def create_full(
        self,
        payload: MedicationCreateSchema,
        org_id: str,
        created_by: str,
    ) -> MedicationModel:
        async with self.session_factory() as session:
            # 1. Resolve & validate references
            mfg_kwargs = _single_reference_kwargs(
                "manufacturer", payload, MedicationManufacturerReferenceType
            )
            await _validate_ref(
                session,
                org_id,
                "manufacturer",
                mfg_kwargs.get("manufacturer_type"),
                mfg_kwargs.get("manufacturer_id"),
            )

            amount_kwargs = _ratio_kwargs(payload.amount, "amount")

            # 2. Main row
            med = MedicationModel(
                tenant_id=org_id,
                created_by=created_by,
                code_text=payload.code.text if payload.code else None,
                status=(
                    MedicationStatusModel[payload.status.name]
                    if payload.status
                    else None
                ),
                **mfg_kwargs,
                form_text=payload.form.text if payload.form else None,
                **amount_kwargs,
                batch_lot_number=payload.batch.lot_number if payload.batch else None,
                batch_expiration_date=(
                    payload.batch.expiration_date if payload.batch else None
                ),
                extension=payload.extension if payload.extension is not None else [],
            )
            session.add(med)
            await session.flush()

            # 3. Add sub-resources
            await _add_identifiers(session, med.id, org_id, payload.identifier, created_by)
            if payload.code and payload.code.coding:
                await _add_code_codings(session, med.id, org_id, payload.code.coding, created_by)
            if payload.form and payload.form.coding:
                await _add_form_codings(session, med.id, org_id, payload.form.coding, created_by)
            await _add_ingredients(session, med.id, org_id, payload.ingredient, created_by)

            pub_id = med.medication_id
            await session.commit()

        # Reload with relationships in a fresh session
        return await self.get_by_medication_id_in_org(pub_id, org_id)

    async def patch_full(
        self,
        medication_id: int,
        payload: MedicationPatchSchema,
        org_id: str,
        updated_by: str,
    ) -> MedicationModel | None:
        async with self.session_factory() as session:
            stmt = select(MedicationModel).where(
                MedicationModel.medication_id == medication_id,
                MedicationModel.tenant_id == org_id,
            )
            res = await session.execute(stmt)
            med = res.scalar_one_or_none()
            if not med:
                return None

            provided = payload.model_fields_set

            if "status" in provided:
                med.status = (
                    MedicationStatusModel[payload.status.name]
                    if payload.status
                    else None
                )

            if "code" in provided:
                med.code_text = payload.code.text if payload.code else None
                await session.execute(
                    delete(MedicationCodeCoding).where(
                        MedicationCodeCoding.medication_pk == med.id
                    )
                )
                if payload.code and payload.code.coding:
                    await _add_code_codings(
                        session, med.id, org_id, payload.code.coding, updated_by
                    )

            if "form" in provided:
                med.form_text = payload.form.text if payload.form else None
                await session.execute(
                    delete(MedicationFormCoding).where(
                        MedicationFormCoding.medication_pk == med.id
                    )
                )
                if payload.form and payload.form.coding:
                    await _add_form_codings(
                        session, med.id, org_id, payload.form.coding, updated_by
                    )

            if provided & _MANUFACTURER_FIELDS:
                mfg_kwargs = _single_reference_kwargs(
                    "manufacturer", payload, MedicationManufacturerReferenceType
                )
                await _validate_ref(
                    session,
                    org_id,
                    "manufacturer",
                    mfg_kwargs.get("manufacturer_type"),
                    mfg_kwargs.get("manufacturer_id"),
                )
                for k, v in mfg_kwargs.items():
                    setattr(med, k, v)

            if "amount" in provided:
                amount_kwargs = _ratio_kwargs(payload.amount, "amount")
                for k, v in amount_kwargs.items():
                    setattr(med, k, v)

            if "batch" in provided:
                med.batch_lot_number = (
                    payload.batch.lot_number if payload.batch else None
                )
                med.batch_expiration_date = (
                    payload.batch.expiration_date if payload.batch else None
                )

            if "extension" in provided:
                med.extension = list(payload.extension) if payload.extension else []

            if "identifier" in provided:
                await session.execute(
                    delete(MedicationIdentifier).where(
                        MedicationIdentifier.medication_pk == med.id
                    )
                )
                await _add_identifiers(
                    session, med.id, org_id, payload.identifier, updated_by
                )

            if "ingredient" in provided:
                await session.execute(
                    delete(MedicationIngredient).where(
                        MedicationIngredient.medication_pk == med.id
                    )
                )
                await _add_ingredients(
                    session, med.id, org_id, payload.ingredient, updated_by
                )

            med.updated_by = updated_by
            pub_id = med.medication_id
            await session.commit()

        # Reload with relationships in a fresh session
        return await self.get_by_medication_id_in_org(pub_id, org_id)
