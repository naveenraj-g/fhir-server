"""add_measure_report_tables

Revision ID: 9c0fd7d14661
Revises: c0af930ace41
Create Date: 2026-11-03 11:25:02.240389

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '9c0fd7d14661'
down_revision: Union[str, None] = 'c0af930ace41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE measure_report_quantity_comparator AS ENUM (
                'lt', 'le', 'ge', 'gt'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE measure_report_reporter_reference_type AS ENUM (
                'Practitioner', 'PractitionerRole', 'Organization', 'Location'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE measure_report_status AS ENUM (
                'complete', 'pending', 'error'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE measure_report_subject_reference_type AS ENUM (
                'Patient', 'Practitioner', 'PractitionerRole', 'Location', 'Device', 'RelatedPerson', 'Group'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE measure_report_subject_results_reference_type AS ENUM (
                'List'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE measure_report_type AS ENUM (
                'individual', 'subject_list', 'summary', 'data_collection'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # 2. Sequence
    op.execute("CREATE SEQUENCE IF NOT EXISTS measure_report_pub_seq START WITH 570000 INCREMENT BY 1;")

    # 3. Tables
    op.create_table('measure_report',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_report_id', sa.BigInteger(), server_default=sa.text("nextval('measure_report_pub_seq')"), nullable=False),
    sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
    sa.Column('status', postgresql.ENUM('complete', 'pending', 'error', name='measure_report_status', create_type=False), nullable=False),
    sa.Column('type', postgresql.ENUM('individual', 'subject_list', 'summary', 'data_collection', name='measure_report_type', create_type=False), nullable=False),
    sa.Column('measure', sa.String(), nullable=False),
    sa.Column('subject_reference', sa.String(), nullable=True),
    sa.Column('subject_type', postgresql.ENUM('Patient', 'Practitioner', 'PractitionerRole', 'Location', 'Device', 'RelatedPerson', 'Group', name='measure_report_subject_reference_type', create_type=False), nullable=True),
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
    sa.Column('date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('reporter_reference', sa.String(), nullable=True),
    sa.Column('reporter_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization', 'Location', name='measure_report_reporter_reference_type', create_type=False), nullable=True),
    sa.Column('reporter_id', sa.BigInteger(), nullable=True),
    sa.Column('reporter_display', sa.String(), nullable=True),
    sa.Column('reporter_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('reporter_identifier_type_system', sa.String(), nullable=True),
    sa.Column('reporter_identifier_type_version', sa.String(), nullable=True),
    sa.Column('reporter_identifier_type_code', sa.String(), nullable=True),
    sa.Column('reporter_identifier_type_display', sa.String(), nullable=True),
    sa.Column('reporter_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('reporter_identifier_type_text', sa.String(), nullable=True),
    sa.Column('reporter_identifier_system', sa.String(), nullable=True),
    sa.Column('reporter_identifier_value', sa.String(), nullable=True),
    sa.Column('reporter_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('reporter_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('improvement_notation_text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_report_created_at'), 'measure_report', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_report_id'), 'measure_report', ['id'], unique=False)
    op.create_index(op.f('ix_measure_report_measure_report_id'), 'measure_report', ['measure_report_id'], unique=True)
    op.create_index(op.f('ix_measure_report_reporter_id'), 'measure_report', ['reporter_id'], unique=False)
    op.create_index(op.f('ix_measure_report_subject_id'), 'measure_report', ['subject_id'], unique=False)
    op.create_index(op.f('ix_measure_report_tenant_id'), 'measure_report', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_report_updated_at'), 'measure_report', ['updated_at'], unique=False)
    op.create_table('measure_report_evaluated_resource',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_report_pk', sa.BigInteger(), nullable=False),
    sa.Column('evaluated_resource_reference', sa.String(), nullable=True),
    sa.Column('evaluated_resource_type', sa.String(), nullable=True),
    sa.Column('evaluated_resource_id', sa.BigInteger(), nullable=True),
    sa.Column('evaluated_resource_display', sa.String(), nullable=True),
    sa.Column('evaluated_resource_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('evaluated_resource_identifier_type_system', sa.String(), nullable=True),
    sa.Column('evaluated_resource_identifier_type_version', sa.String(), nullable=True),
    sa.Column('evaluated_resource_identifier_type_code', sa.String(), nullable=True),
    sa.Column('evaluated_resource_identifier_type_display', sa.String(), nullable=True),
    sa.Column('evaluated_resource_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('evaluated_resource_identifier_type_text', sa.String(), nullable=True),
    sa.Column('evaluated_resource_identifier_system', sa.String(), nullable=True),
    sa.Column('evaluated_resource_identifier_value', sa.String(), nullable=True),
    sa.Column('evaluated_resource_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('evaluated_resource_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['measure_report_pk'], ['measure_report.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_report_evaluated_resource_created_at'), 'measure_report_evaluated_resource', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_report_evaluated_resource_evaluated_resource_id'), 'measure_report_evaluated_resource', ['evaluated_resource_id'], unique=False)
    op.create_index(op.f('ix_measure_report_evaluated_resource_measure_report_pk'), 'measure_report_evaluated_resource', ['measure_report_pk'], unique=False)
    op.create_index(op.f('ix_measure_report_evaluated_resource_tenant_id'), 'measure_report_evaluated_resource', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_report_evaluated_resource_updated_at'), 'measure_report_evaluated_resource', ['updated_at'], unique=False)
    op.create_table('measure_report_group',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_report_pk', sa.BigInteger(), nullable=False),
    sa.Column('code_text', sa.String(), nullable=True),
    sa.Column('measure_score_value', sa.Numeric(), nullable=True),
    sa.Column('measure_score_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='measure_report_quantity_comparator', create_type=False), nullable=True),
    sa.Column('measure_score_unit', sa.String(), nullable=True),
    sa.Column('measure_score_system', sa.String(), nullable=True),
    sa.Column('measure_score_code', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['measure_report_pk'], ['measure_report.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_report_group_created_at'), 'measure_report_group', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_report_group_measure_report_pk'), 'measure_report_group', ['measure_report_pk'], unique=False)
    op.create_index(op.f('ix_measure_report_group_tenant_id'), 'measure_report_group', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_updated_at'), 'measure_report_group', ['updated_at'], unique=False)
    op.create_table('measure_report_identifier',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_report_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['measure_report_pk'], ['measure_report.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_report_identifier_assigner_id'), 'measure_report_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_measure_report_identifier_created_at'), 'measure_report_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_report_identifier_measure_report_pk'), 'measure_report_identifier', ['measure_report_pk'], unique=False)
    op.create_index(op.f('ix_measure_report_identifier_tenant_id'), 'measure_report_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_report_identifier_updated_at'), 'measure_report_identifier', ['updated_at'], unique=False)
    op.create_table('measure_report_improvement_notation_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('measure_report_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['measure_report_pk'], ['measure_report.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_report_improvement_notation_coding_created_at'), 'measure_report_improvement_notation_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_report_improvement_notation_coding_measure_report_pk'), 'measure_report_improvement_notation_coding', ['measure_report_pk'], unique=False)
    op.create_index(op.f('ix_measure_report_improvement_notation_coding_tenant_id'), 'measure_report_improvement_notation_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_report_improvement_notation_coding_updated_at'), 'measure_report_improvement_notation_coding', ['updated_at'], unique=False)
    op.create_table('measure_report_group_code_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('group_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['group_id'], ['measure_report_group.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_report_group_code_coding_created_at'), 'measure_report_group_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_report_group_code_coding_group_id'), 'measure_report_group_code_coding', ['group_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_code_coding_tenant_id'), 'measure_report_group_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_code_coding_updated_at'), 'measure_report_group_code_coding', ['updated_at'], unique=False)
    op.create_table('measure_report_group_population',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('group_id', sa.BigInteger(), nullable=False),
    sa.Column('code_text', sa.String(), nullable=True),
    sa.Column('count', sa.BigInteger(), nullable=True),
    sa.Column('subject_results_reference', sa.String(), nullable=True),
    sa.Column('subject_results_type', postgresql.ENUM('List', name='measure_report_subject_results_reference_type', create_type=False), nullable=True),
    sa.Column('subject_results_id', sa.BigInteger(), nullable=True),
    sa.Column('subject_results_display', sa.String(), nullable=True),
    sa.Column('subject_results_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('subject_results_identifier_type_system', sa.String(), nullable=True),
    sa.Column('subject_results_identifier_type_version', sa.String(), nullable=True),
    sa.Column('subject_results_identifier_type_code', sa.String(), nullable=True),
    sa.Column('subject_results_identifier_type_display', sa.String(), nullable=True),
    sa.Column('subject_results_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('subject_results_identifier_type_text', sa.String(), nullable=True),
    sa.Column('subject_results_identifier_system', sa.String(), nullable=True),
    sa.Column('subject_results_identifier_value', sa.String(), nullable=True),
    sa.Column('subject_results_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('subject_results_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['group_id'], ['measure_report_group.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_report_group_population_created_at'), 'measure_report_group_population', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_report_group_population_group_id'), 'measure_report_group_population', ['group_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_population_subject_results_id'), 'measure_report_group_population', ['subject_results_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_population_tenant_id'), 'measure_report_group_population', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_population_updated_at'), 'measure_report_group_population', ['updated_at'], unique=False)
    op.create_table('measure_report_group_stratifier',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('group_id', sa.BigInteger(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['group_id'], ['measure_report_group.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_report_group_stratifier_created_at'), 'measure_report_group_stratifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_group_id'), 'measure_report_group_stratifier', ['group_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_tenant_id'), 'measure_report_group_stratifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_updated_at'), 'measure_report_group_stratifier', ['updated_at'], unique=False)
    op.create_table('measure_report_identifier_type_coding',
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
    sa.ForeignKeyConstraint(['identifier_id'], ['measure_report_identifier.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_report_identifier_type_coding_created_at'), 'measure_report_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_report_identifier_type_coding_identifier_id'), 'measure_report_identifier_type_coding', ['identifier_id'], unique=False)
    op.create_index(op.f('ix_measure_report_identifier_type_coding_tenant_id'), 'measure_report_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_report_identifier_type_coding_updated_at'), 'measure_report_identifier_type_coding', ['updated_at'], unique=False)
    op.create_table('measure_report_group_population_code_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('population_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['population_id'], ['measure_report_group_population.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_report_group_population_code_coding_created_at'), 'measure_report_group_population_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_report_group_population_code_coding_population_id'), 'measure_report_group_population_code_coding', ['population_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_population_code_coding_tenant_id'), 'measure_report_group_population_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_population_code_coding_updated_at'), 'measure_report_group_population_code_coding', ['updated_at'], unique=False)
    op.create_table('measure_report_group_stratifier_code',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('stratifier_id', sa.BigInteger(), nullable=False),
    sa.Column('code_text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['stratifier_id'], ['measure_report_group_stratifier.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_report_group_stratifier_code_created_at'), 'measure_report_group_stratifier_code', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_code_stratifier_id'), 'measure_report_group_stratifier_code', ['stratifier_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_code_tenant_id'), 'measure_report_group_stratifier_code', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_code_updated_at'), 'measure_report_group_stratifier_code', ['updated_at'], unique=False)
    op.create_table('measure_report_group_stratifier_stratum',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('stratifier_id', sa.BigInteger(), nullable=False),
    sa.Column('value_text', sa.String(), nullable=True),
    sa.Column('measure_score_value', sa.Numeric(), nullable=True),
    sa.Column('measure_score_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='measure_report_quantity_comparator', create_type=False), nullable=True),
    sa.Column('measure_score_unit', sa.String(), nullable=True),
    sa.Column('measure_score_system', sa.String(), nullable=True),
    sa.Column('measure_score_code', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['stratifier_id'], ['measure_report_group_stratifier.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_created_at'), 'measure_report_group_stratifier_stratum', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_stratifier_id'), 'measure_report_group_stratifier_stratum', ['stratifier_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_tenant_id'), 'measure_report_group_stratifier_stratum', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_updated_at'), 'measure_report_group_stratifier_stratum', ['updated_at'], unique=False)
    op.create_table('measure_report_group_stratifier_code_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('stratifier_code_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['stratifier_code_id'], ['measure_report_group_stratifier_code.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_report_group_stratifier_code_coding_created_at'), 'measure_report_group_stratifier_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_code_coding_stratifier_code_id'), 'measure_report_group_stratifier_code_coding', ['stratifier_code_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_code_coding_tenant_id'), 'measure_report_group_stratifier_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_code_coding_updated_at'), 'measure_report_group_stratifier_code_coding', ['updated_at'], unique=False)
    op.create_table('measure_report_group_stratifier_stratum_component',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('stratum_id', sa.BigInteger(), nullable=False),
    sa.Column('code_text', sa.String(), nullable=True),
    sa.Column('value_text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['stratum_id'], ['measure_report_group_stratifier_stratum.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_component_created_at'), 'measure_report_group_stratifier_stratum_component', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_component_stratum_id'), 'measure_report_group_stratifier_stratum_component', ['stratum_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_component_tenant_id'), 'measure_report_group_stratifier_stratum_component', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_component_updated_at'), 'measure_report_group_stratifier_stratum_component', ['updated_at'], unique=False)
    op.create_table('measure_report_group_stratifier_stratum_population',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('stratum_id', sa.BigInteger(), nullable=False),
    sa.Column('code_text', sa.String(), nullable=True),
    sa.Column('count', sa.BigInteger(), nullable=True),
    sa.Column('subject_results_reference', sa.String(), nullable=True),
    sa.Column('subject_results_type', postgresql.ENUM('List', name='measure_report_subject_results_reference_type', create_type=False), nullable=True),
    sa.Column('subject_results_id', sa.BigInteger(), nullable=True),
    sa.Column('subject_results_display', sa.String(), nullable=True),
    sa.Column('subject_results_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('subject_results_identifier_type_system', sa.String(), nullable=True),
    sa.Column('subject_results_identifier_type_version', sa.String(), nullable=True),
    sa.Column('subject_results_identifier_type_code', sa.String(), nullable=True),
    sa.Column('subject_results_identifier_type_display', sa.String(), nullable=True),
    sa.Column('subject_results_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('subject_results_identifier_type_text', sa.String(), nullable=True),
    sa.Column('subject_results_identifier_system', sa.String(), nullable=True),
    sa.Column('subject_results_identifier_value', sa.String(), nullable=True),
    sa.Column('subject_results_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('subject_results_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['stratum_id'], ['measure_report_group_stratifier_stratum.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_population_created_at'), 'measure_report_group_stratifier_stratum_population', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_population_subject_results_id'), 'measure_report_group_stratifier_stratum_population', ['subject_results_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_population_stratum_id'), 'measure_report_group_stratifier_stratum_population', ['stratum_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_population_tenant_id'), 'measure_report_group_stratifier_stratum_population', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_population_updated_at'), 'measure_report_group_stratifier_stratum_population', ['updated_at'], unique=False)
    op.create_table('measure_report_group_stratifier_stratum_value_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('stratum_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['stratum_id'], ['measure_report_group_stratifier_stratum.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_value_coding_stratum_id'), 'measure_report_group_stratifier_stratum_value_coding', ['stratum_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_value_coding_updated_at'), 'measure_report_group_stratifier_stratum_value_coding', ['updated_at'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_value_coding_tenant_id'), 'measure_report_group_stratifier_stratum_value_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_value_coding_created_at'), 'measure_report_group_stratifier_stratum_value_coding', ['created_at'], unique=False)
    op.create_table('measure_report_group_stratifier_stratum_comp_code_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('component_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['component_id'], ['measure_report_group_stratifier_stratum_component.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_comp_code_coding_component_id'), 'measure_report_group_stratifier_stratum_comp_code_coding', ['component_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_comp_code_coding_tenant_id'), 'measure_report_group_stratifier_stratum_comp_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_comp_code_coding_created_at'), 'measure_report_group_stratifier_stratum_comp_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_comp_code_coding_updated_at'), 'measure_report_group_stratifier_stratum_comp_code_coding', ['updated_at'], unique=False)
    op.create_table('measure_report_group_stratifier_stratum_comp_value_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('component_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['component_id'], ['measure_report_group_stratifier_stratum_component.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_comp_value_coding_updated_at'), 'measure_report_group_stratifier_stratum_comp_value_coding', ['updated_at'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_comp_value_coding_component_id'), 'measure_report_group_stratifier_stratum_comp_value_coding', ['component_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_comp_value_coding_tenant_id'), 'measure_report_group_stratifier_stratum_comp_value_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_comp_value_coding_created_at'), 'measure_report_group_stratifier_stratum_comp_value_coding', ['created_at'], unique=False)
    op.create_table('measure_report_group_stratifier_stratum_pop_code_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('stratum_population_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['stratum_population_id'], ['measure_report_group_stratifier_stratum_population.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_pop_code_coding_stratum_population_id'), 'measure_report_group_stratifier_stratum_pop_code_coding', ['stratum_population_id'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_pop_code_coding_created_at'), 'measure_report_group_stratifier_stratum_pop_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_pop_code_coding_updated_at'), 'measure_report_group_stratifier_stratum_pop_code_coding', ['updated_at'], unique=False)
    op.create_index(op.f('ix_measure_report_group_stratifier_stratum_pop_code_coding_tenant_id'), 'measure_report_group_stratifier_stratum_pop_code_coding', ['tenant_id'], unique=False)

def downgrade() -> None:
    op.drop_table('measure_report_group_stratifier_stratum_pop_code_coding')
    op.drop_table('measure_report_group_stratifier_stratum_comp_value_coding')
    op.drop_table('measure_report_group_stratifier_stratum_comp_code_coding')
    op.drop_table('measure_report_group_stratifier_stratum_value_coding')
    op.drop_table('measure_report_group_stratifier_stratum_population')
    op.drop_table('measure_report_group_stratifier_stratum_component')
    op.drop_table('measure_report_group_stratifier_code_coding')
    op.drop_table('measure_report_group_stratifier_stratum')
    op.drop_table('measure_report_group_stratifier_code')
    op.drop_table('measure_report_group_population_code_coding')
    op.drop_table('measure_report_identifier_type_coding')
    op.drop_table('measure_report_group_stratifier')
    op.drop_table('measure_report_group_population')
    op.drop_table('measure_report_group_code_coding')
    op.drop_table('measure_report_improvement_notation_coding')
    op.drop_table('measure_report_identifier')
    op.drop_table('measure_report_group')
    op.drop_table('measure_report_evaluated_resource')
    op.drop_table('measure_report')
    op.execute("DROP SEQUENCE IF EXISTS measure_report_pub_seq")
    op.execute("DROP TYPE IF EXISTS measure_report_type")
    op.execute("DROP TYPE IF EXISTS measure_report_subject_results_reference_type")
    op.execute("DROP TYPE IF EXISTS measure_report_subject_reference_type")
    op.execute("DROP TYPE IF EXISTS measure_report_status")
    op.execute("DROP TYPE IF EXISTS measure_report_reporter_reference_type")
    op.execute("DROP TYPE IF EXISTS measure_report_quantity_comparator")
