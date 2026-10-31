"""add_communication_request_tables

Revision ID: 854f4aa80bf2
Revises: d30d75880506
Create Date: 2026-10-31 18:10:33.088962

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '854f4aa80bf2'
down_revision: Union[str, None] = 'd30d75880506'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Create Enum Types ───────────────────────────────────────────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE communication_request_status AS ENUM (
                'draft', 'active', 'on-hold', 'revoked', 'completed', 'entered-in-error', 'unknown'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE communication_request_priority AS ENUM ('routine', 'urgent', 'asap', 'stat');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE communication_request_subject_reference_type AS ENUM ('Patient', 'Group');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE communication_request_encounter_reference_type AS ENUM ('Encounter');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE communication_request_requester_reference_type AS ENUM (
                'Practitioner', 'PractitionerRole', 'Organization', 'Patient', 'RelatedPerson', 'Device'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE communication_request_recipient_reference_type AS ENUM (
                'Device', 'Organization', 'Patient', 'Practitioner', 'PractitionerRole',
                'RelatedPerson', 'Group', 'CareTeam', 'HealthcareService'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE communication_request_sender_reference_type AS ENUM (
                'Device', 'Organization', 'Patient', 'Practitioner', 'PractitionerRole',
                'RelatedPerson', 'HealthcareService'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE communication_request_reason_reference_type AS ENUM (
                'Condition', 'Observation', 'DiagnosticReport', 'DocumentReference'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # ── 2. Create Public ID Sequence ───────────────────────────────────────────
    op.execute("CREATE SEQUENCE IF NOT EXISTS communication_request_pub_seq START WITH 470000 INCREMENT BY 1")

    # ── 3. Main CommunicationRequest Table ─────────────────────────────────────
    op.create_table(
        'communication_request',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_request_id', sa.BigInteger(), nullable=False),
        sa.Column('group_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('group_identifier_system', sa.String(), nullable=True),
        sa.Column('group_identifier_value', sa.String(), nullable=True),
        sa.Column('group_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('group_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('group_identifier_assigner_reference', sa.String(), nullable=True),
        sa.Column('group_identifier_assigner_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
        sa.Column('group_identifier_assigner_id', sa.BigInteger(), nullable=True),
        sa.Column('group_identifier_assigner_display', sa.String(), nullable=True),
        sa.Column('status', postgresql.ENUM('draft', 'active', 'on-hold', 'revoked', 'completed', 'entered-in-error', 'unknown', name='communication_request_status', create_type=False), nullable=False),
        sa.Column('status_reason_text', sa.String(), nullable=True),
        sa.Column('priority', postgresql.ENUM('routine', 'urgent', 'asap', 'stat', name='communication_request_priority', create_type=False), nullable=True),
        sa.Column('do_not_perform', sa.Boolean(), nullable=True),
        sa.Column('subject_reference', sa.String(), nullable=True),
        sa.Column('subject_type', postgresql.ENUM('Patient', 'Group', name='communication_request_subject_reference_type', create_type=False), nullable=True),
        sa.Column('subject_id', sa.BigInteger(), nullable=True),
        sa.Column('subject_display', sa.String(), nullable=True),
        sa.Column('encounter_reference', sa.String(), nullable=True),
        sa.Column('encounter_type', postgresql.ENUM('Encounter', name='communication_request_encounter_reference_type', create_type=False), nullable=True),
        sa.Column('encounter_id', sa.BigInteger(), nullable=True),
        sa.Column('encounter_display', sa.String(), nullable=True),
        sa.Column('occurrence_date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('occurrence_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('occurrence_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('authored_on', sa.DateTime(timezone=True), nullable=True),
        sa.Column('requester_reference', sa.String(), nullable=True),
        sa.Column('requester_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization', 'Patient', 'RelatedPerson', 'Device', name='communication_request_requester_reference_type', create_type=False), nullable=True),
        sa.Column('requester_id', sa.BigInteger(), nullable=True),
        sa.Column('requester_display', sa.String(), nullable=True),
        sa.Column('sender_reference', sa.String(), nullable=True),
        sa.Column('sender_type', postgresql.ENUM('Device', 'Organization', 'Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', 'HealthcareService', name='communication_request_sender_reference_type', create_type=False), nullable=True),
        sa.Column('sender_id', sa.BigInteger(), nullable=True),
        sa.Column('sender_display', sa.String(), nullable=True),
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_request_communication_request_id'), 'communication_request', ['communication_request_id'], unique=True)
    op.create_index(op.f('ix_communication_request_tenant_id'), 'communication_request', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_request_created_at'), 'communication_request', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_request_updated_at'), 'communication_request', ['updated_at'], unique=False)
    op.create_index(op.f('ix_communication_request_group_identifier_assigner_id'), 'communication_request', ['group_identifier_assigner_id'], unique=False)
    op.create_index(op.f('ix_communication_request_subject_id'), 'communication_request', ['subject_id'], unique=False)
    op.create_index(op.f('ix_communication_request_encounter_id'), 'communication_request', ['encounter_id'], unique=False)
    op.create_index(op.f('ix_communication_request_requester_id'), 'communication_request', ['requester_id'], unique=False)
    op.create_index(op.f('ix_communication_request_sender_id'), 'communication_request', ['sender_id'], unique=False)

    # ── 4. Sibling Tables (Direct Children of communication_request) ────────────
    # communication_request_status_reason_coding
    op.create_table(
        'communication_request_status_reason_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_request_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['communication_request_pk'], ['communication_request.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_request_status_reason_coding_communication_request_pk'), 'communication_request_status_reason_coding', ['communication_request_pk'], unique=False)
    op.create_index(op.f('ix_communication_request_status_reason_coding_tenant_id'), 'communication_request_status_reason_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_request_status_reason_coding_created_at'), 'communication_request_status_reason_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_request_status_reason_coding_updated_at'), 'communication_request_status_reason_coding', ['updated_at'], unique=False)

    # communication_request_about
    op.create_table(
        'communication_request_about',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_request_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['communication_request_pk'], ['communication_request.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_request_about_communication_request_pk'), 'communication_request_about', ['communication_request_pk'], unique=False)
    op.create_index(op.f('ix_communication_request_about_reference_id'), 'communication_request_about', ['reference_id'], unique=False)
    op.create_index(op.f('ix_communication_request_about_tenant_id'), 'communication_request_about', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_request_about_created_at'), 'communication_request_about', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_request_about_updated_at'), 'communication_request_about', ['updated_at'], unique=False)

    # communication_request_based_on
    op.create_table(
        'communication_request_based_on',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_request_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['communication_request_pk'], ['communication_request.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_request_based_on_communication_request_pk'), 'communication_request_based_on', ['communication_request_pk'], unique=False)
    op.create_index(op.f('ix_communication_request_based_on_reference_id'), 'communication_request_based_on', ['reference_id'], unique=False)
    op.create_index(op.f('ix_communication_request_based_on_tenant_id'), 'communication_request_based_on', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_request_based_on_created_at'), 'communication_request_based_on', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_request_based_on_updated_at'), 'communication_request_based_on', ['updated_at'], unique=False)

    # communication_request_replaces
    op.create_table(
        'communication_request_replaces',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_request_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['communication_request_pk'], ['communication_request.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_request_replaces_communication_request_pk'), 'communication_request_replaces', ['communication_request_pk'], unique=False)
    op.create_index(op.f('ix_communication_request_replaces_reference_id'), 'communication_request_replaces', ['reference_id'], unique=False)
    op.create_index(op.f('ix_communication_request_replaces_tenant_id'), 'communication_request_replaces', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_request_replaces_created_at'), 'communication_request_replaces', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_request_replaces_updated_at'), 'communication_request_replaces', ['updated_at'], unique=False)

    # communication_request_recipient
    op.create_table(
        'communication_request_recipient',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_request_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Device', 'Organization', 'Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', 'Group', 'CareTeam', 'HealthcareService', name='communication_request_recipient_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['communication_request_pk'], ['communication_request.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_request_recipient_communication_request_pk'), 'communication_request_recipient', ['communication_request_pk'], unique=False)
    op.create_index(op.f('ix_communication_request_recipient_reference_id'), 'communication_request_recipient', ['reference_id'], unique=False)
    op.create_index(op.f('ix_communication_request_recipient_tenant_id'), 'communication_request_recipient', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_request_recipient_created_at'), 'communication_request_recipient', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_request_recipient_updated_at'), 'communication_request_recipient', ['updated_at'], unique=False)

    # communication_request_reason_reference
    op.create_table(
        'communication_request_reason_reference',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_request_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Condition', 'Observation', 'DiagnosticReport', 'DocumentReference', name='communication_request_reason_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['communication_request_pk'], ['communication_request.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_request_reason_reference_communication_request_pk'), 'communication_request_reason_reference', ['communication_request_pk'], unique=False)
    op.create_index(op.f('ix_communication_request_reason_reference_reference_id'), 'communication_request_reason_reference', ['reference_id'], unique=False)
    op.create_index(op.f('ix_communication_request_reason_reference_tenant_id'), 'communication_request_reason_reference', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_request_reason_reference_created_at'), 'communication_request_reason_reference', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_request_reason_reference_updated_at'), 'communication_request_reason_reference', ['updated_at'], unique=False)

    # communication_request_note
    op.create_table(
        'communication_request_note',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_request_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['communication_request_pk'], ['communication_request.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_request_note_communication_request_pk'), 'communication_request_note', ['communication_request_pk'], unique=False)
    op.create_index(op.f('ix_communication_request_note_author_id'), 'communication_request_note', ['author_id'], unique=False)
    op.create_index(op.f('ix_communication_request_note_tenant_id'), 'communication_request_note', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_request_note_created_at'), 'communication_request_note', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_request_note_updated_at'), 'communication_request_note', ['updated_at'], unique=False)

    # communication_request_payload
    op.create_table(
        'communication_request_payload',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_request_pk', sa.BigInteger(), nullable=False),
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
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['communication_request_pk'], ['communication_request.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_request_payload_communication_request_pk'), 'communication_request_payload', ['communication_request_pk'], unique=False)
    op.create_index(op.f('ix_communication_request_payload_content_reference_id'), 'communication_request_payload', ['content_reference_id'], unique=False)
    op.create_index(op.f('ix_communication_request_payload_tenant_id'), 'communication_request_payload', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_request_payload_created_at'), 'communication_request_payload', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_request_payload_updated_at'), 'communication_request_payload', ['updated_at'], unique=False)

    # communication_request_identifier
    op.create_table(
        'communication_request_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_request_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['communication_request_pk'], ['communication_request.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_request_identifier_communication_request_pk'), 'communication_request_identifier', ['communication_request_pk'], unique=False)
    op.create_index(op.f('ix_communication_request_identifier_assigner_id'), 'communication_request_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_communication_request_identifier_tenant_id'), 'communication_request_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_request_identifier_created_at'), 'communication_request_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_request_identifier_updated_at'), 'communication_request_identifier', ['updated_at'], unique=False)

    # communication_request_category
    op.create_table(
        'communication_request_category',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_request_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['communication_request_pk'], ['communication_request.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_request_category_communication_request_pk'), 'communication_request_category', ['communication_request_pk'], unique=False)
    op.create_index(op.f('ix_communication_request_category_tenant_id'), 'communication_request_category', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_request_category_created_at'), 'communication_request_category', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_request_category_updated_at'), 'communication_request_category', ['updated_at'], unique=False)

    # communication_request_medium
    op.create_table(
        'communication_request_medium',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_request_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['communication_request_pk'], ['communication_request.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_request_medium_communication_request_pk'), 'communication_request_medium', ['communication_request_pk'], unique=False)
    op.create_index(op.f('ix_communication_request_medium_tenant_id'), 'communication_request_medium', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_request_medium_created_at'), 'communication_request_medium', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_request_medium_updated_at'), 'communication_request_medium', ['updated_at'], unique=False)

    # communication_request_reason_code
    op.create_table(
        'communication_request_reason_code',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_request_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['communication_request_pk'], ['communication_request.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_request_reason_code_communication_request_pk'), 'communication_request_reason_code', ['communication_request_pk'], unique=False)
    op.create_index(op.f('ix_communication_request_reason_code_tenant_id'), 'communication_request_reason_code', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_request_reason_code_created_at'), 'communication_request_reason_code', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_request_reason_code_updated_at'), 'communication_request_reason_code', ['updated_at'], unique=False)

    # ── 5. Grandchild Coding Tables ────────────────────────────────────────────
    # communication_request_identifier_type_coding
    op.create_table(
        'communication_request_identifier_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_request_identifier_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['communication_request_identifier_id'], ['communication_request_identifier.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_request_identifier_type_coding_communication_request_identifier_id'), 'communication_request_identifier_type_coding', ['communication_request_identifier_id'], unique=False)
    op.create_index(op.f('ix_communication_request_identifier_type_coding_tenant_id'), 'communication_request_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_request_identifier_type_coding_created_at'), 'communication_request_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_request_identifier_type_coding_updated_at'), 'communication_request_identifier_type_coding', ['updated_at'], unique=False)

    # communication_request_category_coding
    op.create_table(
        'communication_request_category_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_request_category_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['communication_request_category_id'], ['communication_request_category.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_request_category_coding_communication_request_category_id'), 'communication_request_category_coding', ['communication_request_category_id'], unique=False)
    op.create_index(op.f('ix_communication_request_category_coding_tenant_id'), 'communication_request_category_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_request_category_coding_created_at'), 'communication_request_category_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_request_category_coding_updated_at'), 'communication_request_category_coding', ['updated_at'], unique=False)

    # communication_request_medium_coding
    op.create_table(
        'communication_request_medium_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_request_medium_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['communication_request_medium_id'], ['communication_request_medium.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_request_medium_coding_communication_request_medium_id'), 'communication_request_medium_coding', ['communication_request_medium_id'], unique=False)
    op.create_index(op.f('ix_communication_request_medium_coding_tenant_id'), 'communication_request_medium_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_request_medium_coding_created_at'), 'communication_request_medium_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_request_medium_coding_updated_at'), 'communication_request_medium_coding', ['updated_at'], unique=False)

    # communication_request_reason_code_coding
    op.create_table(
        'communication_request_reason_code_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('communication_request_reason_code_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['communication_request_reason_code_id'], ['communication_request_reason_code.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_request_reason_code_coding_communication_request_reason_code_id'), 'communication_request_reason_code_coding', ['communication_request_reason_code_id'], unique=False)
    op.create_index(op.f('ix_communication_request_reason_code_coding_tenant_id'), 'communication_request_reason_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_communication_request_reason_code_coding_created_at'), 'communication_request_reason_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_communication_request_reason_code_coding_updated_at'), 'communication_request_reason_code_coding', ['updated_at'], unique=False)


def downgrade() -> None:
    # ── 1. Drop Grandchild Tables ──────────────────────────────────────────────
    op.drop_table('communication_request_reason_code_coding')
    op.drop_table('communication_request_medium_coding')
    op.drop_table('communication_request_category_coding')
    op.drop_table('communication_request_identifier_type_coding')

    # ── 2. Drop Sibling Tables ─────────────────────────────────────────────────
    op.drop_table('communication_request_reason_code')
    op.drop_table('communication_request_medium')
    op.drop_table('communication_request_category')
    op.drop_table('communication_request_identifier')
    op.drop_table('communication_request_payload')
    op.drop_table('communication_request_note')
    op.drop_table('communication_request_reason_reference')
    op.drop_table('communication_request_recipient')
    op.drop_table('communication_request_replaces')
    op.drop_table('communication_request_based_on')
    op.drop_table('communication_request_about')
    op.drop_table('communication_request_status_reason_coding')

    # ── 3. Drop Main Table ─────────────────────────────────────────────────────
    op.drop_table('communication_request')

    # ── 4. Drop Public ID Sequence ─────────────────────────────────────────────
    op.execute("DROP SEQUENCE IF EXISTS communication_request_pub_seq")

    # ── 5. Drop Enum Types ─────────────────────────────────────────────────────
    op.execute("DROP TYPE IF EXISTS communication_request_reason_reference_type")
    op.execute("DROP TYPE IF EXISTS communication_request_sender_reference_type")
    op.execute("DROP TYPE IF EXISTS communication_request_recipient_reference_type")
    op.execute("DROP TYPE IF EXISTS communication_request_requester_reference_type")
    op.execute("DROP TYPE IF EXISTS communication_request_encounter_reference_type")
    op.execute("DROP TYPE IF EXISTS communication_request_subject_reference_type")
    op.execute("DROP TYPE IF EXISTS communication_request_priority")
    op.execute("DROP TYPE IF EXISTS communication_request_status")
