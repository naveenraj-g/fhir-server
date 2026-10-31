"""add_task_tables

Revision ID: 87f0ee83046e
Revises: dbf7519d8b31
Create Date: 2026-10-31 16:47:24.215045

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '87f0ee83046e'
down_revision: Union[str, None] = 'dbf7519d8b31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Create Enum Types ───────────────────────────────────────────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE task_status AS ENUM (
                'draft', 'requested', 'received', 'accepted', 'rejected',
                'ready', 'cancelled', 'in-progress', 'on-hold', 'failed',
                'completed', 'entered-in-error'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE task_intent AS ENUM (
                'unknown', 'proposal', 'plan', 'order', 'original-order',
                'reflex-order', 'filler-order', 'instance-order', 'option'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE task_priority AS ENUM ('routine', 'urgent', 'asap', 'stat');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE task_requester_reference_type AS ENUM (
                'Device', 'Organization', 'Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE task_owner_reference_type AS ENUM (
                'Practitioner', 'PractitionerRole', 'Organization', 'CareTeam',
                'HealthcareService', 'Patient', 'Device', 'RelatedPerson'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE task_location_reference_type AS ENUM ('Location');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE task_encounter_reference_type AS ENUM ('Encounter');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE task_restriction_recipient_reference_type AS ENUM (
                'Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', 'Group', 'Organization'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE task_insurance_reference_type AS ENUM ('Coverage', 'ClaimResponse');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE task_relevant_history_reference_type AS ENUM ('Provenance');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE task_part_of_reference_type AS ENUM ('Task');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # ── 2. Create Public ID Sequence ───────────────────────────────────────────
    op.execute("CREATE SEQUENCE IF NOT EXISTS task_pub_seq START WITH 280000 INCREMENT BY 1")

    # ── 3. Create Tables and Indexes ───────────────────────────────────────────
    op.create_table(
        'task',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_id', sa.BigInteger(), nullable=False),
        sa.Column('status', postgresql.ENUM('draft', 'requested', 'received', 'accepted', 'rejected', 'ready', 'cancelled', 'in-progress', 'on-hold', 'failed', 'completed', 'entered-in-error', name='task_status', create_type=False), nullable=False),
        sa.Column('intent', postgresql.ENUM('unknown', 'proposal', 'plan', 'order', 'original-order', 'reflex-order', 'filler-order', 'instance-order', 'option', name='task_intent', create_type=False), nullable=False),
        sa.Column('priority', postgresql.ENUM('routine', 'urgent', 'asap', 'stat', name='task_priority', create_type=False), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('instantiates_canonical', sa.String(), nullable=True),
        sa.Column('instantiates_uri', sa.String(), nullable=True),
        sa.Column('authored_on', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_modified', sa.DateTime(timezone=True), nullable=True),
        sa.Column('code_text', sa.String(), nullable=True),
        sa.Column('status_reason_text', sa.String(), nullable=True),
        sa.Column('business_status_text', sa.String(), nullable=True),
        sa.Column('reason_code_text', sa.String(), nullable=True),
        sa.Column('focus_reference', sa.String(), nullable=True),
        sa.Column('focus_type', sa.String(), nullable=True),
        sa.Column('focus_id', sa.BigInteger(), nullable=True),
        sa.Column('focus_display', sa.String(), nullable=True),
        sa.Column('for_reference', sa.String(), nullable=True),
        sa.Column('for_type', sa.String(), nullable=True),
        sa.Column('for_id', sa.BigInteger(), nullable=True),
        sa.Column('for_display', sa.String(), nullable=True),
        sa.Column('encounter_reference', sa.String(), nullable=True),
        sa.Column('encounter_type', postgresql.ENUM('Encounter', name='task_encounter_reference_type', create_type=False), nullable=True),
        sa.Column('encounter_id', sa.BigInteger(), nullable=True),
        sa.Column('encounter_display', sa.String(), nullable=True),
        sa.Column('execution_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('execution_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('requester_reference', sa.String(), nullable=True),
        sa.Column('requester_type', postgresql.ENUM('Device', 'Organization', 'Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', name='task_requester_reference_type', create_type=False), nullable=True),
        sa.Column('requester_id', sa.BigInteger(), nullable=True),
        sa.Column('requester_display', sa.String(), nullable=True),
        sa.Column('owner_reference', sa.String(), nullable=True),
        sa.Column('owner_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization', 'CareTeam', 'HealthcareService', 'Patient', 'Device', 'RelatedPerson', name='task_owner_reference_type', create_type=False), nullable=True),
        sa.Column('owner_id', sa.BigInteger(), nullable=True),
        sa.Column('owner_display', sa.String(), nullable=True),
        sa.Column('location_reference', sa.String(), nullable=True),
        sa.Column('location_type', postgresql.ENUM('Location', name='task_location_reference_type', create_type=False), nullable=True),
        sa.Column('location_id', sa.BigInteger(), nullable=True),
        sa.Column('location_display', sa.String(), nullable=True),
        sa.Column('reason_reference_reference', sa.String(), nullable=True),
        sa.Column('reason_reference_type', sa.String(), nullable=True),
        sa.Column('reason_reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reason_reference_display', sa.String(), nullable=True),
        sa.Column('group_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('group_identifier_system', sa.String(), nullable=True),
        sa.Column('group_identifier_value', sa.String(), nullable=True),
        sa.Column('group_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('group_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('group_identifier_assigner_reference', sa.String(), nullable=True),
        sa.Column('group_identifier_assigner_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
        sa.Column('group_identifier_assigner_id', sa.BigInteger(), nullable=True),
        sa.Column('group_identifier_assigner_display', sa.String(), nullable=True),
        sa.Column('restriction_repetitions', sa.Integer(), nullable=True),
        sa.Column('restriction_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('restriction_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_task_id'), 'task', ['task_id'], unique=True)
    op.create_index(op.f('ix_task_tenant_id'), 'task', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_task_created_at'), 'task', ['created_at'], unique=False)
    op.create_index(op.f('ix_task_updated_at'), 'task', ['updated_at'], unique=False)
    op.create_index(op.f('ix_task_focus_id'), 'task', ['focus_id'], unique=False)
    op.create_index(op.f('ix_task_for_id'), 'task', ['for_id'], unique=False)
    op.create_index(op.f('ix_task_encounter_id'), 'task', ['encounter_id'], unique=False)
    op.create_index(op.f('ix_task_requester_id'), 'task', ['requester_id'], unique=False)
    op.create_index(op.f('ix_task_owner_id'), 'task', ['owner_id'], unique=False)
    op.create_index(op.f('ix_task_location_id'), 'task', ['location_id'], unique=False)
    op.create_index(op.f('ix_task_reason_reference_id'), 'task', ['reason_reference_id'], unique=False)

    # ── Sibling Coding tables for 0..1 CodeableConcepts ────────────────────────
    for table_name in ('task_code_coding', 'task_status_reason_coding', 'task_business_status_coding', 'task_reason_code_coding'):
        op.create_table(
            table_name,
            sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
            sa.Column('task_pk', sa.BigInteger(), nullable=False),
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
            sa.ForeignKeyConstraint(['task_pk'], ['task.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f(f'ix_{table_name}_task_pk'), table_name, ['task_pk'], unique=False)
        op.create_index(op.f(f'ix_{table_name}_tenant_id'), table_name, ['tenant_id'], unique=False)
        op.create_index(op.f(f'ix_{table_name}_created_at'), table_name, ['created_at'], unique=False)
        op.create_index(op.f(f'ix_{table_name}_updated_at'), table_name, ['updated_at'], unique=False)

    # ── task_identifier & task_identifier_type_coding ─────────────────────────
    op.create_table(
        'task_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['task_pk'], ['task.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_identifier_task_pk'), 'task_identifier', ['task_pk'], unique=False)
    op.create_index(op.f('ix_task_identifier_tenant_id'), 'task_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_task_identifier_assigner_id'), 'task_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_task_identifier_created_at'), 'task_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_task_identifier_updated_at'), 'task_identifier', ['updated_at'], unique=False)

    op.create_table(
        'task_identifier_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_identifier_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['task_identifier_id'], ['task_identifier.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_identifier_type_coding_task_identifier_id'), 'task_identifier_type_coding', ['task_identifier_id'], unique=False)
    op.create_index(op.f('ix_task_identifier_type_coding_tenant_id'), 'task_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_task_identifier_type_coding_created_at'), 'task_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_task_identifier_type_coding_updated_at'), 'task_identifier_type_coding', ['updated_at'], unique=False)

    # ── task_performer_type & task_performer_type_coding ──────────────────────
    op.create_table(
        'task_performer_type',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['task_pk'], ['task.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_performer_type_task_pk'), 'task_performer_type', ['task_pk'], unique=False)
    op.create_index(op.f('ix_task_performer_type_tenant_id'), 'task_performer_type', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_task_performer_type_created_at'), 'task_performer_type', ['created_at'], unique=False)
    op.create_index(op.f('ix_task_performer_type_updated_at'), 'task_performer_type', ['updated_at'], unique=False)

    op.create_table(
        'task_performer_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_performer_type_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['task_performer_type_id'], ['task_performer_type.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_performer_type_coding_task_performer_type_id'), 'task_performer_type_coding', ['task_performer_type_id'], unique=False)
    op.create_index(op.f('ix_task_performer_type_coding_tenant_id'), 'task_performer_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_task_performer_type_coding_created_at'), 'task_performer_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_task_performer_type_coding_updated_at'), 'task_performer_type_coding', ['updated_at'], unique=False)

    # ── Reference child tables ────────────────────────────────────────────────
    # 1. task_based_on (open set)
    op.create_table(
        'task_based_on',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['task_pk'], ['task.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_based_on_task_pk'), 'task_based_on', ['task_pk'], unique=False)
    op.create_index(op.f('ix_task_based_on_reference_id'), 'task_based_on', ['reference_id'], unique=False)
    op.create_index(op.f('ix_task_based_on_tenant_id'), 'task_based_on', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_task_based_on_created_at'), 'task_based_on', ['created_at'], unique=False)
    op.create_index(op.f('ix_task_based_on_updated_at'), 'task_based_on', ['updated_at'], unique=False)

    # 2. task_part_of
    op.create_table(
        'task_part_of',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Task', name='task_part_of_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['task_pk'], ['task.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_part_of_task_pk'), 'task_part_of', ['task_pk'], unique=False)
    op.create_index(op.f('ix_task_part_of_reference_id'), 'task_part_of', ['reference_id'], unique=False)
    op.create_index(op.f('ix_task_part_of_tenant_id'), 'task_part_of', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_task_part_of_created_at'), 'task_part_of', ['created_at'], unique=False)
    op.create_index(op.f('ix_task_part_of_updated_at'), 'task_part_of', ['updated_at'], unique=False)

    # 3. task_insurance
    op.create_table(
        'task_insurance',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Coverage', 'ClaimResponse', name='task_insurance_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['task_pk'], ['task.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_insurance_task_pk'), 'task_insurance', ['task_pk'], unique=False)
    op.create_index(op.f('ix_task_insurance_reference_id'), 'task_insurance', ['reference_id'], unique=False)
    op.create_index(op.f('ix_task_insurance_tenant_id'), 'task_insurance', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_task_insurance_created_at'), 'task_insurance', ['created_at'], unique=False)
    op.create_index(op.f('ix_task_insurance_updated_at'), 'task_insurance', ['updated_at'], unique=False)

    # 4. task_relevant_history
    op.create_table(
        'task_relevant_history',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Provenance', name='task_relevant_history_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['task_pk'], ['task.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_relevant_history_task_pk'), 'task_relevant_history', ['task_pk'], unique=False)
    op.create_index(op.f('ix_task_relevant_history_reference_id'), 'task_relevant_history', ['reference_id'], unique=False)
    op.create_index(op.f('ix_task_relevant_history_tenant_id'), 'task_relevant_history', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_task_relevant_history_created_at'), 'task_relevant_history', ['created_at'], unique=False)
    op.create_index(op.f('ix_task_relevant_history_updated_at'), 'task_relevant_history', ['updated_at'], unique=False)

    # 5. task_restriction_recipient
    op.create_table(
        'task_restriction_recipient',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', 'Group', 'Organization', name='task_restriction_recipient_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['task_pk'], ['task.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_restriction_recipient_task_pk'), 'task_restriction_recipient', ['task_pk'], unique=False)
    op.create_index(op.f('ix_task_restriction_recipient_reference_id'), 'task_restriction_recipient', ['reference_id'], unique=False)
    op.create_index(op.f('ix_task_restriction_recipient_tenant_id'), 'task_restriction_recipient', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_task_restriction_recipient_created_at'), 'task_restriction_recipient', ['created_at'], unique=False)
    op.create_index(op.f('ix_task_restriction_recipient_updated_at'), 'task_restriction_recipient', ['updated_at'], unique=False)

    # ── task_note ─────────────────────────────────────────────────────────────
    op.create_table(
        'task_note',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['task_pk'], ['task.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_note_task_pk'), 'task_note', ['task_pk'], unique=False)
    op.create_index(op.f('ix_task_note_author_id'), 'task_note', ['author_id'], unique=False)
    op.create_index(op.f('ix_task_note_tenant_id'), 'task_note', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_task_note_created_at'), 'task_note', ['created_at'], unique=False)
    op.create_index(op.f('ix_task_note_updated_at'), 'task_note', ['updated_at'], unique=False)

    # ── task_input & task_input_type_coding ───────────────────────────────────
    op.create_table(
        'task_input',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_pk', sa.BigInteger(), nullable=False),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('value_string', sa.Text(), nullable=True),
        sa.Column('value_boolean', sa.Boolean(), nullable=True),
        sa.Column('value_integer', sa.Integer(), nullable=True),
        sa.Column('value_decimal', sa.Numeric(), nullable=True),
        sa.Column('value_date', sa.Date(), nullable=True),
        sa.Column('value_date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('value_time', sa.Time(), nullable=True),
        sa.Column('value_uri', sa.String(), nullable=True),
        sa.Column('value_code', sa.String(), nullable=True),
        sa.Column('value_reference_reference', sa.String(), nullable=True),
        sa.Column('value_reference_type', sa.String(), nullable=True),
        sa.Column('value_reference_id', sa.BigInteger(), nullable=True),
        sa.Column('value_reference_display', sa.String(), nullable=True),
        sa.Column('value_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['task_pk'], ['task.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_input_task_pk'), 'task_input', ['task_pk'], unique=False)
    op.create_index(op.f('ix_task_input_value_reference_id'), 'task_input', ['value_reference_id'], unique=False)
    op.create_index(op.f('ix_task_input_tenant_id'), 'task_input', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_task_input_created_at'), 'task_input', ['created_at'], unique=False)
    op.create_index(op.f('ix_task_input_updated_at'), 'task_input', ['updated_at'], unique=False)

    op.create_table(
        'task_input_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_input_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['task_input_id'], ['task_input.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_input_type_coding_task_input_id'), 'task_input_type_coding', ['task_input_id'], unique=False)
    op.create_index(op.f('ix_task_input_type_coding_tenant_id'), 'task_input_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_task_input_type_coding_created_at'), 'task_input_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_task_input_type_coding_updated_at'), 'task_input_type_coding', ['updated_at'], unique=False)

    # ── task_output & task_output_type_coding ─────────────────────────────────
    op.create_table(
        'task_output',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_pk', sa.BigInteger(), nullable=False),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('value_string', sa.Text(), nullable=True),
        sa.Column('value_boolean', sa.Boolean(), nullable=True),
        sa.Column('value_integer', sa.Integer(), nullable=True),
        sa.Column('value_decimal', sa.Numeric(), nullable=True),
        sa.Column('value_date', sa.Date(), nullable=True),
        sa.Column('value_date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('value_time', sa.Time(), nullable=True),
        sa.Column('value_uri', sa.String(), nullable=True),
        sa.Column('value_code', sa.String(), nullable=True),
        sa.Column('value_reference_reference', sa.String(), nullable=True),
        sa.Column('value_reference_type', sa.String(), nullable=True),
        sa.Column('value_reference_id', sa.BigInteger(), nullable=True),
        sa.Column('value_reference_display', sa.String(), nullable=True),
        sa.Column('value_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['task_pk'], ['task.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_output_task_pk'), 'task_output', ['task_pk'], unique=False)
    op.create_index(op.f('ix_task_output_value_reference_id'), 'task_output', ['value_reference_id'], unique=False)
    op.create_index(op.f('ix_task_output_tenant_id'), 'task_output', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_task_output_created_at'), 'task_output', ['created_at'], unique=False)
    op.create_index(op.f('ix_task_output_updated_at'), 'task_output', ['updated_at'], unique=False)

    op.create_table(
        'task_output_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('task_output_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['task_output_id'], ['task_output.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_task_output_type_coding_task_output_id'), 'task_output_type_coding', ['task_output_id'], unique=False)
    op.create_index(op.f('ix_task_output_type_coding_tenant_id'), 'task_output_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_task_output_type_coding_created_at'), 'task_output_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_task_output_type_coding_updated_at'), 'task_output_type_coding', ['updated_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_table('task_output_type_coding')
    op.drop_table('task_output')
    op.drop_table('task_input_type_coding')
    op.drop_table('task_input')
    op.drop_table('task_note')
    op.drop_table('task_restriction_recipient')
    op.drop_table('task_relevant_history')
    op.drop_table('task_insurance')
    op.drop_table('task_part_of')
    op.drop_table('task_based_on')
    op.drop_table('task_performer_type_coding')
    op.drop_table('task_performer_type')
    op.drop_table('task_identifier_type_coding')
    op.drop_table('task_identifier')
    op.drop_table('task_reason_code_coding')
    op.drop_table('task_business_status_coding')
    op.drop_table('task_status_reason_coding')
    op.drop_table('task_code_coding')
    op.drop_table('task')

    # Drop sequence
    op.execute("DROP SEQUENCE IF EXISTS task_pub_seq")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS task_part_of_reference_type")
    op.execute("DROP TYPE IF EXISTS task_relevant_history_reference_type")
    op.execute("DROP TYPE IF EXISTS task_insurance_reference_type")
    op.execute("DROP TYPE IF EXISTS task_restriction_recipient_reference_type")
    op.execute("DROP TYPE IF EXISTS task_encounter_reference_type")
    op.execute("DROP TYPE IF EXISTS task_location_reference_type")
    op.execute("DROP TYPE IF EXISTS task_owner_reference_type")
    op.execute("DROP TYPE IF EXISTS task_requester_reference_type")
    op.execute("DROP TYPE IF EXISTS task_priority")
    op.execute("DROP TYPE IF EXISTS task_intent")
    op.execute("DROP TYPE IF EXISTS task_status")
