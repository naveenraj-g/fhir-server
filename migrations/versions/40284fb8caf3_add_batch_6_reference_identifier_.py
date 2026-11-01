"""add batch 6 reference identifier fallback columns

Revision ID: 40284fb8caf3
Revises: 9e244ee31e3b
Create Date: 2026-11-01 21:35:38.863384

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '40284fb8caf3'
down_revision: Union[str, None] = '9e244ee31e3b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Observation ──────────────────────────────────────────────────────────
    # observation_note: add 11 author_identifier_* fallback columns
    op.add_column('observation_note', sa.Column('author_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('observation_note', sa.Column('author_identifier_type_system', sa.String(), nullable=True))
    op.add_column('observation_note', sa.Column('author_identifier_type_version', sa.String(), nullable=True))
    op.add_column('observation_note', sa.Column('author_identifier_type_code', sa.String(), nullable=True))
    op.add_column('observation_note', sa.Column('author_identifier_type_display', sa.String(), nullable=True))
    op.add_column('observation_note', sa.Column('author_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('observation_note', sa.Column('author_identifier_type_text', sa.String(), nullable=True))
    op.add_column('observation_note', sa.Column('author_identifier_system', sa.String(), nullable=True))
    op.add_column('observation_note', sa.Column('author_identifier_value', sa.String(), nullable=True))
    op.add_column('observation_note', sa.Column('author_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('observation_note', sa.Column('author_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # ── 2. Condition ────────────────────────────────────────────────────────────
    # condition: add 7 missing fallback columns to subject, encounter, recorder, asserter
    for prefix in ('subject', 'encounter', 'recorder', 'asserter'):
        op.add_column('condition', sa.Column(f'{prefix}_identifier_type_system', sa.String(), nullable=True))
        op.add_column('condition', sa.Column(f'{prefix}_identifier_type_version', sa.String(), nullable=True))
        op.add_column('condition', sa.Column(f'{prefix}_identifier_type_code', sa.String(), nullable=True))
        op.add_column('condition', sa.Column(f'{prefix}_identifier_type_display', sa.String(), nullable=True))
        op.add_column('condition', sa.Column(f'{prefix}_identifier_type_user_selected', sa.Boolean(), nullable=True))
        op.add_column('condition', sa.Column(f'{prefix}_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
        op.add_column('condition', sa.Column(f'{prefix}_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # condition_note: add 7 missing fallback columns to author_identifier_*
    op.add_column('condition_note', sa.Column('author_identifier_type_system', sa.String(), nullable=True))
    op.add_column('condition_note', sa.Column('author_identifier_type_version', sa.String(), nullable=True))
    op.add_column('condition_note', sa.Column('author_identifier_type_code', sa.String(), nullable=True))
    op.add_column('condition_note', sa.Column('author_identifier_type_display', sa.String(), nullable=True))
    op.add_column('condition_note', sa.Column('author_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('condition_note', sa.Column('author_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('condition_note', sa.Column('author_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # condition_stage_assessment: add 7 missing fallback columns to reference_identifier_*
    op.add_column('condition_stage_assessment', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))
    op.add_column('condition_stage_assessment', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))
    op.add_column('condition_stage_assessment', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))
    op.add_column('condition_stage_assessment', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))
    op.add_column('condition_stage_assessment', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('condition_stage_assessment', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('condition_stage_assessment', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # condition_evidence_detail: add 7 missing fallback columns to reference_identifier_*
    op.add_column('condition_evidence_detail', sa.Column('reference_identifier_type_system', sa.String(), nullable=True))
    op.add_column('condition_evidence_detail', sa.Column('reference_identifier_type_version', sa.String(), nullable=True))
    op.add_column('condition_evidence_detail', sa.Column('reference_identifier_type_code', sa.String(), nullable=True))
    op.add_column('condition_evidence_detail', sa.Column('reference_identifier_type_display', sa.String(), nullable=True))
    op.add_column('condition_evidence_detail', sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('condition_evidence_detail', sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('condition_evidence_detail', sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # condition_identifier: add 7 missing fallback columns to assigner_identifier_*
    op.add_column('condition_identifier', sa.Column('assigner_identifier_type_system', sa.String(), nullable=True))
    op.add_column('condition_identifier', sa.Column('assigner_identifier_type_version', sa.String(), nullable=True))
    op.add_column('condition_identifier', sa.Column('assigner_identifier_type_code', sa.String(), nullable=True))
    op.add_column('condition_identifier', sa.Column('assigner_identifier_type_display', sa.String(), nullable=True))
    op.add_column('condition_identifier', sa.Column('assigner_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('condition_identifier', sa.Column('assigner_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('condition_identifier', sa.Column('assigner_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # ── 3. AllergyIntolerance ──────────────────────────────────────────────────
    # allergy_intolerance: add 11 fallback columns to patient, encounter, recorder, asserter
    for prefix in ('patient', 'encounter', 'recorder', 'asserter'):
        op.add_column('allergy_intolerance', sa.Column(f'{prefix}_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
        op.add_column('allergy_intolerance', sa.Column(f'{prefix}_identifier_type_system', sa.String(), nullable=True))
        op.add_column('allergy_intolerance', sa.Column(f'{prefix}_identifier_type_version', sa.String(), nullable=True))
        op.add_column('allergy_intolerance', sa.Column(f'{prefix}_identifier_type_code', sa.String(), nullable=True))
        op.add_column('allergy_intolerance', sa.Column(f'{prefix}_identifier_type_display', sa.String(), nullable=True))
        op.add_column('allergy_intolerance', sa.Column(f'{prefix}_identifier_type_user_selected', sa.Boolean(), nullable=True))
        op.add_column('allergy_intolerance', sa.Column(f'{prefix}_identifier_type_text', sa.String(), nullable=True))
        op.add_column('allergy_intolerance', sa.Column(f'{prefix}_identifier_system', sa.String(), nullable=True))
        op.add_column('allergy_intolerance', sa.Column(f'{prefix}_identifier_value', sa.String(), nullable=True))
        op.add_column('allergy_intolerance', sa.Column(f'{prefix}_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
        op.add_column('allergy_intolerance', sa.Column(f'{prefix}_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # allergy_intolerance_identifier: add 11 fallback columns to assigner_identifier_*
    op.add_column('allergy_intolerance_identifier', sa.Column('assigner_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('allergy_intolerance_identifier', sa.Column('assigner_identifier_type_system', sa.String(), nullable=True))
    op.add_column('allergy_intolerance_identifier', sa.Column('assigner_identifier_type_version', sa.String(), nullable=True))
    op.add_column('allergy_intolerance_identifier', sa.Column('assigner_identifier_type_code', sa.String(), nullable=True))
    op.add_column('allergy_intolerance_identifier', sa.Column('assigner_identifier_type_display', sa.String(), nullable=True))
    op.add_column('allergy_intolerance_identifier', sa.Column('assigner_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('allergy_intolerance_identifier', sa.Column('assigner_identifier_type_text', sa.String(), nullable=True))
    op.add_column('allergy_intolerance_identifier', sa.Column('assigner_identifier_system', sa.String(), nullable=True))
    op.add_column('allergy_intolerance_identifier', sa.Column('assigner_identifier_value', sa.String(), nullable=True))
    op.add_column('allergy_intolerance_identifier', sa.Column('assigner_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('allergy_intolerance_identifier', sa.Column('assigner_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # allergy_intolerance_note: add author_reference + 11 author_reference_identifier_* columns
    op.add_column('allergy_intolerance_note', sa.Column('author_reference', sa.String(), nullable=True))
    op.add_column('allergy_intolerance_note', sa.Column('author_reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('allergy_intolerance_note', sa.Column('author_reference_identifier_type_system', sa.String(), nullable=True))
    op.add_column('allergy_intolerance_note', sa.Column('author_reference_identifier_type_version', sa.String(), nullable=True))
    op.add_column('allergy_intolerance_note', sa.Column('author_reference_identifier_type_code', sa.String(), nullable=True))
    op.add_column('allergy_intolerance_note', sa.Column('author_reference_identifier_type_display', sa.String(), nullable=True))
    op.add_column('allergy_intolerance_note', sa.Column('author_reference_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('allergy_intolerance_note', sa.Column('author_reference_identifier_type_text', sa.String(), nullable=True))
    op.add_column('allergy_intolerance_note', sa.Column('author_reference_identifier_system', sa.String(), nullable=True))
    op.add_column('allergy_intolerance_note', sa.Column('author_reference_identifier_value', sa.String(), nullable=True))
    op.add_column('allergy_intolerance_note', sa.Column('author_reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('allergy_intolerance_note', sa.Column('author_reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))

    # allergy_intolerance_reaction_note: add author_reference + 11 author_reference_identifier_* columns
    op.add_column('allergy_intolerance_reaction_note', sa.Column('author_reference', sa.String(), nullable=True))
    op.add_column('allergy_intolerance_reaction_note', sa.Column('author_reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True))
    op.add_column('allergy_intolerance_reaction_note', sa.Column('author_reference_identifier_type_system', sa.String(), nullable=True))
    op.add_column('allergy_intolerance_reaction_note', sa.Column('author_reference_identifier_type_version', sa.String(), nullable=True))
    op.add_column('allergy_intolerance_reaction_note', sa.Column('author_reference_identifier_type_code', sa.String(), nullable=True))
    op.add_column('allergy_intolerance_reaction_note', sa.Column('author_reference_identifier_type_display', sa.String(), nullable=True))
    op.add_column('allergy_intolerance_reaction_note', sa.Column('author_reference_identifier_type_user_selected', sa.Boolean(), nullable=True))
    op.add_column('allergy_intolerance_reaction_note', sa.Column('author_reference_identifier_type_text', sa.String(), nullable=True))
    op.add_column('allergy_intolerance_reaction_note', sa.Column('author_reference_identifier_system', sa.String(), nullable=True))
    op.add_column('allergy_intolerance_reaction_note', sa.Column('author_reference_identifier_value', sa.String(), nullable=True))
    op.add_column('allergy_intolerance_reaction_note', sa.Column('author_reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True))
    op.add_column('allergy_intolerance_reaction_note', sa.Column('author_reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # allergy_intolerance_reaction_note
    for suffix in ('period_end', 'period_start', 'value', 'system', 'type_text', 'type_user_selected', 'type_display', 'type_code', 'type_version', 'type_system', 'use'):
        op.drop_column('allergy_intolerance_reaction_note', f'author_reference_identifier_{suffix}')
    op.drop_column('allergy_intolerance_reaction_note', 'author_reference')

    # allergy_intolerance_note
    for suffix in ('period_end', 'period_start', 'value', 'system', 'type_text', 'type_user_selected', 'type_display', 'type_code', 'type_version', 'type_system', 'use'):
        op.drop_column('allergy_intolerance_note', f'author_reference_identifier_{suffix}')
    op.drop_column('allergy_intolerance_note', 'author_reference')

    # allergy_intolerance_identifier
    for suffix in ('period_end', 'period_start', 'value', 'system', 'type_text', 'type_user_selected', 'type_display', 'type_code', 'type_version', 'type_system', 'use'):
        op.drop_column('allergy_intolerance_identifier', f'assigner_identifier_{suffix}')

    # allergy_intolerance
    for prefix in ('asserter', 'recorder', 'encounter', 'patient'):
        for suffix in ('period_end', 'period_start', 'value', 'system', 'type_text', 'type_user_selected', 'type_display', 'type_code', 'type_version', 'type_system', 'use'):
            op.drop_column('allergy_intolerance', f'{prefix}_identifier_{suffix}')

    # condition_identifier
    for suffix in ('period_end', 'period_start', 'type_user_selected', 'type_display', 'type_code', 'type_version', 'type_system'):
        op.drop_column('condition_identifier', f'assigner_identifier_{suffix}')

    # condition_evidence_detail
    for suffix in ('period_end', 'period_start', 'type_user_selected', 'type_display', 'type_code', 'type_version', 'type_system'):
        op.drop_column('condition_evidence_detail', f'reference_identifier_{suffix}')

    # condition_stage_assessment
    for suffix in ('period_end', 'period_start', 'type_user_selected', 'type_display', 'type_code', 'type_version', 'type_system'):
        op.drop_column('condition_stage_assessment', f'reference_identifier_{suffix}')

    # condition_note
    for suffix in ('period_end', 'period_start', 'type_user_selected', 'type_display', 'type_code', 'type_version', 'type_system'):
        op.drop_column('condition_note', f'author_identifier_{suffix}')

    # condition
    for prefix in ('asserter', 'recorder', 'encounter', 'subject'):
        for suffix in ('period_end', 'period_start', 'type_user_selected', 'type_display', 'type_code', 'type_version', 'type_system'):
            op.drop_column('condition', f'{prefix}_identifier_{suffix}')

    # observation_note
    for suffix in ('period_end', 'period_start', 'value', 'system', 'type_text', 'type_user_selected', 'type_display', 'type_code', 'type_version', 'type_system', 'use'):
        op.drop_column('observation_note', f'author_identifier_{suffix}')
