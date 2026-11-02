"""add immunization recommendation tables

Revision ID: 06977c394bf1
Revises: 7ae3e808c552
Create Date: 2026-11-02 20:58:43.520705

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '06977c394bf1'
down_revision: Union[str, None] = '7ae3e808c552'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE immunization_recommendation_patient_reference_type AS ENUM ('Patient');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE immunization_recommendation_authority_reference_type AS ENUM ('Organization');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE immunization_recommendation_supporting_immunization_reference_type AS ENUM ('Immunization', 'ImmunizationEvaluation');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE immunization_recommendation_supporting_patient_info_reference_type AS ENUM (
                'Condition', 'Observation', 'AllergyIntolerance', 'DiagnosticReport', 'DocumentReference',
                'Encounter', 'MedicationStatement', 'FamilyMemberHistory', 'Procedure', 'Immunization', 'Resource'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # 2. Sequence
    op.execute("CREATE SEQUENCE IF NOT EXISTS immunization_recommendation_pub_seq START WITH 510000 INCREMENT BY 1")

    # 3. Main table
    op.create_table(
        'immunization_recommendation',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_recommendation_id', sa.BigInteger(), server_default=sa.text("nextval('immunization_recommendation_pub_seq')"), nullable=False),
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
        sa.Column('patient_reference', sa.String(), nullable=False),
        sa.Column('patient_type', postgresql.ENUM('Patient', name='immunization_recommendation_patient_reference_type', create_type=False), nullable=False),
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
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('authority_reference', sa.String(), nullable=True),
        sa.Column('authority_type', postgresql.ENUM('Organization', name='immunization_recommendation_authority_reference_type', create_type=False), nullable=True),
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
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_recommendation_authority_id'), 'immunization_recommendation', ['authority_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_created_at'), 'immunization_recommendation', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_id'), 'immunization_recommendation', ['id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_immunization_recommendation_id'), 'immunization_recommendation', ['immunization_recommendation_id'], unique=True)
    op.create_index(op.f('ix_immunization_recommendation_patient_id'), 'immunization_recommendation', ['patient_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_tenant_id'), 'immunization_recommendation', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_updated_at'), 'immunization_recommendation', ['updated_at'], unique=False)

    # 4. Identifier table
    op.create_table(
        'immunization_recommendation_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_recommendation_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['immunization_recommendation_pk'], ['immunization_recommendation.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_recommendation_identifier_assigner_id'), 'immunization_recommendation_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_identifier_created_at'), 'immunization_recommendation_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_identifier_immunization_recommendation_pk'), 'immunization_recommendation_identifier', ['immunization_recommendation_pk'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_identifier_tenant_id'), 'immunization_recommendation_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_identifier_updated_at'), 'immunization_recommendation_identifier', ['updated_at'], unique=False)

    # 5. Identifier type coding table
    op.create_table(
        'immunization_recommendation_identifier_type_coding',
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
        sa.ForeignKeyConstraint(['identifier_id'], ['immunization_recommendation_identifier.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_recommendation_identifier_type_coding_created_at'), 'immunization_recommendation_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_identifier_type_coding_identifier_id'), 'immunization_recommendation_identifier_type_coding', ['identifier_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_identifier_type_coding_tenant_id'), 'immunization_recommendation_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_identifier_type_coding_updated_at'), 'immunization_recommendation_identifier_type_coding', ['updated_at'], unique=False)

    # 6. Recommendation table
    op.create_table(
        'immunization_recommendation_recommendation',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('immunization_recommendation_pk', sa.BigInteger(), nullable=False),
        sa.Column('target_disease_text', sa.String(), nullable=True),
        sa.Column('forecast_status_text', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('series', sa.String(), nullable=True),
        sa.Column('dose_number_positive_int', sa.Integer(), nullable=True),
        sa.Column('dose_number_string', sa.String(), nullable=True),
        sa.Column('series_doses_positive_int', sa.Integer(), nullable=True),
        sa.Column('series_doses_string', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['immunization_recommendation_pk'], ['immunization_recommendation.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_recommendation_recommendation_created_at'), 'immunization_recommendation_recommendation', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_recommendation_immunization_recommendation_pk'), 'immunization_recommendation_recommendation', ['immunization_recommendation_pk'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_recommendation_tenant_id'), 'immunization_recommendation_recommendation', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_recommendation_updated_at'), 'immunization_recommendation_recommendation', ['updated_at'], unique=False)

    # 7. Vaccine code table
    op.create_table(
        'immunization_recommendation_vaccine_code',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('recommendation_id', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['recommendation_id'], ['immunization_recommendation_recommendation.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_recommendation_vaccine_code_created_at'), 'immunization_recommendation_vaccine_code', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_vaccine_code_recommendation_id'), 'immunization_recommendation_vaccine_code', ['recommendation_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_vaccine_code_tenant_id'), 'immunization_recommendation_vaccine_code', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_vaccine_code_updated_at'), 'immunization_recommendation_vaccine_code', ['updated_at'], unique=False)

    # 8. Vaccine code coding table
    op.create_table(
        'immunization_recommendation_vaccine_code_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('vaccine_code_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['vaccine_code_id'], ['immunization_recommendation_vaccine_code.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_recommendation_vaccine_code_coding_created_at'), 'immunization_recommendation_vaccine_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_vaccine_code_coding_tenant_id'), 'immunization_recommendation_vaccine_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_vaccine_code_coding_updated_at'), 'immunization_recommendation_vaccine_code_coding', ['updated_at'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_vaccine_code_coding_vaccine_code_id'), 'immunization_recommendation_vaccine_code_coding', ['vaccine_code_id'], unique=False)

    # 9. Target disease coding table
    op.create_table(
        'immunization_recommendation_target_disease_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('recommendation_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['recommendation_id'], ['immunization_recommendation_recommendation.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_recommendation_target_disease_coding_created_at'), 'immunization_recommendation_target_disease_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_target_disease_coding_recommendation_id'), 'immunization_recommendation_target_disease_coding', ['recommendation_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_target_disease_coding_tenant_id'), 'immunization_recommendation_target_disease_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_target_disease_coding_updated_at'), 'immunization_recommendation_target_disease_coding', ['updated_at'], unique=False)

    # 10. Contraindicated code table
    op.create_table(
        'immunization_recommendation_contraindicated_code',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('recommendation_id', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['recommendation_id'], ['immunization_recommendation_recommendation.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_recommendation_contraindicated_code_created_at'), 'immunization_recommendation_contraindicated_code', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_contraindicated_code_recommendation_id'), 'immunization_recommendation_contraindicated_code', ['recommendation_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_contraindicated_code_tenant_id'), 'immunization_recommendation_contraindicated_code', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_contraindicated_code_updated_at'), 'immunization_recommendation_contraindicated_code', ['updated_at'], unique=False)

    # 11. Contraindicated coding table
    op.create_table(
        'immunization_recommendation_contraindicated_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('contraindicated_code_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['contraindicated_code_id'], ['immunization_recommendation_contraindicated_code.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_recommendation_contraindicated_coding_created_at'), 'immunization_recommendation_contraindicated_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_contraindicated_coding_contraindicated_code_id'), 'immunization_recommendation_contraindicated_coding', ['contraindicated_code_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_contraindicated_coding_tenant_id'), 'immunization_recommendation_contraindicated_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_contraindicated_coding_updated_at'), 'immunization_recommendation_contraindicated_coding', ['updated_at'], unique=False)

    # 12. Forecast status coding table
    op.create_table(
        'immunization_recommendation_forecast_status_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('recommendation_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['recommendation_id'], ['immunization_recommendation_recommendation.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_recommendation_forecast_status_coding_created_at'), 'immunization_recommendation_forecast_status_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_forecast_status_coding_recommendation_id'), 'immunization_recommendation_forecast_status_coding', ['recommendation_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_forecast_status_coding_tenant_id'), 'immunization_recommendation_forecast_status_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_forecast_status_coding_updated_at'), 'immunization_recommendation_forecast_status_coding', ['updated_at'], unique=False)

    # 13. Forecast reason table
    op.create_table(
        'immunization_recommendation_forecast_reason',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('recommendation_id', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['recommendation_id'], ['immunization_recommendation_recommendation.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_recommendation_forecast_reason_created_at'), 'immunization_recommendation_forecast_reason', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_forecast_reason_recommendation_id'), 'immunization_recommendation_forecast_reason', ['recommendation_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_forecast_reason_tenant_id'), 'immunization_recommendation_forecast_reason', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_forecast_reason_updated_at'), 'immunization_recommendation_forecast_reason', ['updated_at'], unique=False)

    # 14. Forecast reason coding table
    op.create_table(
        'immunization_recommendation_forecast_reason_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('forecast_reason_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['forecast_reason_id'], ['immunization_recommendation_forecast_reason.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_recommendation_forecast_reason_coding_created_at'), 'immunization_recommendation_forecast_reason_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_forecast_reason_coding_forecast_reason_id'), 'immunization_recommendation_forecast_reason_coding', ['forecast_reason_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_forecast_reason_coding_tenant_id'), 'immunization_recommendation_forecast_reason_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_forecast_reason_coding_updated_at'), 'immunization_recommendation_forecast_reason_coding', ['updated_at'], unique=False)

    # 15. Date criterion table
    op.create_table(
        'immunization_recommendation_date_criterion',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('recommendation_id', sa.BigInteger(), nullable=False),
        sa.Column('code_text', sa.String(), nullable=True),
        sa.Column('value', sa.DateTime(timezone=True), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['recommendation_id'], ['immunization_recommendation_recommendation.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_recommendation_date_criterion_created_at'), 'immunization_recommendation_date_criterion', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_date_criterion_recommendation_id'), 'immunization_recommendation_date_criterion', ['recommendation_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_date_criterion_tenant_id'), 'immunization_recommendation_date_criterion', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_date_criterion_updated_at'), 'immunization_recommendation_date_criterion', ['updated_at'], unique=False)

    # 16. Date criterion coding table
    op.create_table(
        'immunization_recommendation_date_criterion_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('date_criterion_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['date_criterion_id'], ['immunization_recommendation_date_criterion.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_recommendation_date_criterion_coding_created_at'), 'immunization_recommendation_date_criterion_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_date_criterion_coding_date_criterion_id'), 'immunization_recommendation_date_criterion_coding', ['date_criterion_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_date_criterion_coding_tenant_id'), 'immunization_recommendation_date_criterion_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_date_criterion_coding_updated_at'), 'immunization_recommendation_date_criterion_coding', ['updated_at'], unique=False)

    # 17. Supporting immunization table
    op.create_table(
        'immunization_recommendation_supporting_immunization',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('recommendation_id', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Immunization', 'ImmunizationEvaluation', name='immunization_recommendation_supporting_immunization_reference_type', create_type=False), nullable=True),
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
        sa.ForeignKeyConstraint(['recommendation_id'], ['immunization_recommendation_recommendation.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_recommendation_supporting_immunization_created_at'), 'immunization_recommendation_supporting_immunization', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_supporting_immunization_recommendation_id'), 'immunization_recommendation_supporting_immunization', ['recommendation_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_supporting_immunization_reference_id'), 'immunization_recommendation_supporting_immunization', ['reference_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_supporting_immunization_tenant_id'), 'immunization_recommendation_supporting_immunization', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_supporting_immunization_updated_at'), 'immunization_recommendation_supporting_immunization', ['updated_at'], unique=False)

    # 18. Supporting patient info table
    op.create_table(
        'immunization_recommendation_supporting_patient_info',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('recommendation_id', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Condition', 'Observation', 'AllergyIntolerance', 'DiagnosticReport', 'DocumentReference', 'Encounter', 'MedicationStatement', 'FamilyMemberHistory', 'Procedure', 'Immunization', 'Resource', name='immunization_recommendation_supporting_patient_info_reference_type', create_type=False), nullable=True),
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
        sa.ForeignKeyConstraint(['recommendation_id'], ['immunization_recommendation_recommendation.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_immunization_recommendation_supporting_patient_info_created_at'), 'immunization_recommendation_supporting_patient_info', ['created_at'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_supporting_patient_info_recommendation_id'), 'immunization_recommendation_supporting_patient_info', ['recommendation_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_supporting_patient_info_reference_id'), 'immunization_recommendation_supporting_patient_info', ['reference_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_supporting_patient_info_tenant_id'), 'immunization_recommendation_supporting_patient_info', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_immunization_recommendation_supporting_patient_info_updated_at'), 'immunization_recommendation_supporting_patient_info', ['updated_at'], unique=False)


def downgrade() -> None:
    op.drop_table('immunization_recommendation_supporting_patient_info')
    op.drop_table('immunization_recommendation_supporting_immunization')
    op.drop_table('immunization_recommendation_date_criterion_coding')
    op.drop_table('immunization_recommendation_date_criterion')
    op.drop_table('immunization_recommendation_forecast_reason_coding')
    op.drop_table('immunization_recommendation_forecast_reason')
    op.drop_table('immunization_recommendation_forecast_status_coding')
    op.drop_table('immunization_recommendation_contraindicated_coding')
    op.drop_table('immunization_recommendation_contraindicated_code')
    op.drop_table('immunization_recommendation_target_disease_coding')
    op.drop_table('immunization_recommendation_vaccine_code_coding')
    op.drop_table('immunization_recommendation_vaccine_code')
    op.drop_table('immunization_recommendation_recommendation')
    op.drop_table('immunization_recommendation_identifier_type_coding')
    op.drop_table('immunization_recommendation_identifier')
    op.drop_table('immunization_recommendation')

    op.execute("DROP SEQUENCE IF EXISTS immunization_recommendation_pub_seq")

    op.execute("DROP TYPE IF EXISTS immunization_recommendation_supporting_patient_info_reference_type")
    op.execute("DROP TYPE IF EXISTS immunization_recommendation_supporting_immunization_reference_type")
    op.execute("DROP TYPE IF EXISTS immunization_recommendation_authority_reference_type")
    op.execute("DROP TYPE IF EXISTS immunization_recommendation_patient_reference_type")
