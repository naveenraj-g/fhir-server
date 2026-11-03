"""add_medication_dispense_tables

Revision ID: df4782485581
Revises: 66175c58bcea
Create Date: 2026-11-03 13:34:19.878018

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'df4782485581'
down_revision: Union[str, None] = '66175c58bcea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enums
    op.execute('''
        DO $$ BEGIN
            CREATE TYPE medication_dispense_status AS ENUM (
                'preparation', 'in-progress', 'cancelled', 'on-hold', 'completed', 'entered-in-error', 'stopped', 'declined', 'unknown'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    ''')
    op.execute('''
        DO $$ BEGIN
            CREATE TYPE medication_dispense_part_of_reference_type AS ENUM (
                'Procedure'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    ''')
    op.execute('''
        DO $$ BEGIN
            CREATE TYPE medication_dispense_status_reason_reference_type AS ENUM (
                'DetectedIssue'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    ''')
    op.execute('''
        DO $$ BEGIN
            CREATE TYPE medication_dispense_medication_reference_type AS ENUM (
                'Medication'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    ''')
    op.execute('''
        DO $$ BEGIN
            CREATE TYPE medication_dispense_subject_reference_type AS ENUM (
                'Patient', 'Group'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    ''')
    op.execute('''
        DO $$ BEGIN
            CREATE TYPE medication_dispense_context_reference_type AS ENUM (
                'Encounter', 'EpisodeOfCare'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    ''')
    op.execute('''
        DO $$ BEGIN
            CREATE TYPE medication_dispense_performer_actor_reference_type AS ENUM (
                'Practitioner', 'PractitionerRole', 'Organization', 'Patient', 'Device', 'RelatedPerson'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    ''')
    op.execute('''
        DO $$ BEGIN
            CREATE TYPE medication_dispense_location_reference_type AS ENUM (
                'Location'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    ''')
    op.execute('''
        DO $$ BEGIN
            CREATE TYPE medication_dispense_authorizing_prescription_reference_type AS ENUM (
                'MedicationRequest'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    ''')
    op.execute('''
        DO $$ BEGIN
            CREATE TYPE medication_dispense_destination_reference_type AS ENUM (
                'Location'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    ''')
    op.execute('''
        DO $$ BEGIN
            CREATE TYPE medication_dispense_receiver_reference_type AS ENUM (
                'Patient', 'Practitioner'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    ''')
    op.execute('''
        DO $$ BEGIN
            CREATE TYPE medication_dispense_substitution_responsible_party_reference_type AS ENUM (
                'Practitioner', 'PractitionerRole'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    ''')
    op.execute('''
        DO $$ BEGIN
            CREATE TYPE medication_dispense_detected_issue_reference_type AS ENUM (
                'DetectedIssue'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    ''')
    op.execute('''
        DO $$ BEGIN
            CREATE TYPE medication_dispense_event_history_reference_type AS ENUM (
                'Provenance'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    ''')
    op.execute('''
        DO $$ BEGIN
            CREATE TYPE medication_dispense_note_author_reference_type AS ENUM (
                'Practitioner', 'Patient', 'RelatedPerson', 'Organization'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    ''')

    # 2. Sequence
    op.execute('CREATE SEQUENCE IF NOT EXISTS medication_dispense_pub_seq START WITH 590000 INCREMENT BY 1;')
    op.create_table('medication_dispense',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_id', sa.BigInteger(), nullable=False),
    sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
    sa.Column('status', postgresql.ENUM('preparation', 'in-progress', 'cancelled', 'on-hold', 'completed', 'entered-in-error', 'stopped', 'declined', 'unknown', name='medication_dispense_status', create_type=False), nullable=False),
    sa.Column('status_reason_codeable_concept_text', sa.String(), nullable=True),
    sa.Column('status_reason_reference', sa.String(), nullable=True),
    sa.Column('status_reason_reference_type', postgresql.ENUM('DetectedIssue', name='medication_dispense_status_reason_reference_type', create_type=False), nullable=True),
    sa.Column('status_reason_reference_id', sa.BigInteger(), nullable=True),
    sa.Column('status_reason_reference_display', sa.String(), nullable=True),
    sa.Column('status_reason_reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('status_reason_reference_identifier_type_system', sa.String(), nullable=True),
    sa.Column('status_reason_reference_identifier_type_version', sa.String(), nullable=True),
    sa.Column('status_reason_reference_identifier_type_code', sa.String(), nullable=True),
    sa.Column('status_reason_reference_identifier_type_display', sa.String(), nullable=True),
    sa.Column('status_reason_reference_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('status_reason_reference_identifier_type_text', sa.String(), nullable=True),
    sa.Column('status_reason_reference_identifier_system', sa.String(), nullable=True),
    sa.Column('status_reason_reference_identifier_value', sa.String(), nullable=True),
    sa.Column('status_reason_reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status_reason_reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('category_text', sa.String(), nullable=True),
    sa.Column('medication_codeable_concept_text', sa.String(), nullable=True),
    sa.Column('medication_reference', sa.String(), nullable=True),
    sa.Column('medication_type', postgresql.ENUM('Medication', name='medication_dispense_medication_reference_type', create_type=False), nullable=True),
    sa.Column('medication_id', sa.BigInteger(), nullable=True),
    sa.Column('medication_display', sa.String(), nullable=True),
    sa.Column('medication_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('medication_identifier_type_system', sa.String(), nullable=True),
    sa.Column('medication_identifier_type_version', sa.String(), nullable=True),
    sa.Column('medication_identifier_type_code', sa.String(), nullable=True),
    sa.Column('medication_identifier_type_display', sa.String(), nullable=True),
    sa.Column('medication_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('medication_identifier_type_text', sa.String(), nullable=True),
    sa.Column('medication_identifier_system', sa.String(), nullable=True),
    sa.Column('medication_identifier_value', sa.String(), nullable=True),
    sa.Column('medication_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('medication_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('subject_reference', sa.String(), nullable=True),
    sa.Column('subject_type', postgresql.ENUM('Patient', 'Group', name='medication_dispense_subject_reference_type', create_type=False), nullable=True),
    sa.Column('subject_id', sa.BigInteger(), nullable=True),
    sa.Column('subject_display', sa.String(), nullable=True),
    sa.Column('subject_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('subject_identifier_type_system', sa.String(), nullable=True),
    sa.Column('subject_identifier_type_version', sa.String(), nullable=True),
    sa.Column('subject_identifier_type_code', sa.String(), nullable=True),
    sa.Column('subject_identifier_type_display', sa.String(), nullable=True),
    sa.Column('subject_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('subject_identifier_type_text', sa.String(), nullable=True),
    sa.Column('subject_identifier_system', sa.String(), nullable=True),
    sa.Column('subject_identifier_value', sa.String(), nullable=True),
    sa.Column('subject_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('subject_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('context_reference', sa.String(), nullable=True),
    sa.Column('context_type', postgresql.ENUM('Encounter', 'EpisodeOfCare', name='medication_dispense_context_reference_type', create_type=False), nullable=True),
    sa.Column('context_id', sa.BigInteger(), nullable=True),
    sa.Column('context_display', sa.String(), nullable=True),
    sa.Column('context_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('context_identifier_type_system', sa.String(), nullable=True),
    sa.Column('context_identifier_type_version', sa.String(), nullable=True),
    sa.Column('context_identifier_type_code', sa.String(), nullable=True),
    sa.Column('context_identifier_type_display', sa.String(), nullable=True),
    sa.Column('context_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('context_identifier_type_text', sa.String(), nullable=True),
    sa.Column('context_identifier_system', sa.String(), nullable=True),
    sa.Column('context_identifier_value', sa.String(), nullable=True),
    sa.Column('context_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('context_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('location_reference', sa.String(), nullable=True),
    sa.Column('location_type', postgresql.ENUM('Location', name='medication_dispense_location_reference_type', create_type=False), nullable=True),
    sa.Column('location_id', sa.BigInteger(), nullable=True),
    sa.Column('location_display', sa.String(), nullable=True),
    sa.Column('location_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('location_identifier_type_system', sa.String(), nullable=True),
    sa.Column('location_identifier_type_version', sa.String(), nullable=True),
    sa.Column('location_identifier_type_code', sa.String(), nullable=True),
    sa.Column('location_identifier_type_display', sa.String(), nullable=True),
    sa.Column('location_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('location_identifier_type_text', sa.String(), nullable=True),
    sa.Column('location_identifier_system', sa.String(), nullable=True),
    sa.Column('location_identifier_value', sa.String(), nullable=True),
    sa.Column('location_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('location_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('quantity_value', sa.Numeric(), nullable=True),
    sa.Column('quantity_unit', sa.String(), nullable=True),
    sa.Column('quantity_system', sa.String(), nullable=True),
    sa.Column('quantity_code', sa.String(), nullable=True),
    sa.Column('days_supply_value', sa.Numeric(), nullable=True),
    sa.Column('days_supply_unit', sa.String(), nullable=True),
    sa.Column('days_supply_system', sa.String(), nullable=True),
    sa.Column('days_supply_code', sa.String(), nullable=True),
    sa.Column('when_prepared', sa.DateTime(timezone=True), nullable=True),
    sa.Column('when_handed_over', sa.DateTime(timezone=True), nullable=True),
    sa.Column('destination_reference', sa.String(), nullable=True),
    sa.Column('destination_type', postgresql.ENUM('Location', name='medication_dispense_destination_reference_type', create_type=False), nullable=True),
    sa.Column('destination_id', sa.BigInteger(), nullable=True),
    sa.Column('destination_display', sa.String(), nullable=True),
    sa.Column('destination_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('destination_identifier_type_system', sa.String(), nullable=True),
    sa.Column('destination_identifier_type_version', sa.String(), nullable=True),
    sa.Column('destination_identifier_type_code', sa.String(), nullable=True),
    sa.Column('destination_identifier_type_display', sa.String(), nullable=True),
    sa.Column('destination_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('destination_identifier_type_text', sa.String(), nullable=True),
    sa.Column('destination_identifier_system', sa.String(), nullable=True),
    sa.Column('destination_identifier_value', sa.String(), nullable=True),
    sa.Column('destination_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('destination_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('substitution_was_substituted', sa.Boolean(), nullable=True),
    sa.Column('substitution_type_text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_context_id'), 'medication_dispense', ['context_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_created_at'), 'medication_dispense', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_destination_id'), 'medication_dispense', ['destination_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_location_id'), 'medication_dispense', ['location_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_medication_dispense_id'), 'medication_dispense', ['medication_dispense_id'], unique=True)
    op.create_index(op.f('ix_medication_dispense_medication_id'), 'medication_dispense', ['medication_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_status_reason_reference_id'), 'medication_dispense', ['status_reason_reference_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_subject_id'), 'medication_dispense', ['subject_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_tenant_id'), 'medication_dispense', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_updated_at'), 'medication_dispense', ['updated_at'], unique=False)
    op.create_table('medication_dispense_authorizing_prescription',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('MedicationRequest', name='medication_dispense_authorizing_prescription_reference_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.BigInteger(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('reference_identifier_type_system', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_version', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_code', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('reference_identifier_type_text', sa.String(), nullable=True),
    sa.Column('reference_identifier_system', sa.String(), nullable=True),
    sa.Column('reference_identifier_value', sa.String(), nullable=True),
    sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_dispense_pk'], ['medication_dispense.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_authorizing_prescription_created_at'), 'medication_dispense_authorizing_prescription', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_authorizing_prescription_medication_dispense_pk'), 'medication_dispense_authorizing_prescription', ['medication_dispense_pk'], unique=False)
    op.create_index(op.f('ix_medication_dispense_authorizing_prescription_reference_id'), 'medication_dispense_authorizing_prescription', ['reference_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_authorizing_prescription_tenant_id'), 'medication_dispense_authorizing_prescription', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_authorizing_prescription_updated_at'), 'medication_dispense_authorizing_prescription', ['updated_at'], unique=False)
    op.create_table('medication_dispense_category_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_dispense_pk'], ['medication_dispense.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_category_coding_created_at'), 'medication_dispense_category_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_category_coding_medication_dispense_pk'), 'medication_dispense_category_coding', ['medication_dispense_pk'], unique=False)
    op.create_index(op.f('ix_medication_dispense_category_coding_tenant_id'), 'medication_dispense_category_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_category_coding_updated_at'), 'medication_dispense_category_coding', ['updated_at'], unique=False)
    op.create_table('medication_dispense_detected_issue',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('DetectedIssue', name='medication_dispense_detected_issue_reference_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.BigInteger(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('reference_identifier_type_system', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_version', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_code', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('reference_identifier_type_text', sa.String(), nullable=True),
    sa.Column('reference_identifier_system', sa.String(), nullable=True),
    sa.Column('reference_identifier_value', sa.String(), nullable=True),
    sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_dispense_pk'], ['medication_dispense.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_detected_issue_created_at'), 'medication_dispense_detected_issue', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_detected_issue_medication_dispense_pk'), 'medication_dispense_detected_issue', ['medication_dispense_pk'], unique=False)
    op.create_index(op.f('ix_medication_dispense_detected_issue_reference_id'), 'medication_dispense_detected_issue', ['reference_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_detected_issue_tenant_id'), 'medication_dispense_detected_issue', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_detected_issue_updated_at'), 'medication_dispense_detected_issue', ['updated_at'], unique=False)
    op.create_table('medication_dispense_dosage_instruction',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_pk', sa.BigInteger(), nullable=False),
    sa.Column('sequence', sa.Integer(), nullable=True),
    sa.Column('text', sa.Text(), nullable=True),
    sa.Column('patient_instruction', sa.Text(), nullable=True),
    sa.Column('timing', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('as_needed_boolean', sa.Boolean(), nullable=True),
    sa.Column('as_needed_codeable_concept_text', sa.String(), nullable=True),
    sa.Column('site_text', sa.String(), nullable=True),
    sa.Column('route_text', sa.String(), nullable=True),
    sa.Column('method_text', sa.String(), nullable=True),
    sa.Column('dose_and_rate', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('max_dose_per_period', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('max_dose_per_administration_value', sa.Numeric(), nullable=True),
    sa.Column('max_dose_per_administration_unit', sa.String(), nullable=True),
    sa.Column('max_dose_per_administration_system', sa.String(), nullable=True),
    sa.Column('max_dose_per_administration_code', sa.String(), nullable=True),
    sa.Column('max_dose_per_lifetime_value', sa.Numeric(), nullable=True),
    sa.Column('max_dose_per_lifetime_unit', sa.String(), nullable=True),
    sa.Column('max_dose_per_lifetime_system', sa.String(), nullable=True),
    sa.Column('max_dose_per_lifetime_code', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_dispense_pk'], ['medication_dispense.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_dosage_instruction_created_at'), 'medication_dispense_dosage_instruction', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_dosage_instruction_id'), 'medication_dispense_dosage_instruction', ['id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_dosage_instruction_medication_dispense_pk'), 'medication_dispense_dosage_instruction', ['medication_dispense_pk'], unique=False)
    op.create_index(op.f('ix_medication_dispense_dosage_instruction_tenant_id'), 'medication_dispense_dosage_instruction', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_dosage_instruction_updated_at'), 'medication_dispense_dosage_instruction', ['updated_at'], unique=False)
    op.create_table('medication_dispense_event_history',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Provenance', name='medication_dispense_event_history_reference_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.BigInteger(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('reference_identifier_type_system', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_version', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_code', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('reference_identifier_type_text', sa.String(), nullable=True),
    sa.Column('reference_identifier_system', sa.String(), nullable=True),
    sa.Column('reference_identifier_value', sa.String(), nullable=True),
    sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_dispense_pk'], ['medication_dispense.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_event_history_created_at'), 'medication_dispense_event_history', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_event_history_medication_dispense_pk'), 'medication_dispense_event_history', ['medication_dispense_pk'], unique=False)
    op.create_index(op.f('ix_medication_dispense_event_history_reference_id'), 'medication_dispense_event_history', ['reference_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_event_history_tenant_id'), 'medication_dispense_event_history', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_event_history_updated_at'), 'medication_dispense_event_history', ['updated_at'], unique=False)
    op.create_table('medication_dispense_identifier',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_pk', sa.BigInteger(), nullable=False),
    sa.Column('use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('assigner_reference', sa.String(), nullable=True),
    sa.Column('assigner_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
    sa.Column('assigner_id', sa.BigInteger(), nullable=True),
    sa.Column('assigner_display', sa.String(), nullable=True),
    sa.Column('assigner_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('assigner_identifier_type_system', sa.String(), nullable=True),
    sa.Column('assigner_identifier_type_version', sa.String(), nullable=True),
    sa.Column('assigner_identifier_type_code', sa.String(), nullable=True),
    sa.Column('assigner_identifier_type_display', sa.String(), nullable=True),
    sa.Column('assigner_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('assigner_identifier_type_text', sa.String(), nullable=True),
    sa.Column('assigner_identifier_system', sa.String(), nullable=True),
    sa.Column('assigner_identifier_value', sa.String(), nullable=True),
    sa.Column('assigner_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('assigner_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_dispense_pk'], ['medication_dispense.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_identifier_assigner_id'), 'medication_dispense_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_identifier_created_at'), 'medication_dispense_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_identifier_medication_dispense_pk'), 'medication_dispense_identifier', ['medication_dispense_pk'], unique=False)
    op.create_index(op.f('ix_medication_dispense_identifier_tenant_id'), 'medication_dispense_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_identifier_updated_at'), 'medication_dispense_identifier', ['updated_at'], unique=False)
    op.create_table('medication_dispense_medication_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_dispense_pk'], ['medication_dispense.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_medication_coding_created_at'), 'medication_dispense_medication_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_medication_coding_medication_dispense_pk'), 'medication_dispense_medication_coding', ['medication_dispense_pk'], unique=False)
    op.create_index(op.f('ix_medication_dispense_medication_coding_tenant_id'), 'medication_dispense_medication_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_medication_coding_updated_at'), 'medication_dispense_medication_coding', ['updated_at'], unique=False)
    op.create_table('medication_dispense_note',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('author_string', sa.String(), nullable=True),
    sa.Column('author_reference', sa.String(), nullable=True),
    sa.Column('author_type', postgresql.ENUM('Practitioner', 'Patient', 'RelatedPerson', 'Organization', name='medication_dispense_note_author_reference_type', create_type=False), nullable=True),
    sa.Column('author_id', sa.BigInteger(), nullable=True),
    sa.Column('author_display', sa.String(), nullable=True),
    sa.Column('author_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('author_identifier_type_system', sa.String(), nullable=True),
    sa.Column('author_identifier_type_version', sa.String(), nullable=True),
    sa.Column('author_identifier_type_code', sa.String(), nullable=True),
    sa.Column('author_identifier_type_display', sa.String(), nullable=True),
    sa.Column('author_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('author_identifier_type_text', sa.String(), nullable=True),
    sa.Column('author_identifier_system', sa.String(), nullable=True),
    sa.Column('author_identifier_value', sa.String(), nullable=True),
    sa.Column('author_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('author_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_dispense_pk'], ['medication_dispense.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_note_author_id'), 'medication_dispense_note', ['author_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_note_created_at'), 'medication_dispense_note', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_note_medication_dispense_pk'), 'medication_dispense_note', ['medication_dispense_pk'], unique=False)
    op.create_index(op.f('ix_medication_dispense_note_tenant_id'), 'medication_dispense_note', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_note_updated_at'), 'medication_dispense_note', ['updated_at'], unique=False)
    op.create_table('medication_dispense_part_of',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Procedure', name='medication_dispense_part_of_reference_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.BigInteger(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('reference_identifier_type_system', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_version', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_code', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('reference_identifier_type_text', sa.String(), nullable=True),
    sa.Column('reference_identifier_system', sa.String(), nullable=True),
    sa.Column('reference_identifier_value', sa.String(), nullable=True),
    sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_dispense_pk'], ['medication_dispense.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_part_of_created_at'), 'medication_dispense_part_of', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_part_of_medication_dispense_pk'), 'medication_dispense_part_of', ['medication_dispense_pk'], unique=False)
    op.create_index(op.f('ix_medication_dispense_part_of_reference_id'), 'medication_dispense_part_of', ['reference_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_part_of_tenant_id'), 'medication_dispense_part_of', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_part_of_updated_at'), 'medication_dispense_part_of', ['updated_at'], unique=False)
    op.create_table('medication_dispense_performer',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_pk', sa.BigInteger(), nullable=False),
    sa.Column('function_text', sa.String(), nullable=True),
    sa.Column('actor_reference', sa.String(), nullable=False),
    sa.Column('actor_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization', 'Patient', 'Device', 'RelatedPerson', name='medication_dispense_performer_actor_reference_type', create_type=False), nullable=False),
    sa.Column('actor_id', sa.BigInteger(), nullable=True),
    sa.Column('actor_display', sa.String(), nullable=True),
    sa.Column('actor_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('actor_identifier_type_system', sa.String(), nullable=True),
    sa.Column('actor_identifier_type_version', sa.String(), nullable=True),
    sa.Column('actor_identifier_type_code', sa.String(), nullable=True),
    sa.Column('actor_identifier_type_display', sa.String(), nullable=True),
    sa.Column('actor_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('actor_identifier_type_text', sa.String(), nullable=True),
    sa.Column('actor_identifier_system', sa.String(), nullable=True),
    sa.Column('actor_identifier_value', sa.String(), nullable=True),
    sa.Column('actor_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('actor_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_dispense_pk'], ['medication_dispense.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_performer_actor_id'), 'medication_dispense_performer', ['actor_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_performer_created_at'), 'medication_dispense_performer', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_performer_medication_dispense_pk'), 'medication_dispense_performer', ['medication_dispense_pk'], unique=False)
    op.create_index(op.f('ix_medication_dispense_performer_tenant_id'), 'medication_dispense_performer', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_performer_updated_at'), 'medication_dispense_performer', ['updated_at'], unique=False)
    op.create_table('medication_dispense_receiver',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Patient', 'Practitioner', name='medication_dispense_receiver_reference_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.BigInteger(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('reference_identifier_type_system', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_version', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_code', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('reference_identifier_type_text', sa.String(), nullable=True),
    sa.Column('reference_identifier_system', sa.String(), nullable=True),
    sa.Column('reference_identifier_value', sa.String(), nullable=True),
    sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_dispense_pk'], ['medication_dispense.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_receiver_created_at'), 'medication_dispense_receiver', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_receiver_medication_dispense_pk'), 'medication_dispense_receiver', ['medication_dispense_pk'], unique=False)
    op.create_index(op.f('ix_medication_dispense_receiver_reference_id'), 'medication_dispense_receiver', ['reference_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_receiver_tenant_id'), 'medication_dispense_receiver', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_receiver_updated_at'), 'medication_dispense_receiver', ['updated_at'], unique=False)
    op.create_table('medication_dispense_status_reason_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_dispense_pk'], ['medication_dispense.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_status_reason_coding_created_at'), 'medication_dispense_status_reason_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_status_reason_coding_medication_dispense_pk'), 'medication_dispense_status_reason_coding', ['medication_dispense_pk'], unique=False)
    op.create_index(op.f('ix_medication_dispense_status_reason_coding_tenant_id'), 'medication_dispense_status_reason_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_status_reason_coding_updated_at'), 'medication_dispense_status_reason_coding', ['updated_at'], unique=False)
    op.create_table('medication_dispense_substitution_reason',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_dispense_pk'], ['medication_dispense.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_substitution_reason_created_at'), 'medication_dispense_substitution_reason', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_substitution_reason_medication_dispense_pk'), 'medication_dispense_substitution_reason', ['medication_dispense_pk'], unique=False)
    op.create_index(op.f('ix_medication_dispense_substitution_reason_tenant_id'), 'medication_dispense_substitution_reason', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_substitution_reason_updated_at'), 'medication_dispense_substitution_reason', ['updated_at'], unique=False)
    op.create_table('medication_dispense_substitution_responsible_party',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Practitioner', 'PractitionerRole', name='medication_dispense_substitution_responsible_party_reference_type', create_type=False), nullable=True),
    sa.Column('reference_id', sa.BigInteger(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('reference_identifier_type_system', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_version', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_code', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('reference_identifier_type_text', sa.String(), nullable=True),
    sa.Column('reference_identifier_system', sa.String(), nullable=True),
    sa.Column('reference_identifier_value', sa.String(), nullable=True),
    sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_dispense_pk'], ['medication_dispense.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_substitution_responsible_party_created_at'), 'medication_dispense_substitution_responsible_party', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_substitution_responsible_party_medication_dispense_pk'), 'medication_dispense_substitution_responsible_party', ['medication_dispense_pk'], unique=False)
    op.create_index(op.f('ix_medication_dispense_substitution_responsible_party_reference_id'), 'medication_dispense_substitution_responsible_party', ['reference_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_substitution_responsible_party_tenant_id'), 'medication_dispense_substitution_responsible_party', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_substitution_responsible_party_updated_at'), 'medication_dispense_substitution_responsible_party', ['updated_at'], unique=False)
    op.create_table('medication_dispense_substitution_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_dispense_pk'], ['medication_dispense.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_substitution_type_coding_created_at'), 'medication_dispense_substitution_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_substitution_type_coding_medication_dispense_pk'), 'medication_dispense_substitution_type_coding', ['medication_dispense_pk'], unique=False)
    op.create_index(op.f('ix_medication_dispense_substitution_type_coding_tenant_id'), 'medication_dispense_substitution_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_substitution_type_coding_updated_at'), 'medication_dispense_substitution_type_coding', ['updated_at'], unique=False)
    op.create_table('medication_dispense_supporting_info',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', sa.String(), nullable=True),
    sa.Column('reference_id', sa.BigInteger(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('reference_identifier_type_system', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_version', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_code', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('reference_identifier_type_text', sa.String(), nullable=True),
    sa.Column('reference_identifier_system', sa.String(), nullable=True),
    sa.Column('reference_identifier_value', sa.String(), nullable=True),
    sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_dispense_pk'], ['medication_dispense.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_supporting_info_created_at'), 'medication_dispense_supporting_info', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_supporting_info_medication_dispense_pk'), 'medication_dispense_supporting_info', ['medication_dispense_pk'], unique=False)
    op.create_index(op.f('ix_medication_dispense_supporting_info_reference_id'), 'medication_dispense_supporting_info', ['reference_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_supporting_info_tenant_id'), 'medication_dispense_supporting_info', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_supporting_info_updated_at'), 'medication_dispense_supporting_info', ['updated_at'], unique=False)
    op.create_table('medication_dispense_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_dispense_pk'], ['medication_dispense.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_type_coding_created_at'), 'medication_dispense_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_type_coding_medication_dispense_pk'), 'medication_dispense_type_coding', ['medication_dispense_pk'], unique=False)
    op.create_index(op.f('ix_medication_dispense_type_coding_tenant_id'), 'medication_dispense_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_type_coding_updated_at'), 'medication_dispense_type_coding', ['updated_at'], unique=False)
    op.create_table('medication_dispense_dosage_additional_instruction',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_dosage_instruction_id', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_dispense_dosage_instruction_id'], ['medication_dispense_dosage_instruction.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_dosage_additional_instruction_created_at'), 'medication_dispense_dosage_additional_instruction', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_dosage_additional_instruction_medication_dispense_dosage_instruction_id'), 'medication_dispense_dosage_additional_instruction', ['medication_dispense_dosage_instruction_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_dosage_additional_instruction_tenant_id'), 'medication_dispense_dosage_additional_instruction', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_dosage_additional_instruction_updated_at'), 'medication_dispense_dosage_additional_instruction', ['updated_at'], unique=False)
    op.create_table('medication_dispense_dosage_as_needed_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_dosage_instruction_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_dispense_dosage_instruction_id'], ['medication_dispense_dosage_instruction.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_dosage_as_needed_coding_created_at'), 'medication_dispense_dosage_as_needed_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_dosage_as_needed_coding_medication_dispense_dosage_instruction_id'), 'medication_dispense_dosage_as_needed_coding', ['medication_dispense_dosage_instruction_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_dosage_as_needed_coding_tenant_id'), 'medication_dispense_dosage_as_needed_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_dosage_as_needed_coding_updated_at'), 'medication_dispense_dosage_as_needed_coding', ['updated_at'], unique=False)
    op.create_table('medication_dispense_dosage_method_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_dosage_instruction_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_dispense_dosage_instruction_id'], ['medication_dispense_dosage_instruction.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_dosage_method_coding_created_at'), 'medication_dispense_dosage_method_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_dosage_method_coding_medication_dispense_dosage_instruction_id'), 'medication_dispense_dosage_method_coding', ['medication_dispense_dosage_instruction_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_dosage_method_coding_tenant_id'), 'medication_dispense_dosage_method_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_dosage_method_coding_updated_at'), 'medication_dispense_dosage_method_coding', ['updated_at'], unique=False)
    op.create_table('medication_dispense_dosage_route_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_dosage_instruction_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_dispense_dosage_instruction_id'], ['medication_dispense_dosage_instruction.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_dosage_route_coding_created_at'), 'medication_dispense_dosage_route_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_dosage_route_coding_medication_dispense_dosage_instruction_id'), 'medication_dispense_dosage_route_coding', ['medication_dispense_dosage_instruction_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_dosage_route_coding_tenant_id'), 'medication_dispense_dosage_route_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_dosage_route_coding_updated_at'), 'medication_dispense_dosage_route_coding', ['updated_at'], unique=False)
    op.create_table('medication_dispense_dosage_site_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_dosage_instruction_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_dispense_dosage_instruction_id'], ['medication_dispense_dosage_instruction.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_dosage_site_coding_created_at'), 'medication_dispense_dosage_site_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_dosage_site_coding_medication_dispense_dosage_instruction_id'), 'medication_dispense_dosage_site_coding', ['medication_dispense_dosage_instruction_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_dosage_site_coding_tenant_id'), 'medication_dispense_dosage_site_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_dosage_site_coding_updated_at'), 'medication_dispense_dosage_site_coding', ['updated_at'], unique=False)
    op.create_table('medication_dispense_identifier_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_identifier_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_dispense_identifier_id'], ['medication_dispense_identifier.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_identifier_type_coding_created_at'), 'medication_dispense_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_identifier_type_coding_medication_dispense_identifier_id'), 'medication_dispense_identifier_type_coding', ['medication_dispense_identifier_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_identifier_type_coding_tenant_id'), 'medication_dispense_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_identifier_type_coding_updated_at'), 'medication_dispense_identifier_type_coding', ['updated_at'], unique=False)
    op.create_table('medication_dispense_performer_function_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_performer_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_dispense_performer_id'], ['medication_dispense_performer.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_performer_function_coding_created_at'), 'medication_dispense_performer_function_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_performer_function_coding_medication_dispense_performer_id'), 'medication_dispense_performer_function_coding', ['medication_dispense_performer_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_performer_function_coding_tenant_id'), 'medication_dispense_performer_function_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_performer_function_coding_updated_at'), 'medication_dispense_performer_function_coding', ['updated_at'], unique=False)
    op.create_table('medication_dispense_substitution_reason_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_substitution_reason_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_dispense_substitution_reason_id'], ['medication_dispense_substitution_reason.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_substitution_reason_coding_created_at'), 'medication_dispense_substitution_reason_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_substitution_reason_coding_medication_dispense_substitution_reason_id'), 'medication_dispense_substitution_reason_coding', ['medication_dispense_substitution_reason_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_substitution_reason_coding_tenant_id'), 'medication_dispense_substitution_reason_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_substitution_reason_coding_updated_at'), 'medication_dispense_substitution_reason_coding', ['updated_at'], unique=False)
    op.create_table('medication_dispense_dosage_additional_instruction_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_dispense_dosage_additional_instruction_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_dispense_dosage_additional_instruction_id'], ['medication_dispense_dosage_additional_instruction.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_dispense_dosage_additional_instruction_coding_updated_at'), 'medication_dispense_dosage_additional_instruction_coding', ['updated_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_dosage_additional_instruction_coding_created_at'), 'medication_dispense_dosage_additional_instruction_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_dispense_dosage_additional_instruction_coding_medication_dispense_dosage_additional_instruction_id'), 'medication_dispense_dosage_additional_instruction_coding', ['medication_dispense_dosage_additional_instruction_id'], unique=False)
    op.create_index(op.f('ix_medication_dispense_dosage_additional_instruction_coding_tenant_id'), 'medication_dispense_dosage_additional_instruction_coding', ['tenant_id'], unique=False)


def downgrade() -> None:
    op.drop_table('medication_dispense_dosage_additional_instruction_coding')
    op.drop_table('medication_dispense_substitution_reason_coding')
    op.drop_table('medication_dispense_performer_function_coding')
    op.drop_table('medication_dispense_identifier_type_coding')
    op.drop_table('medication_dispense_dosage_site_coding')
    op.drop_table('medication_dispense_dosage_route_coding')
    op.drop_table('medication_dispense_dosage_method_coding')
    op.drop_table('medication_dispense_dosage_as_needed_coding')
    op.drop_table('medication_dispense_dosage_additional_instruction')
    op.drop_table('medication_dispense_type_coding')
    op.drop_table('medication_dispense_supporting_info')
    op.drop_table('medication_dispense_substitution_type_coding')
    op.drop_table('medication_dispense_substitution_responsible_party')
    op.drop_table('medication_dispense_substitution_reason')
    op.drop_table('medication_dispense_status_reason_coding')
    op.drop_table('medication_dispense_receiver')
    op.drop_table('medication_dispense_performer')
    op.drop_table('medication_dispense_part_of')
    op.drop_table('medication_dispense_note')
    op.drop_table('medication_dispense_medication_coding')
    op.drop_table('medication_dispense_identifier')
    op.drop_table('medication_dispense_event_history')
    op.drop_table('medication_dispense_dosage_instruction')
    op.drop_table('medication_dispense_detected_issue')
    op.drop_table('medication_dispense_category_coding')
    op.drop_table('medication_dispense_authorizing_prescription')
    op.drop_table('medication_dispense')
    op.execute('DROP SEQUENCE IF EXISTS medication_dispense_pub_seq CASCADE;')
    op.execute('DROP TYPE IF EXISTS medication_dispense_status CASCADE;')
    op.execute('DROP TYPE IF EXISTS medication_dispense_part_of_reference_type CASCADE;')
    op.execute('DROP TYPE IF EXISTS medication_dispense_status_reason_reference_type CASCADE;')
    op.execute('DROP TYPE IF EXISTS medication_dispense_medication_reference_type CASCADE;')
    op.execute('DROP TYPE IF EXISTS medication_dispense_subject_reference_type CASCADE;')
    op.execute('DROP TYPE IF EXISTS medication_dispense_context_reference_type CASCADE;')
    op.execute('DROP TYPE IF EXISTS medication_dispense_performer_actor_reference_type CASCADE;')
    op.execute('DROP TYPE IF EXISTS medication_dispense_location_reference_type CASCADE;')
    op.execute('DROP TYPE IF EXISTS medication_dispense_authorizing_prescription_reference_type CASCADE;')
    op.execute('DROP TYPE IF EXISTS medication_dispense_destination_reference_type CASCADE;')
    op.execute('DROP TYPE IF EXISTS medication_dispense_receiver_reference_type CASCADE;')
    op.execute('DROP TYPE IF EXISTS medication_dispense_substitution_responsible_party_reference_type CASCADE;')
    op.execute('DROP TYPE IF EXISTS medication_dispense_detected_issue_reference_type CASCADE;')
    op.execute('DROP TYPE IF EXISTS medication_dispense_event_history_reference_type CASCADE;')
    op.execute('DROP TYPE IF EXISTS medication_dispense_note_author_reference_type CASCADE;')
