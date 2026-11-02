"""add_family_member_history_tables

Revision ID: 4b2458546921
Revises: 6bae59a881f2
Create Date: 2026-11-02 16:39:02.713520

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4b2458546921'
down_revision: Union[str, None] = '6bae59a881f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE family_member_history_status AS ENUM ('partial', 'completed', 'entered-in-error', 'health-unknown');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE family_member_history_patient_reference_type AS ENUM ('Patient');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE family_member_history_quantity_comparator AS ENUM ('lt', 'le', 'ge', 'gt');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE family_member_history_reason_reference_type AS ENUM (
                'Condition', 'Observation', 'AllergyIntolerance', 'QuestionnaireResponse', 'DiagnosticReport', 'DocumentReference'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE family_member_history_note_author_reference_type AS ENUM (
                'Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson', 'Organization'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    op.execute('CREATE SEQUENCE IF NOT EXISTS family_member_history_pub_seq START 490000 INCREMENT 1')

    op.create_table('family_member_history',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('family_member_history_id', sa.BigInteger(), server_default=sa.text("nextval('family_member_history_pub_seq')"), nullable=False),
    sa.Column('instantiates_canonical', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('instantiates_uri', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('status', postgresql.ENUM('partial', 'completed', 'entered-in-error', 'health-unknown', name='family_member_history_status', create_type=False), nullable=False),
    sa.Column('data_absent_reason_text', sa.String(), nullable=True),
    sa.Column('patient_reference', sa.String(), nullable=False),
    sa.Column('patient_type', postgresql.ENUM('Patient', name='family_member_history_patient_reference_type', create_type=False), nullable=False),
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
    sa.Column('date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('relationship_text', sa.String(), nullable=True),
    sa.Column('sex_text', sa.String(), nullable=True),
    sa.Column('born_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('born_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('born_date', sa.Date(), nullable=True),
    sa.Column('born_string', sa.String(), nullable=True),
    sa.Column('age_age_value', sa.Numeric(), nullable=True),
    sa.Column('age_age_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='family_member_history_quantity_comparator', create_type=False), nullable=True),
    sa.Column('age_age_unit', sa.String(), nullable=True),
    sa.Column('age_age_system', sa.String(), nullable=True),
    sa.Column('age_age_code', sa.String(), nullable=True),
    sa.Column('age_range_low_value', sa.Numeric(), nullable=True),
    sa.Column('age_range_low_unit', sa.String(), nullable=True),
    sa.Column('age_range_low_system', sa.String(), nullable=True),
    sa.Column('age_range_low_code', sa.String(), nullable=True),
    sa.Column('age_range_high_value', sa.Numeric(), nullable=True),
    sa.Column('age_range_high_unit', sa.String(), nullable=True),
    sa.Column('age_range_high_system', sa.String(), nullable=True),
    sa.Column('age_range_high_code', sa.String(), nullable=True),
    sa.Column('age_string', sa.String(), nullable=True),
    sa.Column('estimated_age', sa.Boolean(), nullable=True),
    sa.Column('deceased_boolean', sa.Boolean(), nullable=True),
    sa.Column('deceased_age_value', sa.Numeric(), nullable=True),
    sa.Column('deceased_age_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='family_member_history_quantity_comparator', create_type=False), nullable=True),
    sa.Column('deceased_age_unit', sa.String(), nullable=True),
    sa.Column('deceased_age_system', sa.String(), nullable=True),
    sa.Column('deceased_age_code', sa.String(), nullable=True),
    sa.Column('deceased_range_low_value', sa.Numeric(), nullable=True),
    sa.Column('deceased_range_low_unit', sa.String(), nullable=True),
    sa.Column('deceased_range_low_system', sa.String(), nullable=True),
    sa.Column('deceased_range_low_code', sa.String(), nullable=True),
    sa.Column('deceased_range_high_value', sa.Numeric(), nullable=True),
    sa.Column('deceased_range_high_unit', sa.String(), nullable=True),
    sa.Column('deceased_range_high_system', sa.String(), nullable=True),
    sa.Column('deceased_range_high_code', sa.String(), nullable=True),
    sa.Column('deceased_date', sa.Date(), nullable=True),
    sa.Column('deceased_string', sa.String(), nullable=True),
    sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_member_history_created_at'), 'family_member_history', ['created_at'], unique=False)
    op.create_index(op.f('ix_family_member_history_family_member_history_id'), 'family_member_history', ['family_member_history_id'], unique=True)
    op.create_index(op.f('ix_family_member_history_patient_id'), 'family_member_history', ['patient_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_tenant_id'), 'family_member_history', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_updated_at'), 'family_member_history', ['updated_at'], unique=False)
    op.create_table('family_member_history_condition',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('family_member_history_pk', sa.BigInteger(), nullable=False),
    sa.Column('code_text', sa.String(), nullable=True),
    sa.Column('outcome_text', sa.String(), nullable=True),
    sa.Column('contributed_to_death', sa.Boolean(), nullable=True),
    sa.Column('onset_age_value', sa.Numeric(), nullable=True),
    sa.Column('onset_age_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='family_member_history_quantity_comparator', create_type=False), nullable=True),
    sa.Column('onset_age_unit', sa.String(), nullable=True),
    sa.Column('onset_age_system', sa.String(), nullable=True),
    sa.Column('onset_age_code', sa.String(), nullable=True),
    sa.Column('onset_range_low_value', sa.Numeric(), nullable=True),
    sa.Column('onset_range_low_unit', sa.String(), nullable=True),
    sa.Column('onset_range_low_system', sa.String(), nullable=True),
    sa.Column('onset_range_low_code', sa.String(), nullable=True),
    sa.Column('onset_range_high_value', sa.Numeric(), nullable=True),
    sa.Column('onset_range_high_unit', sa.String(), nullable=True),
    sa.Column('onset_range_high_system', sa.String(), nullable=True),
    sa.Column('onset_range_high_code', sa.String(), nullable=True),
    sa.Column('onset_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('onset_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('onset_string', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['family_member_history_pk'], ['family_member_history.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_member_history_condition_created_at'), 'family_member_history_condition', ['created_at'], unique=False)
    op.create_index(op.f('ix_family_member_history_condition_family_member_history_pk'), 'family_member_history_condition', ['family_member_history_pk'], unique=False)
    op.create_index(op.f('ix_family_member_history_condition_tenant_id'), 'family_member_history_condition', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_condition_updated_at'), 'family_member_history_condition', ['updated_at'], unique=False)
    op.create_table('family_member_history_data_absent_reason_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('family_member_history_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['family_member_history_pk'], ['family_member_history.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_member_history_data_absent_reason_coding_created_at'), 'family_member_history_data_absent_reason_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_family_member_history_data_absent_reason_coding_family_member_history_pk'), 'family_member_history_data_absent_reason_coding', ['family_member_history_pk'], unique=False)
    op.create_index(op.f('ix_family_member_history_data_absent_reason_coding_tenant_id'), 'family_member_history_data_absent_reason_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_data_absent_reason_coding_updated_at'), 'family_member_history_data_absent_reason_coding', ['updated_at'], unique=False)
    op.create_table('family_member_history_identifier',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('family_member_history_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['family_member_history_pk'], ['family_member_history.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_member_history_identifier_assigner_id'), 'family_member_history_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_identifier_created_at'), 'family_member_history_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_family_member_history_identifier_family_member_history_pk'), 'family_member_history_identifier', ['family_member_history_pk'], unique=False)
    op.create_index(op.f('ix_family_member_history_identifier_tenant_id'), 'family_member_history_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_identifier_updated_at'), 'family_member_history_identifier', ['updated_at'], unique=False)
    op.create_table('family_member_history_note',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('family_member_history_pk', sa.BigInteger(), nullable=False),
    sa.Column('author_string', sa.String(), nullable=True),
    sa.Column('author_reference', sa.String(), nullable=True),
    sa.Column('author_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson', 'Organization', name='family_member_history_note_author_reference_type', create_type=False), nullable=True),
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
    sa.Column('time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('text', sa.Text(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['family_member_history_pk'], ['family_member_history.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_member_history_note_author_id'), 'family_member_history_note', ['author_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_note_created_at'), 'family_member_history_note', ['created_at'], unique=False)
    op.create_index(op.f('ix_family_member_history_note_family_member_history_pk'), 'family_member_history_note', ['family_member_history_pk'], unique=False)
    op.create_index(op.f('ix_family_member_history_note_tenant_id'), 'family_member_history_note', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_note_updated_at'), 'family_member_history_note', ['updated_at'], unique=False)
    op.create_table('family_member_history_reason_code',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('family_member_history_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['family_member_history_pk'], ['family_member_history.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_member_history_reason_code_created_at'), 'family_member_history_reason_code', ['created_at'], unique=False)
    op.create_index(op.f('ix_family_member_history_reason_code_family_member_history_pk'), 'family_member_history_reason_code', ['family_member_history_pk'], unique=False)
    op.create_index(op.f('ix_family_member_history_reason_code_tenant_id'), 'family_member_history_reason_code', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_reason_code_updated_at'), 'family_member_history_reason_code', ['updated_at'], unique=False)
    op.create_table('family_member_history_reason_reference',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('family_member_history_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Condition', 'Observation', 'AllergyIntolerance', 'QuestionnaireResponse', 'DiagnosticReport', 'DocumentReference', name='family_member_history_reason_reference_type', create_type=False), nullable=True),
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
    sa.ForeignKeyConstraint(['family_member_history_pk'], ['family_member_history.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_member_history_reason_reference_created_at'), 'family_member_history_reason_reference', ['created_at'], unique=False)
    op.create_index(op.f('ix_family_member_history_reason_reference_family_member_history_pk'), 'family_member_history_reason_reference', ['family_member_history_pk'], unique=False)
    op.create_index(op.f('ix_family_member_history_reason_reference_reference_id'), 'family_member_history_reason_reference', ['reference_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_reason_reference_tenant_id'), 'family_member_history_reason_reference', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_reason_reference_updated_at'), 'family_member_history_reason_reference', ['updated_at'], unique=False)
    op.create_table('family_member_history_relationship_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('family_member_history_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['family_member_history_pk'], ['family_member_history.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_member_history_relationship_coding_created_at'), 'family_member_history_relationship_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_family_member_history_relationship_coding_family_member_history_pk'), 'family_member_history_relationship_coding', ['family_member_history_pk'], unique=False)
    op.create_index(op.f('ix_family_member_history_relationship_coding_tenant_id'), 'family_member_history_relationship_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_relationship_coding_updated_at'), 'family_member_history_relationship_coding', ['updated_at'], unique=False)
    op.create_table('family_member_history_sex_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('family_member_history_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['family_member_history_pk'], ['family_member_history.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_member_history_sex_coding_created_at'), 'family_member_history_sex_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_family_member_history_sex_coding_family_member_history_pk'), 'family_member_history_sex_coding', ['family_member_history_pk'], unique=False)
    op.create_index(op.f('ix_family_member_history_sex_coding_tenant_id'), 'family_member_history_sex_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_sex_coding_updated_at'), 'family_member_history_sex_coding', ['updated_at'], unique=False)
    op.create_table('family_member_history_condition_code_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('family_member_history_condition_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['family_member_history_condition_id'], ['family_member_history_condition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_member_history_condition_code_coding_created_at'), 'family_member_history_condition_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_family_member_history_condition_code_coding_family_member_history_condition_id'), 'family_member_history_condition_code_coding', ['family_member_history_condition_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_condition_code_coding_tenant_id'), 'family_member_history_condition_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_condition_code_coding_updated_at'), 'family_member_history_condition_code_coding', ['updated_at'], unique=False)
    op.create_table('family_member_history_condition_note',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('family_member_history_condition_id', sa.BigInteger(), nullable=False),
    sa.Column('author_string', sa.String(), nullable=True),
    sa.Column('author_reference', sa.String(), nullable=True),
    sa.Column('author_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson', 'Organization', name='family_member_history_note_author_reference_type', create_type=False), nullable=True),
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
    sa.Column('time', sa.DateTime(timezone=True), nullable=True),
    sa.Column('text', sa.Text(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['family_member_history_condition_id'], ['family_member_history_condition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_member_history_condition_note_author_id'), 'family_member_history_condition_note', ['author_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_condition_note_created_at'), 'family_member_history_condition_note', ['created_at'], unique=False)
    op.create_index(op.f('ix_family_member_history_condition_note_family_member_history_condition_id'), 'family_member_history_condition_note', ['family_member_history_condition_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_condition_note_tenant_id'), 'family_member_history_condition_note', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_condition_note_updated_at'), 'family_member_history_condition_note', ['updated_at'], unique=False)
    op.create_table('family_member_history_condition_outcome_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('family_member_history_condition_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['family_member_history_condition_id'], ['family_member_history_condition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_member_history_condition_outcome_coding_created_at'), 'family_member_history_condition_outcome_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_family_member_history_condition_outcome_coding_family_member_history_condition_id'), 'family_member_history_condition_outcome_coding', ['family_member_history_condition_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_condition_outcome_coding_tenant_id'), 'family_member_history_condition_outcome_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_condition_outcome_coding_updated_at'), 'family_member_history_condition_outcome_coding', ['updated_at'], unique=False)
    op.create_table('family_member_history_identifier_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('family_member_history_identifier_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['family_member_history_identifier_id'], ['family_member_history_identifier.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_member_history_identifier_type_coding_created_at'), 'family_member_history_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_family_member_history_identifier_type_coding_family_member_history_identifier_id'), 'family_member_history_identifier_type_coding', ['family_member_history_identifier_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_identifier_type_coding_tenant_id'), 'family_member_history_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_identifier_type_coding_updated_at'), 'family_member_history_identifier_type_coding', ['updated_at'], unique=False)
    op.create_table('family_member_history_reason_code_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('family_member_history_reason_code_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['family_member_history_reason_code_id'], ['family_member_history_reason_code.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_family_member_history_reason_code_coding_created_at'), 'family_member_history_reason_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_family_member_history_reason_code_coding_family_member_history_reason_code_id'), 'family_member_history_reason_code_coding', ['family_member_history_reason_code_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_reason_code_coding_tenant_id'), 'family_member_history_reason_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_family_member_history_reason_code_coding_updated_at'), 'family_member_history_reason_code_coding', ['updated_at'], unique=False)


def downgrade() -> None:
    # Drop grandchild tables
    op.drop_table('family_member_history_reason_code_coding')
    op.drop_table('family_member_history_identifier_type_coding')
    op.drop_table('family_member_history_condition_outcome_coding')
    op.drop_table('family_member_history_condition_note')
    op.drop_table('family_member_history_condition_code_coding')

    # Drop child tables
    op.drop_table('family_member_history_sex_coding')
    op.drop_table('family_member_history_relationship_coding')
    op.drop_table('family_member_history_reason_reference')
    op.drop_table('family_member_history_reason_code')
    op.drop_table('family_member_history_note')
    op.drop_table('family_member_history_identifier')
    op.drop_table('family_member_history_data_absent_reason_coding')
    op.drop_table('family_member_history_condition')

    # Drop main table
    op.drop_table('family_member_history')

    # Drop sequence
    op.execute('DROP SEQUENCE IF EXISTS family_member_history_pub_seq')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS family_member_history_note_author_reference_type')
    op.execute('DROP TYPE IF EXISTS family_member_history_reason_reference_type')
    op.execute('DROP TYPE IF EXISTS family_member_history_quantity_comparator')
    op.execute('DROP TYPE IF EXISTS family_member_history_patient_reference_type')
    op.execute('DROP TYPE IF EXISTS family_member_history_status')
