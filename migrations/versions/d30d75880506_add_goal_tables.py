"""add_goal_tables

Revision ID: d30d75880506
Revises: 87f0ee83046e
Create Date: 2026-10-31 17:27:18.418266

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd30d75880506'
down_revision: Union[str, None] = '87f0ee83046e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Create Enum Types ───────────────────────────────────────────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE goal_lifecycle_status AS ENUM (
                'proposed', 'planned', 'accepted', 'active', 'on-hold',
                'completed', 'cancelled', 'entered-in-error', 'rejected'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE goal_subject_reference_type AS ENUM ('Patient', 'Group', 'Organization');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE goal_expressed_by_reference_type AS ENUM ('Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE goal_outcome_reference_type AS ENUM ('Observation');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # ── 2. Create Public ID Sequence ───────────────────────────────────────────
    op.execute("CREATE SEQUENCE IF NOT EXISTS goal_pub_seq START WITH 460000 INCREMENT BY 1")

    # ── 3. Create Tables and Indexes ───────────────────────────────────────────
    op.create_table(
        'goal',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('goal_id', sa.BigInteger(), nullable=False),
        sa.Column('lifecycle_status', postgresql.ENUM('proposed', 'planned', 'accepted', 'active', 'on-hold', 'completed', 'cancelled', 'entered-in-error', 'rejected', name='goal_lifecycle_status', create_type=False), nullable=False),
        sa.Column('achievement_status_text', sa.String(), nullable=True),
        sa.Column('priority_text', sa.String(), nullable=True),
        sa.Column('description_text', sa.String(), nullable=True),
        sa.Column('subject_reference', sa.String(), nullable=False),
        sa.Column('subject_type', postgresql.ENUM('Patient', 'Group', 'Organization', name='goal_subject_reference_type', create_type=False), nullable=False),
        sa.Column('subject_id', sa.BigInteger(), nullable=True),
        sa.Column('subject_display', sa.String(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('start_codeable_concept_text', sa.String(), nullable=True),
        sa.Column('status_date', sa.Date(), nullable=True),
        sa.Column('status_reason', sa.String(), nullable=True),
        sa.Column('expressed_by_reference', sa.String(), nullable=True),
        sa.Column('expressed_by_type', postgresql.ENUM('Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', name='goal_expressed_by_reference_type', create_type=False), nullable=True),
        sa.Column('expressed_by_id', sa.BigInteger(), nullable=True),
        sa.Column('expressed_by_display', sa.String(), nullable=True),
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goal_goal_id'), 'goal', ['goal_id'], unique=True)
    op.create_index(op.f('ix_goal_tenant_id'), 'goal', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_goal_created_at'), 'goal', ['created_at'], unique=False)
    op.create_index(op.f('ix_goal_updated_at'), 'goal', ['updated_at'], unique=False)
    op.create_index(op.f('ix_goal_subject_id'), 'goal', ['subject_id'], unique=False)
    op.create_index(op.f('ix_goal_expressed_by_id'), 'goal', ['expressed_by_id'], unique=False)

    # Sibling Coding tables for 0..1 CodeableConcepts on goal
    for table_name in (
        'goal_achievement_status_coding',
        'goal_priority_coding',
        'goal_description_coding',
        'goal_start_coding',
    ):
        op.create_table(
            table_name,
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('goal_pk', sa.BigInteger(), nullable=False),
            sa.Column('system', sa.String(), nullable=True),
            sa.Column('version', sa.String(), nullable=True),
            sa.Column('code', sa.String(), nullable=True),
            sa.Column('display', sa.String(), nullable=True),
            sa.Column('user_selected', sa.Boolean(), nullable=True),
            sa.Column('tenant_id', sa.String(), nullable=False),
            sa.Column('created_by', sa.String(), nullable=False),
            sa.Column('updated_by', sa.String(), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['goal_pk'], ['goal.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f(f'ix_{table_name}_goal_pk'), table_name, ['goal_pk'], unique=False)
        op.create_index(op.f(f'ix_{table_name}_tenant_id'), table_name, ['tenant_id'], unique=False)
        op.create_index(op.f(f'ix_{table_name}_created_at'), table_name, ['created_at'], unique=False)
        op.create_index(op.f(f'ix_{table_name}_updated_at'), table_name, ['updated_at'], unique=False)

    # ── goal_identifier & goal_identifier_type_coding ─────────────────────────
    op.create_table(
        'goal_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('goal_pk', sa.BigInteger(), nullable=False),
        sa.Column('use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigner_reference', sa.String(), nullable=True),
        sa.Column('assigner_id', sa.BigInteger(), nullable=True),
        sa.Column('assigner_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
        sa.Column('assigner_display', sa.String(), nullable=True),
        sa.Column('assigner_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('assigner_identifier_type_system', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_version', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_code', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_display', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_text', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('assigner_identifier_system', sa.String(), nullable=True),
        sa.Column('assigner_identifier_value', sa.String(), nullable=True),
        sa.Column('assigner_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigner_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['goal_pk'], ['goal.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goal_identifier_goal_pk'), 'goal_identifier', ['goal_pk'], unique=False)
    op.create_index(op.f('ix_goal_identifier_tenant_id'), 'goal_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_goal_identifier_assigner_id'), 'goal_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_goal_identifier_created_at'), 'goal_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_goal_identifier_updated_at'), 'goal_identifier', ['updated_at'], unique=False)

    op.create_table(
        'goal_identifier_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('goal_identifier_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['goal_identifier_id'], ['goal_identifier.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goal_identifier_type_coding_goal_identifier_id'), 'goal_identifier_type_coding', ['goal_identifier_id'], unique=False)
    op.create_index(op.f('ix_goal_identifier_type_coding_tenant_id'), 'goal_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_goal_identifier_type_coding_created_at'), 'goal_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_goal_identifier_type_coding_updated_at'), 'goal_identifier_type_coding', ['updated_at'], unique=False)

    # ── goal_category & goal_category_coding ──────────────────────────────────
    op.create_table(
        'goal_category',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('goal_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['goal_pk'], ['goal.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goal_category_goal_pk'), 'goal_category', ['goal_pk'], unique=False)
    op.create_index(op.f('ix_goal_category_tenant_id'), 'goal_category', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_goal_category_created_at'), 'goal_category', ['created_at'], unique=False)
    op.create_index(op.f('ix_goal_category_updated_at'), 'goal_category', ['updated_at'], unique=False)

    op.create_table(
        'goal_category_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('goal_category_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['goal_category_id'], ['goal_category.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goal_category_coding_goal_category_id'), 'goal_category_coding', ['goal_category_id'], unique=False)
    op.create_index(op.f('ix_goal_category_coding_tenant_id'), 'goal_category_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_goal_category_coding_created_at'), 'goal_category_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_goal_category_coding_updated_at'), 'goal_category_coding', ['updated_at'], unique=False)

    # ── goal_target & grandchild codings ──────────────────────────────────────
    op.create_table(
        'goal_target',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('goal_pk', sa.BigInteger(), nullable=False),
        sa.Column('measure_text', sa.String(), nullable=True),
        sa.Column('detail_string', sa.Text(), nullable=True),
        sa.Column('detail_boolean', sa.Boolean(), nullable=True),
        sa.Column('detail_integer', sa.Integer(), nullable=True),
        sa.Column('detail_quantity_value', sa.Numeric(), nullable=True),
        sa.Column('detail_quantity_unit', sa.String(), nullable=True),
        sa.Column('detail_quantity_system', sa.String(), nullable=True),
        sa.Column('detail_quantity_code', sa.String(), nullable=True),
        sa.Column('detail_quantity_comparator', sa.String(), nullable=True),
        sa.Column('detail_range_low_value', sa.Numeric(), nullable=True),
        sa.Column('detail_range_low_unit', sa.String(), nullable=True),
        sa.Column('detail_range_low_system', sa.String(), nullable=True),
        sa.Column('detail_range_low_code', sa.String(), nullable=True),
        sa.Column('detail_range_high_value', sa.Numeric(), nullable=True),
        sa.Column('detail_range_high_unit', sa.String(), nullable=True),
        sa.Column('detail_range_high_system', sa.String(), nullable=True),
        sa.Column('detail_range_high_code', sa.String(), nullable=True),
        sa.Column('detail_ratio_numerator_value', sa.Numeric(), nullable=True),
        sa.Column('detail_ratio_numerator_unit', sa.String(), nullable=True),
        sa.Column('detail_ratio_numerator_system', sa.String(), nullable=True),
        sa.Column('detail_ratio_numerator_code', sa.String(), nullable=True),
        sa.Column('detail_ratio_denominator_value', sa.Numeric(), nullable=True),
        sa.Column('detail_ratio_denominator_unit', sa.String(), nullable=True),
        sa.Column('detail_ratio_denominator_system', sa.String(), nullable=True),
        sa.Column('detail_ratio_denominator_code', sa.String(), nullable=True),
        sa.Column('detail_codeable_concept_text', sa.String(), nullable=True),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('due_duration_value', sa.Numeric(), nullable=True),
        sa.Column('due_duration_unit', sa.String(), nullable=True),
        sa.Column('due_duration_system', sa.String(), nullable=True),
        sa.Column('due_duration_code', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['goal_pk'], ['goal.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goal_target_goal_pk'), 'goal_target', ['goal_pk'], unique=False)
    op.create_index(op.f('ix_goal_target_tenant_id'), 'goal_target', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_goal_target_created_at'), 'goal_target', ['created_at'], unique=False)
    op.create_index(op.f('ix_goal_target_updated_at'), 'goal_target', ['updated_at'], unique=False)

    op.create_table(
        'goal_target_measure_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('goal_target_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['goal_target_id'], ['goal_target.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goal_target_measure_coding_goal_target_id'), 'goal_target_measure_coding', ['goal_target_id'], unique=False)
    op.create_index(op.f('ix_goal_target_measure_coding_tenant_id'), 'goal_target_measure_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_goal_target_measure_coding_created_at'), 'goal_target_measure_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_goal_target_measure_coding_updated_at'), 'goal_target_measure_coding', ['updated_at'], unique=False)

    op.create_table(
        'goal_target_detail_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('goal_target_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['goal_target_id'], ['goal_target.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goal_target_detail_coding_goal_target_id'), 'goal_target_detail_coding', ['goal_target_id'], unique=False)
    op.create_index(op.f('ix_goal_target_detail_coding_tenant_id'), 'goal_target_detail_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_goal_target_detail_coding_created_at'), 'goal_target_detail_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_goal_target_detail_coding_updated_at'), 'goal_target_detail_coding', ['updated_at'], unique=False)

    # ── goal_addresses ────────────────────────────────────────────────────────
    op.create_table(
        'goal_addresses',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('goal_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['goal_pk'], ['goal.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goal_addresses_goal_pk'), 'goal_addresses', ['goal_pk'], unique=False)
    op.create_index(op.f('ix_goal_addresses_reference_id'), 'goal_addresses', ['reference_id'], unique=False)
    op.create_index(op.f('ix_goal_addresses_tenant_id'), 'goal_addresses', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_goal_addresses_created_at'), 'goal_addresses', ['created_at'], unique=False)
    op.create_index(op.f('ix_goal_addresses_updated_at'), 'goal_addresses', ['updated_at'], unique=False)

    # ── goal_note ─────────────────────────────────────────────────────────────
    op.create_table(
        'goal_note',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('goal_pk', sa.BigInteger(), nullable=False),
        sa.Column('author_string', sa.String(), nullable=True),
        sa.Column('author_reference', sa.String(), nullable=True),
        sa.Column('author_type', sa.String(), nullable=True),
        sa.Column('author_id', sa.BigInteger(), nullable=True),
        sa.Column('author_display', sa.String(), nullable=True),
        sa.Column('time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['goal_pk'], ['goal.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goal_note_goal_pk'), 'goal_note', ['goal_pk'], unique=False)
    op.create_index(op.f('ix_goal_note_author_id'), 'goal_note', ['author_id'], unique=False)
    op.create_index(op.f('ix_goal_note_tenant_id'), 'goal_note', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_goal_note_created_at'), 'goal_note', ['created_at'], unique=False)
    op.create_index(op.f('ix_goal_note_updated_at'), 'goal_note', ['updated_at'], unique=False)

    # ── goal_outcome_code & grandchild codings ────────────────────────────────
    op.create_table(
        'goal_outcome_code',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('goal_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['goal_pk'], ['goal.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goal_outcome_code_goal_pk'), 'goal_outcome_code', ['goal_pk'], unique=False)
    op.create_index(op.f('ix_goal_outcome_code_tenant_id'), 'goal_outcome_code', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_goal_outcome_code_created_at'), 'goal_outcome_code', ['created_at'], unique=False)
    op.create_index(op.f('ix_goal_outcome_code_updated_at'), 'goal_outcome_code', ['updated_at'], unique=False)

    op.create_table(
        'goal_outcome_code_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('goal_outcome_code_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['goal_outcome_code_id'], ['goal_outcome_code.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goal_outcome_code_coding_goal_outcome_code_id'), 'goal_outcome_code_coding', ['goal_outcome_code_id'], unique=False)
    op.create_index(op.f('ix_goal_outcome_code_coding_tenant_id'), 'goal_outcome_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_goal_outcome_code_coding_created_at'), 'goal_outcome_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_goal_outcome_code_coding_updated_at'), 'goal_outcome_code_coding', ['updated_at'], unique=False)

    # ── goal_outcome_reference ────────────────────────────────────────────────
    op.create_table(
        'goal_outcome_reference',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('goal_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Observation', name='goal_outcome_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['goal_pk'], ['goal.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_goal_outcome_reference_goal_pk'), 'goal_outcome_reference', ['goal_pk'], unique=False)
    op.create_index(op.f('ix_goal_outcome_reference_reference_id'), 'goal_outcome_reference', ['reference_id'], unique=False)
    op.create_index(op.f('ix_goal_outcome_reference_tenant_id'), 'goal_outcome_reference', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_goal_outcome_reference_created_at'), 'goal_outcome_reference', ['created_at'], unique=False)
    op.create_index(op.f('ix_goal_outcome_reference_updated_at'), 'goal_outcome_reference', ['updated_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_table('goal_outcome_reference')
    op.drop_table('goal_outcome_code_coding')
    op.drop_table('goal_outcome_code')
    op.drop_table('goal_note')
    op.drop_table('goal_addresses')
    op.drop_table('goal_target_detail_coding')
    op.drop_table('goal_target_measure_coding')
    op.drop_table('goal_target')
    op.drop_table('goal_category_coding')
    op.drop_table('goal_category')
    op.drop_table('goal_identifier_type_coding')
    op.drop_table('goal_identifier')
    op.drop_table('goal_start_coding')
    op.drop_table('goal_description_coding')
    op.drop_table('goal_priority_coding')
    op.drop_table('goal_achievement_status_coding')
    op.drop_table('goal')

    # Drop sequence
    op.execute("DROP SEQUENCE IF EXISTS goal_pub_seq")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS goal_outcome_reference_type")
    op.execute("DROP TYPE IF EXISTS goal_expressed_by_reference_type")
    op.execute("DROP TYPE IF EXISTS goal_subject_reference_type")
    op.execute("DROP TYPE IF EXISTS goal_lifecycle_status")
