"""add_medication_administration_tables

Revision ID: 66175c58bcea
Revises: 9c0fd7d14661
Create Date: 2026-11-03 12:16:15.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '66175c58bcea'
down_revision: Union[str, None] = '9c0fd7d14661'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE medication_administration_status AS ENUM (
                'in-progress', 'not-done', 'on-hold', 'completed', 'entered-in-error', 'stopped', 'unknown'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE medication_administration_medication_reference_type AS ENUM (
                'Medication'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE medication_administration_subject_reference_type AS ENUM (
                'Patient', 'Group'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE medication_administration_context_reference_type AS ENUM (
                'Encounter', 'EpisodeOfCare'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE medication_administration_part_of_reference_type AS ENUM (
                'MedicationAdministration', 'Procedure'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE medication_administration_performer_actor_reference_type AS ENUM (
                'Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson', 'Device'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE medication_administration_reason_reference_type AS ENUM (
                'Condition', 'Observation', 'DiagnosticReport'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE medication_administration_request_reference_type AS ENUM (
                'MedicationRequest'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE medication_administration_device_reference_type AS ENUM (
                'Device'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE medication_administration_note_author_reference_type AS ENUM (
                'Practitioner', 'Patient', 'RelatedPerson', 'Organization'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE medication_administration_event_history_reference_type AS ENUM (
                'Provenance'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # 2. Sequence
    op.execute("CREATE SEQUENCE IF NOT EXISTS medication_administration_pub_seq START WITH 580000 INCREMENT BY 1;")

    # 3. Tables
    op.create_table('medication_administration',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_administration_id', sa.BigInteger(), server_default=sa.text("nextval('medication_administration_pub_seq')"), nullable=False),
    sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
    sa.Column('instantiates', sa.ARRAY(sa.String()), nullable=True),
    sa.Column('status', postgresql.ENUM('in-progress', 'not-done', 'on-hold', 'completed', 'entered-in-error', 'stopped', 'unknown', name='medication_administration_status', create_type=False), nullable=False),
    sa.Column('category_text', sa.String(), nullable=True),
    sa.Column('medication_codeable_concept_text', sa.String(), nullable=True),
    sa.Column('medication_reference', sa.String(), nullable=True),
    sa.Column('medication_type', postgresql.ENUM('Medication', name='medication_administration_medication_reference_type', create_type=False), nullable=True),
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
    sa.Column('subject_reference', sa.String(), nullable=False),
    sa.Column('subject_type', postgresql.ENUM('Patient', 'Group', name='medication_administration_subject_reference_type', create_type=False), nullable=False),
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
    sa.Column('context_type', postgresql.ENUM('Encounter', 'EpisodeOfCare', name='medication_administration_context_reference_type', create_type=False), nullable=True),
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
    sa.Column('effective_date_time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('effective_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('effective_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('request_reference', sa.String(), nullable=True),
    sa.Column('request_type', postgresql.ENUM('MedicationRequest', name='medication_administration_request_reference_type', create_type=False), nullable=True),
    sa.Column('request_id', sa.BigInteger(), nullable=True),
    sa.Column('request_display', sa.String(), nullable=True),
    sa.Column('request_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('request_identifier_type_system', sa.String(), nullable=True),
    sa.Column('request_identifier_type_version', sa.String(), nullable=True),
    sa.Column('request_identifier_type_code', sa.String(), nullable=True),
    sa.Column('request_identifier_type_display', sa.String(), nullable=True),
    sa.Column('request_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('request_identifier_type_text', sa.String(), nullable=True),
    sa.Column('request_identifier_system', sa.String(), nullable=True),
    sa.Column('request_identifier_value', sa.String(), nullable=True),
    sa.Column('request_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('request_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('dosage_text', sa.String(), nullable=True),
    sa.Column('dosage_site_text', sa.String(), nullable=True),
    sa.Column('dosage_route_text', sa.String(), nullable=True),
    sa.Column('dosage_method_text', sa.String(), nullable=True),
    sa.Column('dosage_dose_value', sa.Numeric(), nullable=True),
    sa.Column('dosage_dose_unit', sa.String(), nullable=True),
    sa.Column('dosage_dose_system', sa.String(), nullable=True),
    sa.Column('dosage_dose_code', sa.String(), nullable=True),
    sa.Column('dosage_rate_ratio_numerator_value', sa.Numeric(), nullable=True),
    sa.Column('dosage_rate_ratio_numerator_unit', sa.String(), nullable=True),
    sa.Column('dosage_rate_ratio_numerator_system', sa.String(), nullable=True),
    sa.Column('dosage_rate_ratio_numerator_code', sa.String(), nullable=True),
    sa.Column('dosage_rate_ratio_denominator_value', sa.Numeric(), nullable=True),
    sa.Column('dosage_rate_ratio_denominator_unit', sa.String(), nullable=True),
    sa.Column('dosage_rate_ratio_denominator_system', sa.String(), nullable=True),
    sa.Column('dosage_rate_ratio_denominator_code', sa.String(), nullable=True),
    sa.Column('dosage_rate_quantity_value', sa.Numeric(), nullable=True),
    sa.Column('dosage_rate_quantity_unit', sa.String(), nullable=True),
    sa.Column('dosage_rate_quantity_system', sa.String(), nullable=True),
    sa.Column('dosage_rate_quantity_code', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('medication_administration_category_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_administration_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_administration_pk'], ['medication_administration.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('medication_administration_device',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_administration_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Device', name='medication_administration_device_reference_type', create_type=False), nullable=True),
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
    sa.ForeignKeyConstraint(['medication_administration_pk'], ['medication_administration.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('medication_administration_dosage_method_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_administration_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_administration_pk'], ['medication_administration.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('medication_administration_dosage_route_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_administration_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_administration_pk'], ['medication_administration.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('medication_administration_dosage_site_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_administration_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_administration_pk'], ['medication_administration.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('medication_administration_event_history',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_administration_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Provenance', name='medication_administration_event_history_reference_type', create_type=False), nullable=True),
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
    sa.ForeignKeyConstraint(['medication_administration_pk'], ['medication_administration.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('medication_administration_identifier',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_administration_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_administration_pk'], ['medication_administration.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('medication_administration_medication_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_administration_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_administration_pk'], ['medication_administration.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('medication_administration_note',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_administration_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('author_string', sa.String(), nullable=True),
    sa.Column('author_reference', sa.String(), nullable=True),
    sa.Column('author_type', postgresql.ENUM('Practitioner', 'Patient', 'RelatedPerson', 'Organization', name='medication_administration_note_author_reference_type', create_type=False), nullable=True),
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
    sa.ForeignKeyConstraint(['medication_administration_pk'], ['medication_administration.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('medication_administration_part_of',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_administration_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('MedicationAdministration', 'Procedure', name='medication_administration_part_of_reference_type', create_type=False), nullable=True),
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
    sa.ForeignKeyConstraint(['medication_administration_pk'], ['medication_administration.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('medication_administration_performer',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_administration_pk', sa.BigInteger(), nullable=False),
    sa.Column('function_text', sa.String(), nullable=True),
    sa.Column('actor_reference', sa.String(), nullable=False),
    sa.Column('actor_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson', 'Device', name='medication_administration_performer_actor_reference_type', create_type=False), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_administration_pk'], ['medication_administration.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('medication_administration_reason_code',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_administration_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_administration_pk'], ['medication_administration.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('medication_administration_reason_reference',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_administration_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Condition', 'Observation', 'DiagnosticReport', name='medication_administration_reason_reference_type', create_type=False), nullable=True),
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
    sa.ForeignKeyConstraint(['medication_administration_pk'], ['medication_administration.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('medication_administration_status_reason',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_administration_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_administration_pk'], ['medication_administration.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('medication_administration_supporting_information',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_administration_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', sa.String(), nullable=True),
    sa.Column('reference_id', sa.BigInteger(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('reference_identifier_type_system', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_version', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_code', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_text', sa.String(), nullable=True),
    sa.Column('reference_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('reference_identifier_system', sa.String(), nullable=True),
    sa.Column('reference_identifier_value', sa.String(), nullable=True),
    sa.Column('reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_administration_pk'], ['medication_administration.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('medication_administration_identifier_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_administration_identifier_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_administration_identifier_id'], ['medication_administration_identifier.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('medication_administration_performer_function_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_administration_performer_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_administration_performer_id'], ['medication_administration_performer.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('medication_administration_reason_code_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_administration_reason_code_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_administration_reason_code_id'], ['medication_administration_reason_code.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('medication_administration_status_reason_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_administration_status_reason_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['medication_administration_status_reason_id'], ['medication_administration_status_reason.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    # 1. Tables (reverse FK order)
    op.drop_table('medication_administration_status_reason_coding')
    op.drop_table('medication_administration_reason_code_coding')
    op.drop_table('medication_administration_performer_function_coding')
    op.drop_table('medication_administration_identifier_type_coding')
    op.drop_table('medication_administration_supporting_information')
    op.drop_table('medication_administration_status_reason')
    op.drop_table('medication_administration_reason_reference')
    op.drop_table('medication_administration_reason_code')
    op.drop_table('medication_administration_performer')
    op.drop_table('medication_administration_part_of')
    op.drop_table('medication_administration_note')
    op.drop_table('medication_administration_medication_coding')
    op.drop_table('medication_administration_identifier')
    op.drop_table('medication_administration_event_history')
    op.drop_table('medication_administration_dosage_site_coding')
    op.drop_table('medication_administration_dosage_route_coding')
    op.drop_table('medication_administration_dosage_method_coding')
    op.drop_table('medication_administration_device')
    op.drop_table('medication_administration_category_coding')
    op.drop_table('medication_administration')

    # 2. Sequence
    op.execute("DROP SEQUENCE IF EXISTS medication_administration_pub_seq;")

    # 3. Enums
    op.execute("DROP TYPE IF EXISTS medication_administration_event_history_reference_type;")
    op.execute("DROP TYPE IF EXISTS medication_administration_note_author_reference_type;")
    op.execute("DROP TYPE IF EXISTS medication_administration_device_reference_type;")
    op.execute("DROP TYPE IF EXISTS medication_administration_request_reference_type;")
    op.execute("DROP TYPE IF EXISTS medication_administration_reason_reference_type;")
    op.execute("DROP TYPE IF EXISTS medication_administration_performer_actor_reference_type;")
    op.execute("DROP TYPE IF EXISTS medication_administration_part_of_reference_type;")
    op.execute("DROP TYPE IF EXISTS medication_administration_context_reference_type;")
    op.execute("DROP TYPE IF EXISTS medication_administration_subject_reference_type;")
    op.execute("DROP TYPE IF EXISTS medication_administration_medication_reference_type;")
    op.execute("DROP TYPE IF EXISTS medication_administration_status;")
