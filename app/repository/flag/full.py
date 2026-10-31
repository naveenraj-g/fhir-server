from sqlalchemy import delete, func, select

from app.core.logging import get_logger
from app.core.pagination import resolve_sort
from app.models.flag import (
    FlagCategory,
    FlagCategoryCoding,
    FlagCodeCoding,
    FlagIdentifier,
    FlagIdentifierTypeCoding,
    FlagModel,
)
from app.schemas.flag import FlagCreateSchema, FlagPatchSchema

from ._shared import (
    _SORTABLE_FIELDS,
    _parse_assigner_ref,
    _parse_author_ref,
    _parse_encounter_ref,
    _parse_subject_ref,
    _validate_ref,
    _with_relationships,
)

logger = get_logger(__name__)


def _coding_kwargs(coding, org_id: str, created_by: str) -> dict:
    return {
        "tenant_id": org_id,
        "system": coding.system,
        "version": coding.version,
        "code": coding.code,
        "display": coding.display,
        "user_selected": coding.user_selected,
        "created_by": created_by,
    }


async def _add_identifiers(
    session, flag_pk: int, org_id: str, identifiers, created_by: str
) -> None:
    for i in identifiers or []:
        a_type, a_id = _parse_assigner_ref(i.assigner) if i.assigner else (None, None)
        if a_type and a_id:
            await _validate_ref(session, org_id, a_type, a_id, "identifier.assigner")

        ident = FlagIdentifier(
            flag_pk=flag_pk,
            tenant_id=org_id,
            use=i.use,
            type_text=i.type_text,
            system=i.system,
            value=i.value,
            period_start=i.period_start,
            period_end=i.period_end,
            assigner_reference=i.assigner,
            assigner_type=a_type,
            assigner_id=a_id,
            assigner_display=i.assigner_display,
            assigner_identifier_use=i.assigner_identifier_use,
            assigner_identifier_type_system=i.assigner_identifier_type_system,
            assigner_identifier_type_version=i.assigner_identifier_type_version,
            assigner_identifier_type_code=i.assigner_identifier_type_code,
            assigner_identifier_type_display=i.assigner_identifier_type_display,
            assigner_identifier_type_text=i.assigner_identifier_type_text,
            assigner_identifier_type_user_selected=i.assigner_identifier_type_user_selected,
            assigner_identifier_system=i.assigner_identifier_system,
            assigner_identifier_value=i.assigner_identifier_value,
            assigner_identifier_period_start=i.assigner_identifier_period_start,
            assigner_identifier_period_end=i.assigner_identifier_period_end,
            created_by=created_by,
        )
        session.add(ident)
        await session.flush()

        if i.type_coding:
            for c in i.type_coding:
                session.add(
                    FlagIdentifierTypeCoding(
                        flag_identifier_id=ident.id,
                        **_coding_kwargs(c, org_id, created_by),
                    )
                )


async def _add_categories(
    session, flag_pk: int, org_id: str, categories, created_by: str
) -> None:
    for cat in categories or []:
        c_row = FlagCategory(
            flag_pk=flag_pk,
            tenant_id=org_id,
            text=cat.text,
            created_by=created_by,
        )
        session.add(c_row)
        await session.flush()

        if cat.coding:
            for cd in cat.coding:
                session.add(
                    FlagCategoryCoding(
                        flag_category_id=c_row.id,
                        **_coding_kwargs(cd, org_id, created_by),
                    )
                )


def _add_code_codings(
    session, flag_pk: int, org_id: str, code_codings, created_by: str
) -> None:
    for c in code_codings or []:
        session.add(
            FlagCodeCoding(
                flag_pk=flag_pk,
                **_coding_kwargs(c, org_id, created_by),
            )
        )


