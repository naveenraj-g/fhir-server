"""add_immunization_tables

Revision ID: 7ae3e808c552
Revises: a5d91c782041
Create Date: 2026-11-02 19:14:00.353219

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7ae3e808c552'
down_revision: Union[str, None] = 'a5d91c782041'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE immunization_status AS ENUM ('completed', 'entered-in-error', 'not-done');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE immunization_patient_reference_type AS ENUM ('Patient');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE immunization_encounter_reference_type AS ENUM ('Encounter');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE immunization_location_reference_type AS ENUM ('Location');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE immunization_manufacturer_reference_type AS ENUM ('Organization');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE immunization_performer_actor_reference_type AS ENUM ('Practitioner', 'PractitionerRole', 'Organization');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE immunization_note_author_reference_type AS ENUM ('Practitioner', 'Patient', 'RelatedPerson', 'Organization');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE immunization_reason_reference_type AS ENUM ('Condition', 'Observation', 'DiagnosticReport');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE immunization_reaction_detail_reference_type AS ENUM ('Observation');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE immunization_protocol_applied_authority_reference_type AS ENUM ('Organization');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute("CREATE SEQUENCE IF NOT EXISTS immunization_pub_seq START WITH 330000 INCREMENT BY 1")

    # 1. Main table
    op.create_table(
        'immunization',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_id', sa.BigInteger(), server_default=sa.text("nextval('immunization_pub_seq')"), nullable=False),
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
        sa.Column('status', postgresql.ENUM('completed', 'entered-in-error', 'not-done', name='immunization_status', create_type=False), nullable=False),
        sa.Column('status_reason_text', sa.String(), nullable=True),
        sa.Column('vaccine_code_text', sa.String(), nullable=True),

        sa.Column('patient_reference', sa.String(), nullable=False),
        sa.Column('patient_type', postgresql.ENUM('Patient', name='immunization_patient_reference_type', create_type=False), nullable=False),
        sa.Column('patient_id', sa.BigInteger(), nullable=True),
        sa.Column('patient_display', sa.String(), nullable=True),
        sa.Column('patient_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('patient_identifier_type_system', sa.String(), nullable=True),
        sa.Column('patient_identifier_type_version', sa.String(), nullable=True),
        sa.Column('patient_identifier_type_code', sa.String(), nullable=True),
        sa.Column('patient_identifier_type_display', sa.String(), nullable=True),
        sa.Column('patient_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('patient_identifier_type_text', sa.String(), nullable=True),
        sa.Column('patient_identifier_system', sa.String(), nullable=True),
        sa.Column('patient_identifier_value', sa.String(), nullable=True),
        sa.Column('patient_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('patient_identifier_period_end', sa.DateTime(timezone=True), nullable=True),

        sa.Column('encounter_reference', sa.String(), nullable=True),
        sa.Column('encounter_type', postgresql.ENUM('Encounter', name='immunization_encounter_reference_type', create_type=False), nullable=True),
        sa.Column('encounter_id', sa.BigInteger(), nullable=True),
        sa.Column('encounter_display', sa.String(), nullable=True),
        sa.Column('encounter_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('encounter_identifier_type_system', sa.String(), nullable=True),
        sa.Column('encounter_identifier_type_version', sa.String(), nullable=True),
        sa.Column('encounter_identifier_type_code', sa.String(), nullable=True),
        sa.Column('encounter_identifier_type_display', sa.String(), nullable=True),
        sa.Column('encounter_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('encounter_identifier_type_text', sa.String(), nullable=True),
        sa.Column('encounter_identifier_system', sa.String(), nullable=True),
        sa.Column('encounter_identifier_value', sa.String(), nullable=True),
        sa.Column('encounter_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('encounter_identifier_period_end', sa.DateTime(timezone=True), nullable=True),

        sa.Column('occurrence_date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('occurrence_string', sa.String(), nullable=True),
        sa.Column('recorded', sa.DateTime(timezone=True), nullable=True),
        sa.Column('primary_source', sa.Boolean(), nullable=True),
        sa.Column('report_origin_text', sa.String(), nullable=True),

        sa.Column('location_reference', sa.String(), nullable=True),
        sa.Column('location_type', postgresql.ENUM('Location', name='immunization_location_reference_type', create_type=False), nullable=True),
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

        sa.Column('manufacturer_reference', sa.String(), nullable=True),
        sa.Column('manufacturer_type', postgresql.ENUM('Organization', name='immunization_manufacturer_reference_type', create_type=False), nullable=True),
        sa.Column('manufacturer_id', sa.BigInteger(), nullable=True),
        sa.Column('manufacturer_display', sa.String(), nullable=True),
        sa.Column('manufacturer_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('manufacturer_identifier_type_system', sa.String(), nullable=True),
        sa.Column('manufacturer_identifier_type_version', sa.String(), nullable=True),
        sa.Column('manufacturer_identifier_type_code', sa.String(), nullable=True),
        sa.Column('manufacturer_identifier_type_display', sa.String(), nullable=True),
        sa.Column('manufacturer_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('manufacturer_identifier_type_text', sa.String(), nullable=True),
        sa.Column('manufacturer_identifier_system', sa.String(), nullable=True),
        sa.Column('manufacturer_identifier_value', sa.String(), nullable=True),
        sa.Column('manufacturer_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('manufacturer_identifier_period_end', sa.DateTime(timezone=True), nullable=True),

        sa.Column('lot_number', sa.String(), nullable=True),
        sa.Column('expiration_date', sa.Date(), nullable=True),
        sa.Column('site_text', sa.String(), nullable=True),
        sa.Column('route_text', sa.String(), nullable=True),
        sa.Column('dose_quantity_value', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('dose_quantity_unit', sa.String(), nullable=True),
        sa.Column('dose_quantity_system', sa.String(), nullable=True),
        sa.Column('dose_quantity_code', sa.String(), nullable=True),
        sa.Column('is_subpotent', sa.Boolean(), nullable=True),
        sa.Column('funding_source_text', sa.String(), nullable=True),

        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_id'), 'immunization', ['id'], unique=False)
    op.create_index(op.f('ix_immunization_immunization_id'), 'immunization', ['immunization_id'], unique=True)
    op.create_index(op.f('ix_immunization_patient_id'), 'immunization', ['patient_id'], unique=False)
    op.create_index(op.f('ix_immunization_encounter_id'), 'immunization', ['encounter_id'], unique=False)
    op.create_index(op.f('ix_immunization_location_id'), 'immunization', ['location_id'], unique=False)
    op.create_index(op.f('ix_immunization_manufacturer_id'), 'immunization', ['manufacturer_id'], unique=False)
    op.create_index(op.f('ix_immunization_tenant_id'), 'immunization', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_created_at'), 'immunization', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_updated_at'), 'immunization', ['updated_at'], unique=False)

    # 2. identifier
    op.create_table(
        'immunization_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['immunization_pk'], ['immunization.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_identifier_immunization_pk'), 'immunization_identifier', ['immunization_pk'], unique=False)
    op.create_index(op.f('ix_immunization_identifier_assigner_id'), 'immunization_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_immunization_identifier_tenant_id'), 'immunization_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_identifier_created_at'), 'immunization_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_identifier_updated_at'), 'immunization_identifier', ['updated_at'], unique=False)

    # 3. identifier_type_coding
    op.create_table(
        'immunization_identifier_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('identifier_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['identifier_id'], ['immunization_identifier.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_identifier_type_coding_identifier_id'), 'immunization_identifier_type_coding', ['identifier_id'], unique=False)
    op.create_index(op.f('ix_immunization_identifier_type_coding_tenant_id'), 'immunization_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_identifier_type_coding_created_at'), 'immunization_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_identifier_type_coding_updated_at'), 'immunization_identifier_type_coding', ['updated_at'], unique=False)

    # 4. status_reason_coding
    op.create_table(
        'immunization_status_reason_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['immunization_pk'], ['immunization.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_status_reason_coding_immunization_pk'), 'immunization_status_reason_coding', ['immunization_pk'], unique=False)
    op.create_index(op.f('ix_immunization_status_reason_coding_tenant_id'), 'immunization_status_reason_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_status_reason_coding_created_at'), 'immunization_status_reason_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_status_reason_coding_updated_at'), 'immunization_status_reason_coding', ['updated_at'], unique=False)

    # 5. vaccine_coding
    op.create_table(
        'immunization_vaccine_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['immunization_pk'], ['immunization.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_vaccine_coding_immunization_pk'), 'immunization_vaccine_coding', ['immunization_pk'], unique=False)
    op.create_index(op.f('ix_immunization_vaccine_coding_tenant_id'), 'immunization_vaccine_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_vaccine_coding_created_at'), 'immunization_vaccine_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_vaccine_coding_updated_at'), 'immunization_vaccine_coding', ['updated_at'], unique=False)

    # 6. report_origin_coding
    op.create_table(
        'immunization_report_origin_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['immunization_pk'], ['immunization.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_report_origin_coding_immunization_pk'), 'immunization_report_origin_coding', ['immunization_pk'], unique=False)
    op.create_index(op.f('ix_immunization_report_origin_coding_tenant_id'), 'immunization_report_origin_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_report_origin_coding_created_at'), 'immunization_report_origin_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_report_origin_coding_updated_at'), 'immunization_report_origin_coding', ['updated_at'], unique=False)

    # 7. site_coding
    op.create_table(
        'immunization_site_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['immunization_pk'], ['immunization.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_site_coding_immunization_pk'), 'immunization_site_coding', ['immunization_pk'], unique=False)
    op.create_index(op.f('ix_immunization_site_coding_tenant_id'), 'immunization_site_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_site_coding_created_at'), 'immunization_site_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_site_coding_updated_at'), 'immunization_site_coding', ['updated_at'], unique=False)

    # 8. route_coding
    op.create_table(
        'immunization_route_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['immunization_pk'], ['immunization.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_route_coding_immunization_pk'), 'immunization_route_coding', ['immunization_pk'], unique=False)
    op.create_index(op.f('ix_immunization_route_coding_tenant_id'), 'immunization_route_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_route_coding_created_at'), 'immunization_route_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_route_coding_updated_at'), 'immunization_route_coding', ['updated_at'], unique=False)

    # 9. funding_source_coding
    op.create_table(
        'immunization_funding_source_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['immunization_pk'], ['immunization.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_funding_source_coding_immunization_pk'), 'immunization_funding_source_coding', ['immunization_pk'], unique=False)
    op.create_index(op.f('ix_immunization_funding_source_coding_tenant_id'), 'immunization_funding_source_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_funding_source_coding_created_at'), 'immunization_funding_source_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_funding_source_coding_updated_at'), 'immunization_funding_source_coding', ['updated_at'], unique=False)

    # 10. performer
    op.create_table(
        'immunization_performer',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_pk', sa.BigInteger(), nullable=False),
        sa.Column('function_text', sa.String(), nullable=True),
        sa.Column('actor_reference', sa.String(), nullable=False),
        sa.Column('actor_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization', name='immunization_performer_actor_reference_type', create_type=False), nullable=False),
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
        sa.ForeignKeyConstraint(['immunization_pk'], ['immunization.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_performer_immunization_pk'), 'immunization_performer', ['immunization_pk'], unique=False)
    op.create_index(op.f('ix_immunization_performer_actor_id'), 'immunization_performer', ['actor_id'], unique=False)
    op.create_index(op.f('ix_immunization_performer_tenant_id'), 'immunization_performer', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_performer_created_at'), 'immunization_performer', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_performer_updated_at'), 'immunization_performer', ['updated_at'], unique=False)

    # 11. performer_function_coding
    op.create_table(
        'immunization_performer_function_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('performer_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['performer_id'], ['immunization_performer.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_performer_function_coding_performer_id'), 'immunization_performer_function_coding', ['performer_id'], unique=False)
    op.create_index(op.f('ix_immunization_performer_function_coding_tenant_id'), 'immunization_performer_function_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_performer_function_coding_created_at'), 'immunization_performer_function_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_performer_function_coding_updated_at'), 'immunization_performer_function_coding', ['updated_at'], unique=False)

    # 12. note
    op.create_table(
        'immunization_note',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('author_string', sa.String(), nullable=True),
        sa.Column('author_reference', sa.String(), nullable=True),
        sa.Column('author_type', postgresql.ENUM('Practitioner', 'Patient', 'RelatedPerson', 'Organization', name='immunization_note_author_reference_type', create_type=False), nullable=True),
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
        sa.ForeignKeyConstraint(['immunization_pk'], ['immunization.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_note_immunization_pk'), 'immunization_note', ['immunization_pk'], unique=False)
    op.create_index(op.f('ix_immunization_note_author_id'), 'immunization_note', ['author_id'], unique=False)
    op.create_index(op.f('ix_immunization_note_tenant_id'), 'immunization_note', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_note_created_at'), 'immunization_note', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_note_updated_at'), 'immunization_note', ['updated_at'], unique=False)

    # 13. reason_code
    op.create_table(
        'immunization_reason_code',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['immunization_pk'], ['immunization.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_reason_code_immunization_pk'), 'immunization_reason_code', ['immunization_pk'], unique=False)
    op.create_index(op.f('ix_immunization_reason_code_tenant_id'), 'immunization_reason_code', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_reason_code_created_at'), 'immunization_reason_code', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_reason_code_updated_at'), 'immunization_reason_code', ['updated_at'], unique=False)

    # 14. reason_code_coding
    op.create_table(
        'immunization_reason_code_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('reason_code_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['reason_code_id'], ['immunization_reason_code.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_reason_code_coding_reason_code_id'), 'immunization_reason_code_coding', ['reason_code_id'], unique=False)
    op.create_index(op.f('ix_immunization_reason_code_coding_tenant_id'), 'immunization_reason_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_reason_code_coding_created_at'), 'immunization_reason_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_reason_code_coding_updated_at'), 'immunization_reason_code_coding', ['updated_at'], unique=False)

    # 15. reason_reference
    op.create_table(
        'immunization_reason_reference',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Condition', 'Observation', 'DiagnosticReport', name='immunization_reason_reference_type', create_type=False), nullable=True),
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
        sa.ForeignKeyConstraint(['immunization_pk'], ['immunization.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_reason_reference_immunization_pk'), 'immunization_reason_reference', ['immunization_pk'], unique=False)
    op.create_index(op.f('ix_immunization_reason_reference_reference_id'), 'immunization_reason_reference', ['reference_id'], unique=False)
    op.create_index(op.f('ix_immunization_reason_reference_tenant_id'), 'immunization_reason_reference', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_reason_reference_created_at'), 'immunization_reason_reference', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_reason_reference_updated_at'), 'immunization_reason_reference', ['updated_at'], unique=False)

    # 16. subpotent_reason
    op.create_table(
        'immunization_subpotent_reason',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['immunization_pk'], ['immunization.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_subpotent_reason_immunization_pk'), 'immunization_subpotent_reason', ['immunization_pk'], unique=False)
    op.create_index(op.f('ix_immunization_subpotent_reason_tenant_id'), 'immunization_subpotent_reason', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_subpotent_reason_created_at'), 'immunization_subpotent_reason', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_subpotent_reason_updated_at'), 'immunization_subpotent_reason', ['updated_at'], unique=False)

    # 17. subpotent_reason_coding
    op.create_table(
        'immunization_subpotent_reason_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('subpotent_reason_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['subpotent_reason_id'], ['immunization_subpotent_reason.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_subpotent_reason_coding_subpotent_reason_id'), 'immunization_subpotent_reason_coding', ['subpotent_reason_id'], unique=False)
    op.create_index(op.f('ix_immunization_subpotent_reason_coding_tenant_id'), 'immunization_subpotent_reason_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_subpotent_reason_coding_created_at'), 'immunization_subpotent_reason_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_subpotent_reason_coding_updated_at'), 'immunization_subpotent_reason_coding', ['updated_at'], unique=False)

    # 18. education
    op.create_table(
        'immunization_education',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_pk', sa.BigInteger(), nullable=False),
        sa.Column('document_type', sa.String(), nullable=True),
        sa.Column('reference', sa.String(), nullable=True),
        sa.Column('publication_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('presentation_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['immunization_pk'], ['immunization.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_education_immunization_pk'), 'immunization_education', ['immunization_pk'], unique=False)
    op.create_index(op.f('ix_immunization_education_tenant_id'), 'immunization_education', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_education_created_at'), 'immunization_education', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_education_updated_at'), 'immunization_education', ['updated_at'], unique=False)

    # 19. program_eligibility
    op.create_table(
        'immunization_program_eligibility',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['immunization_pk'], ['immunization.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_program_eligibility_immunization_pk'), 'immunization_program_eligibility', ['immunization_pk'], unique=False)
    op.create_index(op.f('ix_immunization_program_eligibility_tenant_id'), 'immunization_program_eligibility', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_program_eligibility_created_at'), 'immunization_program_eligibility', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_program_eligibility_updated_at'), 'immunization_program_eligibility', ['updated_at'], unique=False)

    # 20. program_eligibility_coding
    op.create_table(
        'immunization_program_eligibility_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('program_eligibility_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['program_eligibility_id'], ['immunization_program_eligibility.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_program_eligibility_coding_prog_elig_id'), 'immunization_program_eligibility_coding', ['program_eligibility_id'], unique=False)
    op.create_index(op.f('ix_immunization_program_eligibility_coding_tenant_id'), 'immunization_program_eligibility_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_program_eligibility_coding_created_at'), 'immunization_program_eligibility_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_program_eligibility_coding_updated_at'), 'immunization_program_eligibility_coding', ['updated_at'], unique=False)

    # 21. reaction
    op.create_table(
        'immunization_reaction',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_pk', sa.BigInteger(), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reported', sa.Boolean(), nullable=True),
        sa.Column('detail_reference', sa.String(), nullable=True),
        sa.Column('detail_type', postgresql.ENUM('Observation', name='immunization_reaction_detail_reference_type', create_type=False), nullable=True),
        sa.Column('detail_id', sa.BigInteger(), nullable=True),
        sa.Column('detail_display', sa.String(), nullable=True),
        sa.Column('detail_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('detail_identifier_type_system', sa.String(), nullable=True),
        sa.Column('detail_identifier_type_version', sa.String(), nullable=True),
        sa.Column('detail_identifier_type_code', sa.String(), nullable=True),
        sa.Column('detail_identifier_type_display', sa.String(), nullable=True),
        sa.Column('detail_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('detail_identifier_type_text', sa.String(), nullable=True),
        sa.Column('detail_identifier_system', sa.String(), nullable=True),
        sa.Column('detail_identifier_value', sa.String(), nullable=True),
        sa.Column('detail_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('detail_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['immunization_pk'], ['immunization.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_reaction_immunization_pk'), 'immunization_reaction', ['immunization_pk'], unique=False)
    op.create_index(op.f('ix_immunization_reaction_detail_id'), 'immunization_reaction', ['detail_id'], unique=False)
    op.create_index(op.f('ix_immunization_reaction_tenant_id'), 'immunization_reaction', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_reaction_created_at'), 'immunization_reaction', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_reaction_updated_at'), 'immunization_reaction', ['updated_at'], unique=False)

    # 22. protocol_applied
    op.create_table(
        'immunization_protocol_applied',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_pk', sa.BigInteger(), nullable=False),
        sa.Column('series', sa.String(), nullable=True),
        sa.Column('authority_reference', sa.String(), nullable=True),
        sa.Column('authority_type', postgresql.ENUM('Organization', name='immunization_protocol_applied_authority_reference_type', create_type=False), nullable=True),
        sa.Column('authority_id', sa.BigInteger(), nullable=True),
        sa.Column('authority_display', sa.String(), nullable=True),
        sa.Column('authority_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('authority_identifier_type_system', sa.String(), nullable=True),
        sa.Column('authority_identifier_type_version', sa.String(), nullable=True),
        sa.Column('authority_identifier_type_code', sa.String(), nullable=True),
        sa.Column('authority_identifier_type_display', sa.String(), nullable=True),
        sa.Column('authority_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('authority_identifier_type_text', sa.String(), nullable=True),
        sa.Column('authority_identifier_system', sa.String(), nullable=True),
        sa.Column('authority_identifier_value', sa.String(), nullable=True),
        sa.Column('authority_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('authority_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dose_number_positive_int', sa.Integer(), nullable=True),
        sa.Column('dose_number_string', sa.String(), nullable=True),
        sa.Column('series_doses_positive_int', sa.Integer(), nullable=True),
        sa.Column('series_doses_string', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['immunization_pk'], ['immunization.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_protocol_applied_immunization_pk'), 'immunization_protocol_applied', ['immunization_pk'], unique=False)
    op.create_index(op.f('ix_immunization_protocol_applied_authority_id'), 'immunization_protocol_applied', ['authority_id'], unique=False)
    op.create_index(op.f('ix_immunization_protocol_applied_tenant_id'), 'immunization_protocol_applied', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_protocol_applied_created_at'), 'immunization_protocol_applied', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_protocol_applied_updated_at'), 'immunization_protocol_applied', ['updated_at'], unique=False)

    # 23. protocol_applied_target_disease
    op.create_table(
        'immunization_protocol_applied_target_disease',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('protocol_applied_id', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['protocol_applied_id'], ['immunization_protocol_applied.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_prot_app_target_disease_prot_app_id'), 'immunization_protocol_applied_target_disease', ['protocol_applied_id'], unique=False)
    op.create_index(op.f('ix_immunization_protocol_applied_target_disease_tenant_id'), 'immunization_protocol_applied_target_disease', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_protocol_applied_target_disease_created_at'), 'immunization_protocol_applied_target_disease', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_protocol_applied_target_disease_updated_at'), 'immunization_protocol_applied_target_disease', ['updated_at'], unique=False)

    # 24. protocol_applied_target_disease_coding
    op.create_table(
        'immunization_protocol_applied_target_disease_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('target_disease_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['target_disease_id'], ['immunization_protocol_applied_target_disease.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_prot_app_target_disease_coding_tgt_dis_id'), 'immunization_protocol_applied_target_disease_coding', ['target_disease_id'], unique=False)
    op.create_index(op.f('ix_immunization_protocol_applied_target_disease_coding_tenant_id'), 'immunization_protocol_applied_target_disease_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_protocol_applied_target_disease_coding_created_at'), 'immunization_protocol_applied_target_disease_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_protocol_applied_target_disease_coding_updated_at'), 'immunization_protocol_applied_target_disease_coding', ['updated_at'], unique=False)


def downgrade() -> None:
    op.drop_table('immunization_protocol_applied_target_disease_coding')
    op.drop_table('immunization_protocol_applied_target_disease')
    op.drop_table('immunization_protocol_applied')
    op.drop_table('immunization_reaction')
    op.drop_table('immunization_program_eligibility_coding')
    op.drop_table('immunization_program_eligibility')
    op.drop_table('immunization_education')
    op.drop_table('immunization_subpotent_reason_coding')
    op.drop_table('immunization_subpotent_reason')
    op.drop_table('immunization_reason_reference')
    op.drop_table('immunization_reason_code_coding')
    op.drop_table('immunization_reason_code')
    op.drop_table('immunization_note')
    op.drop_table('immunization_performer_function_coding')
    op.drop_table('immunization_performer')
    op.drop_table('immunization_funding_source_coding')
    op.drop_table('immunization_route_coding')
    op.drop_table('immunization_site_coding')
    op.drop_table('immunization_report_origin_coding')
    op.drop_table('immunization_vaccine_coding')
    op.drop_table('immunization_status_reason_coding')
    op.drop_table('immunization_identifier_type_coding')
    op.drop_table('immunization_identifier')
    op.drop_table('immunization')

    op.execute("DROP SEQUENCE IF EXISTS immunization_pub_seq")

    op.execute("DROP TYPE IF EXISTS immunization_protocol_applied_authority_reference_type")
    op.execute("DROP TYPE IF EXISTS immunization_reaction_detail_reference_type")
    op.execute("DROP TYPE IF EXISTS immunization_reason_reference_type")
    op.execute("DROP TYPE IF EXISTS immunization_note_author_reference_type")
    op.execute("DROP TYPE IF EXISTS immunization_performer_actor_reference_type")
    op.execute("DROP TYPE IF EXISTS immunization_manufacturer_reference_type")
    op.execute("DROP TYPE IF EXISTS immunization_location_reference_type")
    op.execute("DROP TYPE IF EXISTS immunization_encounter_reference_type")
    op.execute("DROP TYPE IF EXISTS immunization_patient_reference_type")
    op.execute("DROP TYPE IF EXISTS immunization_status")
