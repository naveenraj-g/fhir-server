"""add_communication_tables

Revision ID: cd0541a6d680
Revises: 854f4aa80bf2
Create Date: 2026-11-01 08:55:43.000404

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'cd0541a6d680'
down_revision: Union[str, None] = '854f4aa80bf2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Create Enum Types ───────────────────────────────────────────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE communication_status AS ENUM (
                'preparation', 'in-progress', 'not-done', 'on-hold', 'stopped', 'completed', 'entered-in-error', 'unknown'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE communication_priority AS ENUM ('routine', 'urgent', 'asap', 'stat');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE communication_subject_reference_type AS ENUM ('Patient', 'Group');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE communication_encounter_reference_type AS ENUM ('Encounter');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE communication_sender_reference_type AS ENUM (
                'Device', 'Organization', 'Patient', 'Practitioner', 'PractitionerRole',
                'RelatedPerson', 'HealthcareService'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE communication_recipient_reference_type AS ENUM (
                'Device', 'Organization', 'Patient', 'Practitioner', 'PractitionerRole',
                'RelatedPerson', 'Group', 'CareTeam', 'HealthcareService'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE communication_in_response_to_reference_type AS ENUM ('Communication');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE communication_reason_reference_type AS ENUM (
                'Condition', 'Observation', 'DiagnosticReport', 'DocumentReference'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # ── 2. Create Public ID Sequence ───────────────────────────────────────────
    op.execute("CREATE SEQUENCE IF NOT EXISTS communication_pub_seq START WITH 480000 INCREMENT BY 1")

    # ── 3. Main Communication Table ────────────────────────────────────────────
    op.create_table(
        'communication',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_id', sa.BigInteger(), nullable=False),
        sa.Column('instantiates_canonical', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('instantiates_uri', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('status', postgresql.ENUM('preparation', 'in-progress', 'not-done', 'on-hold', 'stopped', 'completed', 'entered-in-error', 'unknown', name='communication_status', create_type=False), nullable=False),
        sa.Column('status_reason_text', sa.String(), nullable=True),
        sa.Column('priority', postgresql.ENUM('routine', 'urgent', 'asap', 'stat', name='communication_priority', create_type=False), nullable=True),
        sa.Column('subject_reference', sa.String(), nullable=True),
        sa.Column('subject_type', postgresql.ENUM('Patient', 'Group', name='communication_subject_reference_type', create_type=False), nullable=True),
        sa.Column('subject_id', sa.BigInteger(), nullable=True),
        sa.Column('subject_display', sa.String(), nullable=True),
        sa.Column('topic_text', sa.String(), nullable=True),
        sa.Column('encounter_reference', sa.String(), nullable=True),
        sa.Column('encounter_type', postgresql.ENUM('Encounter', name='communication_encounter_reference_type', create_type=False), nullable=True),
        sa.Column('encounter_id', sa.BigInteger(), nullable=True),
        sa.Column('encounter_display', sa.String(), nullable=True),
        sa.Column('sent', sa.DateTime(timezone=True), nullable=True),
        sa.Column('received', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sender_reference', sa.String(), nullable=True),
        sa.Column('sender_type', postgresql.ENUM('Device', 'Organization', 'Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', 'HealthcareService', name='communication_sender_reference_type', create_type=False), nullable=True),
        sa.Column('sender_id', sa.BigInteger(), nullable=True),
        sa.Column('sender_display', sa.String(), nullable=True),
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('communication_id')
    )
    op.create_index(op.f('ix_communication_communication_id'), 'communication', ['communication_id'], unique=True)
    op.create_index(op.f('ix_communication_subject_id'), 'communication', ['subject_id'], unique=False)
    op.create_index(op.f('ix_communication_encounter_id'), 'communication', ['encounter_id'], unique=False)
    op.create_index(op.f('ix_communication_sender_id'), 'communication', ['sender_id'], unique=False)
    op.create_index(op.f('ix_communication_tenant_id'), 'communication', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_created_at'), 'communication', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_updated_at'), 'communication', ['updated_at'], unique=False)

    # ── 4. Sibling Tables ──────────────────────────────────────────────────────
    # communication_identifier
    op.create_table(
        'communication_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_pk', sa.BigInteger(), nullable=False),
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
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['communication_pk'], ['communication.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_identifier_communication_pk'), 'communication_identifier', ['communication_pk'], unique=False)
    op.create_index(op.f('ix_communication_identifier_assigner_id'), 'communication_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_communication_identifier_tenant_id'), 'communication_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_identifier_created_at'), 'communication_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_identifier_updated_at'), 'communication_identifier', ['updated_at'], unique=False)

    # communication_identifier_type_coding
    op.create_table(
        'communication_identifier_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_identifier_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['communication_identifier_id'], ['communication_identifier.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_identifier_type_coding_communication_identifier_id'), 'communication_identifier_type_coding', ['communication_identifier_id'], unique=False)
    op.create_index(op.f('ix_communication_identifier_type_coding_tenant_id'), 'communication_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_identifier_type_coding_created_at'), 'communication_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_identifier_type_coding_updated_at'), 'communication_identifier_type_coding', ['updated_at'], unique=False)

    # communication_category
    op.create_table(
        'communication_category',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['communication_pk'], ['communication.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_category_communication_pk'), 'communication_category', ['communication_pk'], unique=False)
    op.create_index(op.f('ix_communication_category_tenant_id'), 'communication_category', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_category_created_at'), 'communication_category', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_category_updated_at'), 'communication_category', ['updated_at'], unique=False)

    # communication_category_coding
    op.create_table(
        'communication_category_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_category_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['communication_category_id'], ['communication_category.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_category_coding_communication_category_id'), 'communication_category_coding', ['communication_category_id'], unique=False)
    op.create_index(op.f('ix_communication_category_coding_tenant_id'), 'communication_category_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_category_coding_created_at'), 'communication_category_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_category_coding_updated_at'), 'communication_category_coding', ['updated_at'], unique=False)

    # communication_medium
    op.create_table(
        'communication_medium',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['communication_pk'], ['communication.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_medium_communication_pk'), 'communication_medium', ['communication_pk'], unique=False)
    op.create_index(op.f('ix_communication_medium_tenant_id'), 'communication_medium', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_medium_created_at'), 'communication_medium', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_medium_updated_at'), 'communication_medium', ['updated_at'], unique=False)

    # communication_medium_coding
    op.create_table(
        'communication_medium_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_medium_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['communication_medium_id'], ['communication_medium.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_medium_coding_communication_medium_id'), 'communication_medium_coding', ['communication_medium_id'], unique=False)
    op.create_index(op.f('ix_communication_medium_coding_tenant_id'), 'communication_medium_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_medium_coding_created_at'), 'communication_medium_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_medium_coding_updated_at'), 'communication_medium_coding', ['updated_at'], unique=False)

    # communication_status_reason_coding
    op.create_table(
        'communication_status_reason_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['communication_pk'], ['communication.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_status_reason_coding_communication_pk'), 'communication_status_reason_coding', ['communication_pk'], unique=False)
    op.create_index(op.f('ix_communication_status_reason_coding_tenant_id'), 'communication_status_reason_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_status_reason_coding_created_at'), 'communication_status_reason_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_status_reason_coding_updated_at'), 'communication_status_reason_coding', ['updated_at'], unique=False)

    # communication_topic_coding
    op.create_table(
        'communication_topic_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['communication_pk'], ['communication.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_topic_coding_communication_pk'), 'communication_topic_coding', ['communication_pk'], unique=False)
    op.create_index(op.f('ix_communication_topic_coding_tenant_id'), 'communication_topic_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_topic_coding_created_at'), 'communication_topic_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_topic_coding_updated_at'), 'communication_topic_coding', ['updated_at'], unique=False)

    # communication_based_on
    op.create_table(
        'communication_based_on',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['communication_pk'], ['communication.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_based_on_communication_pk'), 'communication_based_on', ['communication_pk'], unique=False)
    op.create_index(op.f('ix_communication_based_on_reference_id'), 'communication_based_on', ['reference_id'], unique=False)
    op.create_index(op.f('ix_communication_based_on_tenant_id'), 'communication_based_on', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_based_on_created_at'), 'communication_based_on', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_based_on_updated_at'), 'communication_based_on', ['updated_at'], unique=False)

    # communication_part_of
    op.create_table(
        'communication_part_of',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['communication_pk'], ['communication.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_part_of_communication_pk'), 'communication_part_of', ['communication_pk'], unique=False)
    op.create_index(op.f('ix_communication_part_of_reference_id'), 'communication_part_of', ['reference_id'], unique=False)
    op.create_index(op.f('ix_communication_part_of_tenant_id'), 'communication_part_of', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_part_of_created_at'), 'communication_part_of', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_part_of_updated_at'), 'communication_part_of', ['updated_at'], unique=False)

    # communication_in_response_to
    op.create_table(
        'communication_in_response_to',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Communication', name='communication_in_response_to_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['communication_pk'], ['communication.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_in_response_to_communication_pk'), 'communication_in_response_to', ['communication_pk'], unique=False)
    op.create_index(op.f('ix_communication_in_response_to_reference_id'), 'communication_in_response_to', ['reference_id'], unique=False)
    op.create_index(op.f('ix_communication_in_response_to_tenant_id'), 'communication_in_response_to', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_in_response_to_created_at'), 'communication_in_response_to', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_in_response_to_updated_at'), 'communication_in_response_to', ['updated_at'], unique=False)

    # communication_about
    op.create_table(
        'communication_about',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['communication_pk'], ['communication.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_about_communication_pk'), 'communication_about', ['communication_pk'], unique=False)
    op.create_index(op.f('ix_communication_about_reference_id'), 'communication_about', ['reference_id'], unique=False)
    op.create_index(op.f('ix_communication_about_tenant_id'), 'communication_about', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_about_created_at'), 'communication_about', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_about_updated_at'), 'communication_about', ['updated_at'], unique=False)

    # communication_recipient
    op.create_table(
        'communication_recipient',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Device', 'Organization', 'Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', 'Group', 'CareTeam', 'HealthcareService', name='communication_recipient_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['communication_pk'], ['communication.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_recipient_communication_pk'), 'communication_recipient', ['communication_pk'], unique=False)
    op.create_index(op.f('ix_communication_recipient_reference_id'), 'communication_recipient', ['reference_id'], unique=False)
    op.create_index(op.f('ix_communication_recipient_tenant_id'), 'communication_recipient', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_recipient_created_at'), 'communication_recipient', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_recipient_updated_at'), 'communication_recipient', ['updated_at'], unique=False)

    # communication_reason_reference
    op.create_table(
        'communication_reason_reference',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Condition', 'Observation', 'DiagnosticReport', 'DocumentReference', name='communication_reason_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['communication_pk'], ['communication.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_reason_reference_communication_pk'), 'communication_reason_reference', ['communication_pk'], unique=False)
    op.create_index(op.f('ix_communication_reason_reference_reference_id'), 'communication_reason_reference', ['reference_id'], unique=False)
    op.create_index(op.f('ix_communication_reason_reference_tenant_id'), 'communication_reason_reference', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_reason_reference_created_at'), 'communication_reason_reference', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_reason_reference_updated_at'), 'communication_reason_reference', ['updated_at'], unique=False)

    # communication_payload
    op.create_table(
        'communication_payload',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_pk', sa.BigInteger(), nullable=False),
        sa.Column('content_string', sa.Text(), nullable=True),
        sa.Column('content_reference_reference', sa.String(), nullable=True),
        sa.Column('content_reference_type', sa.String(), nullable=True),
        sa.Column('content_reference_id', sa.BigInteger(), nullable=True),
        sa.Column('content_reference_display', sa.String(), nullable=True),
        sa.Column('content_attachment_content_type', sa.String(), nullable=True),
        sa.Column('content_attachment_language', sa.String(), nullable=True),
        sa.Column('content_attachment_data', sa.Text(), nullable=True),
        sa.Column('content_attachment_url', sa.String(), nullable=True),
        sa.Column('content_attachment_size', sa.Integer(), nullable=True),
        sa.Column('content_attachment_hash', sa.String(), nullable=True),
        sa.Column('content_attachment_title', sa.String(), nullable=True),
        sa.Column('content_attachment_creation', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['communication_pk'], ['communication.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_payload_communication_pk'), 'communication_payload', ['communication_pk'], unique=False)
    op.create_index(op.f('ix_communication_payload_content_reference_id'), 'communication_payload', ['content_reference_id'], unique=False)
    op.create_index(op.f('ix_communication_payload_tenant_id'), 'communication_payload', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_payload_created_at'), 'communication_payload', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_payload_updated_at'), 'communication_payload', ['updated_at'], unique=False)

    # communication_note
    op.create_table(
        'communication_note',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_pk', sa.BigInteger(), nullable=False),
        sa.Column('author_string', sa.String(), nullable=True),
        sa.Column('author_reference', sa.String(), nullable=True),
        sa.Column('author_type', sa.String(), nullable=True),
        sa.Column('author_id', sa.BigInteger(), nullable=True),
        sa.Column('author_display', sa.String(), nullable=True),
        sa.Column('time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['communication_pk'], ['communication.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_note_communication_pk'), 'communication_note', ['communication_pk'], unique=False)
    op.create_index(op.f('ix_communication_note_author_id'), 'communication_note', ['author_id'], unique=False)
    op.create_index(op.f('ix_communication_note_tenant_id'), 'communication_note', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_note_created_at'), 'communication_note', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_note_updated_at'), 'communication_note', ['updated_at'], unique=False)

    # communication_reason_code
    op.create_table(
        'communication_reason_code',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['communication_pk'], ['communication.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_reason_code_communication_pk'), 'communication_reason_code', ['communication_pk'], unique=False)
    op.create_index(op.f('ix_communication_reason_code_tenant_id'), 'communication_reason_code', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_reason_code_created_at'), 'communication_reason_code', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_reason_code_updated_at'), 'communication_reason_code', ['updated_at'], unique=False)

    # communication_reason_code_coding
    op.create_table(
        'communication_reason_code_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_reason_code_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.BigInteger(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['communication_reason_code_id'], ['communication_reason_code.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_reason_code_coding_communication_reason_code_id'), 'communication_reason_code_coding', ['communication_reason_code_id'], unique=False)
    op.create_index(op.f('ix_communication_reason_code_coding_tenant_id'), 'communication_reason_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_reason_code_coding_created_at'), 'communication_reason_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_reason_code_coding_updated_at'), 'communication_reason_code_coding', ['updated_at'], unique=False)


def downgrade() -> None:
    # ── 1. Drop Grandchild Tables ──────────────────────────────────────────────
    op.drop_table('communication_reason_code_coding')
    op.drop_table('communication_medium_coding')
    op.drop_table('communication_category_coding')
    op.drop_table('communication_identifier_type_coding')

    # ── 2. Drop Sibling Tables ─────────────────────────────────────────────────
    op.drop_table('communication_reason_code')
    op.drop_table('communication_medium')
    op.drop_table('communication_category')
    op.drop_table('communication_identifier')
    op.drop_table('communication_payload')
    op.drop_table('communication_note')
    op.drop_table('communication_reason_reference')
    op.drop_table('communication_recipient')
    op.drop_table('communication_in_response_to')
    op.drop_table('communication_part_of')
    op.drop_table('communication_based_on')
    op.drop_table('communication_about')
    op.drop_table('communication_topic_coding')
    op.drop_table('communication_status_reason_coding')

    # ── 3. Drop Main Table ─────────────────────────────────────────────────────
    op.drop_table('communication')

    # ── 4. Drop Public ID Sequence ─────────────────────────────────────────────
    op.execute("DROP SEQUENCE IF EXISTS communication_pub_seq")

    # ── 5. Drop Enum Types ─────────────────────────────────────────────────────
    op.execute("DROP TYPE IF EXISTS communication_reason_reference_type")
    op.execute("DROP TYPE IF EXISTS communication_in_response_to_reference_type")
    op.execute("DROP TYPE IF EXISTS communication_recipient_reference_type")
    op.execute("DROP TYPE IF EXISTS communication_sender_reference_type")
    op.execute("DROP TYPE IF EXISTS communication_encounter_reference_type")
    op.execute("DROP TYPE IF EXISTS communication_subject_reference_type")
    op.execute("DROP TYPE IF EXISTS communication_priority")
    op.execute("DROP TYPE IF EXISTS communication_status")
