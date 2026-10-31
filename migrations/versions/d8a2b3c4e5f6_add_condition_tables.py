"""add_condition_tables

Revision ID: d8a2b3c4e5f6
Revises: c7b8e1a90f12
Create Date: 2026-10-30 14:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd8a2b3c4e5f6'
down_revision: Union[str, None] = 'c7b8e1a90f12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE condition_quantity_comparator AS ENUM ('lt', 'le', 'ge', 'gt')")
    op.execute("CREATE TYPE condition_recorder_reference_type AS ENUM ('Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson')")
    op.execute("CREATE TYPE condition_asserter_reference_type AS ENUM ('Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson')")
    op.execute("CREATE TYPE condition_stage_assessment_reference_type AS ENUM ('ClinicalImpression', 'DiagnosticReport', 'Observation')")
    op.execute("CREATE TYPE condition_note_author_reference_type AS ENUM ('Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson', 'Organization')")
    op.execute("CREATE SEQUENCE IF NOT EXISTS condition_pub_seq START 120000 INCREMENT 1")

    # Main condition table
    op.create_table(
        'condition',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('condition_id', sa.BigInteger(), server_default=sa.text("nextval('condition_pub_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('clinical_status_text', sa.String(), nullable=True),
        sa.Column('verification_status_text', sa.String(), nullable=True),
        sa.Column('severity_text', sa.String(), nullable=True),
        sa.Column('code_text', sa.String(), nullable=True),
        # subject (1..1)
        sa.Column('subject_reference', sa.String(), nullable=False),
        sa.Column('subject_type', postgresql.ENUM('Patient', 'Group', name='subject_reference_type', create_type=False), nullable=False),
        sa.Column('subject_id', sa.BigInteger(), nullable=True),
        sa.Column('subject_display', sa.String(), nullable=True),
        sa.Column('subject_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('subject_identifier_system', sa.String(), nullable=True),
        sa.Column('subject_identifier_value', sa.String(), nullable=True),
        sa.Column('subject_identifier_type_text', sa.String(), nullable=True),
        # encounter (0..1)
        sa.Column('encounter_reference', sa.String(), nullable=True),
        sa.Column('encounter_type', postgresql.ENUM('Encounter', name='encounter_reference_type', create_type=False), nullable=True),
        sa.Column('encounter_id', sa.BigInteger(), nullable=True),
        sa.Column('encounter_display', sa.String(), nullable=True),
        sa.Column('encounter_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('encounter_identifier_system', sa.String(), nullable=True),
        sa.Column('encounter_identifier_value', sa.String(), nullable=True),
        sa.Column('encounter_identifier_type_text', sa.String(), nullable=True),
        # onset[x]
        sa.Column('onset_date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('onset_age_value', sa.Numeric(), nullable=True),
        sa.Column('onset_age_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='condition_quantity_comparator', create_type=False), nullable=True),
        sa.Column('onset_age_unit', sa.String(), nullable=True),
        sa.Column('onset_age_system', sa.String(), nullable=True),
        sa.Column('onset_age_code', sa.String(), nullable=True),
        sa.Column('onset_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('onset_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('onset_range_low_value', sa.Numeric(), nullable=True),
        sa.Column('onset_range_low_unit', sa.String(), nullable=True),
        sa.Column('onset_range_low_system', sa.String(), nullable=True),
        sa.Column('onset_range_low_code', sa.String(), nullable=True),
        sa.Column('onset_range_high_value', sa.Numeric(), nullable=True),
        sa.Column('onset_range_high_unit', sa.String(), nullable=True),
        sa.Column('onset_range_high_system', sa.String(), nullable=True),
        sa.Column('onset_range_high_code', sa.String(), nullable=True),
        sa.Column('onset_string', sa.String(), nullable=True),
        # abatement[x]
        sa.Column('abatement_date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('abatement_age_value', sa.Numeric(), nullable=True),
        sa.Column('abatement_age_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='condition_quantity_comparator', create_type=False), nullable=True),
        sa.Column('abatement_age_unit', sa.String(), nullable=True),
        sa.Column('abatement_age_system', sa.String(), nullable=True),
        sa.Column('abatement_age_code', sa.String(), nullable=True),
        sa.Column('abatement_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('abatement_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('abatement_range_low_value', sa.Numeric(), nullable=True),
        sa.Column('abatement_range_low_unit', sa.String(), nullable=True),
        sa.Column('abatement_range_low_system', sa.String(), nullable=True),
        sa.Column('abatement_range_low_code', sa.String(), nullable=True),
        sa.Column('abatement_range_high_value', sa.Numeric(), nullable=True),
        sa.Column('abatement_range_high_unit', sa.String(), nullable=True),
        sa.Column('abatement_range_high_system', sa.String(), nullable=True),
        sa.Column('abatement_range_high_code', sa.String(), nullable=True),
        sa.Column('abatement_string', sa.String(), nullable=True),
        # recordedDate
        sa.Column('recorded_date', sa.DateTime(timezone=True), nullable=True),
        # recorder
        sa.Column('recorder_reference', sa.String(), nullable=True),
        sa.Column('recorder_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson', name='condition_recorder_reference_type', create_type=False), nullable=True),
        sa.Column('recorder_id', sa.BigInteger(), nullable=True),
        sa.Column('recorder_display', sa.String(), nullable=True),
        sa.Column('recorder_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('recorder_identifier_system', sa.String(), nullable=True),
        sa.Column('recorder_identifier_value', sa.String(), nullable=True),
        sa.Column('recorder_identifier_type_text', sa.String(), nullable=True),
        # asserter
        sa.Column('asserter_reference', sa.String(), nullable=True),
        sa.Column('asserter_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson', name='condition_asserter_reference_type', create_type=False), nullable=True),
        sa.Column('asserter_id', sa.BigInteger(), nullable=True),
        sa.Column('asserter_display', sa.String(), nullable=True),
        sa.Column('asserter_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('asserter_identifier_system', sa.String(), nullable=True),
        sa.Column('asserter_identifier_value', sa.String(), nullable=True),
        sa.Column('asserter_identifier_type_text', sa.String(), nullable=True),
        # condition identifier fallback
        sa.Column('identifier_system', sa.String(), nullable=True),
        sa.Column('identifier_value', sa.String(), nullable=True),
        sa.Column('identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('identifier_type_text', sa.String(), nullable=True),
        # domain resource extension
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
        # tenant audit
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('condition_id')
    )
    op.create_index(op.f('ix_condition_id'), 'condition', ['id'], unique=False)
    op.create_index(op.f('ix_condition_condition_id'), 'condition', ['condition_id'], unique=True)
    op.create_index(op.f('ix_condition_user_id'), 'condition', ['user_id'], unique=False)
    op.create_index(op.f('ix_condition_subject_id'), 'condition', ['subject_id'], unique=False)
    op.create_index(op.f('ix_condition_encounter_id'), 'condition', ['encounter_id'], unique=False)
    op.create_index(op.f('ix_condition_recorder_id'), 'condition', ['recorder_id'], unique=False)
    op.create_index(op.f('ix_condition_asserter_id'), 'condition', ['asserter_id'], unique=False)

    # condition_identifier
    op.create_table(
        'condition_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('condition_pk', sa.BigInteger(), nullable=False),
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
        sa.Column('assigner_identifier_system', sa.String(), nullable=True),
        sa.Column('assigner_identifier_value', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['condition_pk'], ['condition.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_condition_identifier_condition_pk'), 'condition_identifier', ['condition_pk'], unique=False)
    op.create_index(op.f('ix_condition_identifier_assigner_id'), 'condition_identifier', ['assigner_id'], unique=False)

    # condition_identifier_type_coding
    op.create_table(
        'condition_identifier_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('condition_identifier_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['condition_identifier_id'], ['condition_identifier.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_condition_identifier_type_coding_condition_identifier_id'), 'condition_identifier_type_coding', ['condition_identifier_id'], unique=False)

    # condition_clinical_status_coding
    op.create_table(
        'condition_clinical_status_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('condition_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['condition_pk'], ['condition.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_condition_clinical_status_coding_condition_pk'), 'condition_clinical_status_coding', ['condition_pk'], unique=False)

    # condition_verification_status_coding
    op.create_table(
        'condition_verification_status_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('condition_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['condition_pk'], ['condition.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_condition_verification_status_coding_condition_pk'), 'condition_verification_status_coding', ['condition_pk'], unique=False)

    # condition_category
    op.create_table(
        'condition_category',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('condition_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['condition_pk'], ['condition.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_condition_category_condition_pk'), 'condition_category', ['condition_pk'], unique=False)

    # condition_category_coding
    op.create_table(
        'condition_category_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('condition_category_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['condition_category_id'], ['condition_category.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_condition_category_coding_condition_category_id'), 'condition_category_coding', ['condition_category_id'], unique=False)

    # condition_severity_coding
    op.create_table(
        'condition_severity_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('condition_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['condition_pk'], ['condition.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_condition_severity_coding_condition_pk'), 'condition_severity_coding', ['condition_pk'], unique=False)

    # condition_code_coding
    op.create_table(
        'condition_code_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('condition_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['condition_pk'], ['condition.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_condition_code_coding_condition_pk'), 'condition_code_coding', ['condition_pk'], unique=False)

    # condition_body_site
    op.create_table(
        'condition_body_site',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('condition_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['condition_pk'], ['condition.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_condition_body_site_condition_pk'), 'condition_body_site', ['condition_pk'], unique=False)

    # condition_body_site_coding
    op.create_table(
        'condition_body_site_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('condition_body_site_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['condition_body_site_id'], ['condition_body_site.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_condition_body_site_coding_condition_body_site_id'), 'condition_body_site_coding', ['condition_body_site_id'], unique=False)

    # condition_stage
    op.create_table(
        'condition_stage',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('condition_pk', sa.BigInteger(), nullable=False),
        sa.Column('summary_text', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['condition_pk'], ['condition.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_condition_stage_condition_pk'), 'condition_stage', ['condition_pk'], unique=False)

    # condition_stage_summary_coding
    op.create_table(
        'condition_stage_summary_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('condition_stage_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['condition_stage_id'], ['condition_stage.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_condition_stage_summary_coding_condition_stage_id'), 'condition_stage_summary_coding', ['condition_stage_id'], unique=False)

    # condition_stage_type_coding
    op.create_table(
        'condition_stage_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('condition_stage_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['condition_stage_id'], ['condition_stage.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_condition_stage_type_coding_condition_stage_id'), 'condition_stage_type_coding', ['condition_stage_id'], unique=False)

    # condition_stage_assessment
    op.create_table(
        'condition_stage_assessment',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('condition_stage_id', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('ClinicalImpression', 'DiagnosticReport', 'Observation', name='condition_stage_assessment_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('reference_identifier_system', sa.String(), nullable=True),
        sa.Column('reference_identifier_value', sa.String(), nullable=True),
        sa.Column('reference_identifier_type_text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['condition_stage_id'], ['condition_stage.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_condition_stage_assessment_condition_stage_id'), 'condition_stage_assessment', ['condition_stage_id'], unique=False)
    op.create_index(op.f('ix_condition_stage_assessment_reference_id'), 'condition_stage_assessment', ['reference_id'], unique=False)

    # condition_evidence
    op.create_table(
        'condition_evidence',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('condition_pk', sa.BigInteger(), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['condition_pk'], ['condition.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_condition_evidence_condition_pk'), 'condition_evidence', ['condition_pk'], unique=False)

    # condition_evidence_code
    op.create_table(
        'condition_evidence_code',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('condition_evidence_id', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['condition_evidence_id'], ['condition_evidence.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_condition_evidence_code_condition_evidence_id'), 'condition_evidence_code', ['condition_evidence_id'], unique=False)

    # condition_evidence_code_coding
    op.create_table(
        'condition_evidence_code_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('condition_evidence_code_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['condition_evidence_code_id'], ['condition_evidence_code.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_condition_evidence_code_coding_condition_evidence_code_id'), 'condition_evidence_code_coding', ['condition_evidence_code_id'], unique=False)

    # condition_evidence_detail
    op.create_table(
        'condition_evidence_detail',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('condition_evidence_id', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('reference_identifier_system', sa.String(), nullable=True),
        sa.Column('reference_identifier_value', sa.String(), nullable=True),
        sa.Column('reference_identifier_type_text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['condition_evidence_id'], ['condition_evidence.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_condition_evidence_detail_condition_evidence_id'), 'condition_evidence_detail', ['condition_evidence_id'], unique=False)
    op.create_index(op.f('ix_condition_evidence_detail_reference_id'), 'condition_evidence_detail', ['reference_id'], unique=False)

    # condition_note
    op.create_table(
        'condition_note',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('condition_pk', sa.BigInteger(), nullable=False),
        sa.Column('author_string', sa.String(), nullable=True),
        sa.Column('author_reference', sa.String(), nullable=True),
        sa.Column('author_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson', 'Organization', name='condition_note_author_reference_type', create_type=False), nullable=True),
        sa.Column('author_id', sa.BigInteger(), nullable=True),
        sa.Column('author_display', sa.String(), nullable=True),
        sa.Column('author_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('author_identifier_system', sa.String(), nullable=True),
        sa.Column('author_identifier_value', sa.String(), nullable=True),
        sa.Column('author_identifier_type_text', sa.String(), nullable=True),
        sa.Column('time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['condition_pk'], ['condition.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_condition_note_condition_pk'), 'condition_note', ['condition_pk'], unique=False)
    op.create_index(op.f('ix_condition_note_author_id'), 'condition_note', ['author_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_condition_note_author_id'), table_name='condition_note')
    op.drop_index(op.f('ix_condition_note_condition_pk'), table_name='condition_note')
    op.drop_table('condition_note')

    op.drop_index(op.f('ix_condition_evidence_detail_reference_id'), table_name='condition_evidence_detail')
    op.drop_index(op.f('ix_condition_evidence_detail_condition_evidence_id'), table_name='condition_evidence_detail')
    op.drop_table('condition_evidence_detail')

    op.drop_index(op.f('ix_condition_evidence_code_coding_condition_evidence_code_id'), table_name='condition_evidence_code_coding')
    op.drop_table('condition_evidence_code_coding')

    op.drop_index(op.f('ix_condition_evidence_code_condition_evidence_id'), table_name='condition_evidence_code')
    op.drop_table('condition_evidence_code')

    op.drop_index(op.f('ix_condition_evidence_condition_pk'), table_name='condition_evidence')
    op.drop_table('condition_evidence')

    op.drop_index(op.f('ix_condition_stage_assessment_reference_id'), table_name='condition_stage_assessment')
    op.drop_index(op.f('ix_condition_stage_assessment_condition_stage_id'), table_name='condition_stage_assessment')
    op.drop_table('condition_stage_assessment')

    op.drop_index(op.f('ix_condition_stage_type_coding_condition_stage_id'), table_name='condition_stage_type_coding')
    op.drop_table('condition_stage_type_coding')

    op.drop_index(op.f('ix_condition_stage_summary_coding_condition_stage_id'), table_name='condition_stage_summary_coding')
    op.drop_table('condition_stage_summary_coding')

    op.drop_index(op.f('ix_condition_stage_condition_pk'), table_name='condition_stage')
    op.drop_table('condition_stage')

    op.drop_index(op.f('ix_condition_body_site_coding_condition_body_site_id'), table_name='condition_body_site_coding')
    op.drop_table('condition_body_site_coding')

    op.drop_index(op.f('ix_condition_body_site_condition_pk'), table_name='condition_body_site')
    op.drop_table('condition_body_site')

    op.drop_index(op.f('ix_condition_code_coding_condition_pk'), table_name='condition_code_coding')
    op.drop_table('condition_code_coding')

    op.drop_index(op.f('ix_condition_severity_coding_condition_pk'), table_name='condition_severity_coding')
    op.drop_table('condition_severity_coding')

    op.drop_index(op.f('ix_condition_category_coding_condition_category_id'), table_name='condition_category_coding')
    op.drop_table('condition_category_coding')

    op.drop_index(op.f('ix_condition_category_condition_pk'), table_name='condition_category')
    op.drop_table('condition_category')

    op.drop_index(op.f('ix_condition_verification_status_coding_condition_pk'), table_name='condition_verification_status_coding')
    op.drop_table('condition_verification_status_coding')

    op.drop_index(op.f('ix_condition_clinical_status_coding_condition_pk'), table_name='condition_clinical_status_coding')
    op.drop_table('condition_clinical_status_coding')

    op.drop_index(op.f('ix_condition_identifier_type_coding_condition_identifier_id'), table_name='condition_identifier_type_coding')
    op.drop_table('condition_identifier_type_coding')

    op.drop_index(op.f('ix_condition_identifier_assigner_id'), table_name='condition_identifier')
    op.drop_index(op.f('ix_condition_identifier_condition_pk'), table_name='condition_identifier')
    op.drop_table('condition_identifier')

    op.drop_index(op.f('ix_condition_asserter_id'), table_name='condition')
    op.drop_index(op.f('ix_condition_recorder_id'), table_name='condition')
    op.drop_index(op.f('ix_condition_encounter_id'), table_name='condition')
    op.drop_index(op.f('ix_condition_subject_id'), table_name='condition')
    op.drop_index(op.f('ix_condition_user_id'), table_name='condition')
    op.drop_index(op.f('ix_condition_condition_id'), table_name='condition')
    op.drop_index(op.f('ix_condition_id'), table_name='condition')
    op.drop_table('condition')

    op.execute("DROP SEQUENCE IF EXISTS condition_pub_seq")
    op.execute("DROP TYPE IF EXISTS condition_note_author_reference_type")
    op.execute("DROP TYPE IF EXISTS condition_stage_assessment_reference_type")
    op.execute("DROP TYPE IF EXISTS condition_asserter_reference_type")
    op.execute("DROP TYPE IF EXISTS condition_recorder_reference_type")
    op.execute("DROP TYPE IF EXISTS condition_quantity_comparator")