class FlagRepository:
    """Repository handling database operations for Flag resources."""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    async def get_by_flag_id(self, flag_id: int) -> FlagModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(FlagModel).where(FlagModel.flag_id == flag_id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def get_by_flag_id_in_org(
        self, flag_id: int, org_id: str
    ) -> FlagModel | None:
        async with self.session_factory() as session:
            stmt = _with_relationships(
                select(FlagModel).where(
                    FlagModel.flag_id == flag_id,
                    FlagModel.tenant_id == org_id,
                )
            )
            return (await session.execute(stmt)).scalars().first()

    async def flag_belongs_to_org(self, flag_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(FlagModel.id).where(
                FlagModel.flag_id == flag_id,
                FlagModel.tenant_id == org_id,
            )
            return (await session.execute(stmt)).scalar_one_or_none() is not None

    async def create_full(
        self, payload: FlagCreateSchema, org_id: str, created_by: str
    ) -> FlagModel:
        async with self.session_factory() as session:
            s_type, s_id = _parse_subject_ref(payload.subject)
            await _validate_ref(session, org_id, s_type, s_id, "subject")

            e_type, e_id = (
                _parse_encounter_ref(payload.encounter)
                if payload.encounter
                else (None, None)
            )
            if e_type and e_id:
                await _validate_ref(session, org_id, e_type, e_id, "encounter")

            a_type, a_id = (
                _parse_author_ref(payload.author) if payload.author else (None, None)
            )
            if a_type and a_id:
                await _validate_ref(session, org_id, a_type, a_id, "author")

            model = FlagModel(
                tenant_id=org_id,
                created_by=created_by,
                status=payload.status,
                code_text=payload.code_text,
                subject_reference=payload.subject,
                subject_type=s_type,
                subject_id=s_id,
                subject_display=payload.subject_display,
                period_start=payload.period_start,
                period_end=payload.period_end,
                encounter_reference=payload.encounter,
                encounter_type=e_type,
                encounter_id=e_id,
                encounter_display=payload.encounter_display,
                author_reference=payload.author,
                author_type=a_type,
                author_id=a_id,
                author_display=payload.author_display,
            )
            session.add(model)
            await session.flush()

            await _add_identifiers(
                session, model.id, org_id, payload.identifier, created_by
            )
            await _add_categories(
                session, model.id, org_id, payload.category, created_by
            )
            _add_code_codings(
                session, model.id, org_id, payload.code_coding, created_by
            )

            await session.commit()

            stmt = _with_relationships(
                select(FlagModel).where(FlagModel.id == model.id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def patch_full(
        self,
        flag_id: int,
        payload: FlagPatchSchema,
        org_id: str,
        updated_by: str,
    ) -> FlagModel | None:
        async with self.session_factory() as session:
            stmt = select(FlagModel).where(
                FlagModel.flag_id == flag_id,
                FlagModel.tenant_id == org_id,
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return None

            provided = payload.model_fields_set

            if "status" in provided and payload.status is not None:
                model.status = payload.status

            if "code_text" in provided:
                model.code_text = payload.code_text

            if "subject" in provided and payload.subject:
                s_type, s_id = _parse_subject_ref(payload.subject)
                await _validate_ref(session, org_id, s_type, s_id, "subject")
                model.subject_reference = payload.subject
                model.subject_type = s_type
                model.subject_id = s_id

            if "subject_display" in provided:
                model.subject_display = payload.subject_display

            if "period_start" in provided:
                model.period_start = payload.period_start

            if "period_end" in provided:
                model.period_end = payload.period_end

            if "encounter" in provided:
                if payload.encounter:
                    e_type, e_id = _parse_encounter_ref(payload.encounter)
                    await _validate_ref(session, org_id, e_type, e_id, "encounter")
                    model.encounter_reference = payload.encounter
                    model.encounter_type = e_type
                    model.encounter_id = e_id
                else:
                    model.encounter_reference = None
                    model.encounter_type = None
                    model.encounter_id = None

            if "encounter_display" in provided:
                model.encounter_display = payload.encounter_display

            if "author" in provided:
                if payload.author:
                    a_type, a_id = _parse_author_ref(payload.author)
                    await _validate_ref(session, org_id, a_type, a_id, "author")
                    model.author_reference = payload.author
                    model.author_type = a_type
                    model.author_id = a_id
                else:
                    model.author_reference = None
                    model.author_type = None
                    model.author_id = None

            if "author_display" in provided:
                model.author_display = payload.author_display

            model.updated_by = updated_by

            effective_org_id = model.tenant_id

            if "identifier" in provided:
                # Delete grandchildren first
                await session.execute(
                    delete(FlagIdentifierTypeCoding).where(
                        FlagIdentifierTypeCoding.flag_identifier_id.in_(
                            select(FlagIdentifier.id).where(
                                FlagIdentifier.flag_pk == model.id
                            )
                        )
                    )
                )
                await session.execute(
                    delete(FlagIdentifier).where(
                        FlagIdentifier.flag_pk == model.id
                    )
                )
                await _add_identifiers(
                    session, model.id, effective_org_id, payload.identifier, updated_by
                )

            if "category" in provided:
                # Delete grandchildren first
                await session.execute(
                    delete(FlagCategoryCoding).where(
                        FlagCategoryCoding.flag_category_id.in_(
                            select(FlagCategory.id).where(
                                FlagCategory.flag_pk == model.id
                            )
                        )
                    )
                )
                await session.execute(
                    delete(FlagCategory).where(
                        FlagCategory.flag_pk == model.id
                    )
                )
                await _add_categories(
                    session, model.id, effective_org_id, payload.category, updated_by
                )

            if "code_coding" in provided:
                await session.execute(
                    delete(FlagCodeCoding).where(
                        FlagCodeCoding.flag_pk == model.id
                    )
                )
                _add_code_codings(
                    session, model.id, effective_org_id, payload.code_coding, updated_by
                )

            await session.commit()

            stmt = _with_relationships(
                select(FlagModel).where(FlagModel.id == model.id)
            )
            return (await session.execute(stmt)).scalars().first()

    async def list(
        self,
        org_id: str,
        subject: str | None = None,
        status: str | None = None,
        encounter: str | None = None,
        author: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[list[FlagModel], int]:
        async with self.session_factory() as session:
            stmt = select(FlagModel).where(FlagModel.tenant_id == org_id)

            if subject:
                s_type, s_id = _parse_subject_ref(subject)
                if s_id is not None:
                    stmt = stmt.where(
                        FlagModel.subject_type == s_type,
                        FlagModel.subject_id == s_id,
                    )
                else:
                    stmt = stmt.where(FlagModel.subject_reference == subject)

            if status:
                stmt = stmt.where(FlagModel.status == status)

            if encounter:
                e_type, e_id = _parse_encounter_ref(encounter)
                if e_id is not None:
                    stmt = stmt.where(
                        FlagModel.encounter_type == e_type,
                        FlagModel.encounter_id == e_id,
                    )
                else:
                    stmt = stmt.where(FlagModel.encounter_reference == encounter)

            if author:
                a_type, a_id = _parse_author_ref(author)
                if a_id is not None:
                    stmt = stmt.where(
                        FlagModel.author_type == a_type,
                        FlagModel.author_id == a_id,
                    )
                else:
                    stmt = stmt.where(FlagModel.author_reference == author)

            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = (await session.execute(count_stmt)).scalar() or 0

            sort_col, sort_desc = resolve_sort(
                sort, _SORTABLE_FIELDS, FlagModel.id, default_desc=True
            )
            data_stmt = (
                _with_relationships(stmt)
                .order_by(sort_col.desc() if sort_desc else sort_col.asc())
                .limit(limit)
                .offset(offset)
            )
            items = list((await session.execute(data_stmt)).scalars().all())
            return items, total

    async def delete(self, flag_id: int, org_id: str) -> bool:
        async with self.session_factory() as session:
            stmt = select(FlagModel).where(
                FlagModel.flag_id == flag_id,
                FlagModel.tenant_id == org_id,
            )
            model = (await session.execute(stmt)).scalars().first()
            if not model:
                return False

            await session.delete(model)
            await session.commit()
            return True
