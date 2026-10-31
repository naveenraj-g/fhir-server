"""add_observation_definition_tables

Revision ID: 21e305b60db9
Revises: ee2a42a23151
Create Date: 2026-10-30 22:08:12.008035

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '21e305b60db9'
down_revision: Union[str, None] = 'ee2a42a23151'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Enum types ─────────────────────────────────────────────────────────────
    op.execute("CREATE TYPE observation_definition_permitted_data_type AS ENUM ('Quantity', 'CodeableConcept', 'string', 'boolean', 'integer', 'Range', 'Ratio', 'SampledData', 'time', 'dateTime', 'Period')")
    op.execute("CREATE TYPE observation_definition_gender AS ENUM ('male', 'female', 'other', 'unknown')")
    op.execute("CREATE TYPE observation_definition_qualified_interval_category AS ENUM ('reference', 'critical', 'absolute')")
    op.execute("CREATE TYPE observation_definition_value_set_reference_type AS ENUM ('ValueSet')")

    # ── Public sequence ────────────────────────────────────────────────────────
    op.execute("CREATE SEQUENCE IF NOT EXISTS observation_definition_pub_seq START 400000 INCREMENT 1")

    # ── 1. observation_definition (main table) ─────────────────────────────────
    op.create_table(
        'observation_definition',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('observation_definition_id', sa.BigInteger(), server_default=sa.text("nextval('observation_definition_pub_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
        sa.Column('code_text', sa.String(), nullable=True),
        sa.Column('permitted_data_type', postgresql.ARRAY(postgresql.ENUM('Quantity', 'CodeableConcept', 'string', 'boolean', 'integer', 'Range', 'Ratio', 'SampledData', 'time', 'dateTime', 'Period', name='observation_definition_permitted_data_type', create_type=False)), nullable=True),
        sa.Column('multiple_results_allowed', sa.Boolean(), nullable=True),
        sa.Column('method_text', sa.String(), nullable=True),
        sa.Column('preferred_report_name', sa.String(), nullable=True),
        sa.Column('quantitative_details_customary_unit_text', sa.String(), nullable=True),
        sa.Column('quantitative_details_unit_text', sa.String(), nullable=True),
        sa.Column('quantitative_details_conversion_factor', sa.Numeric(), nullable=True),
        sa.Column('quantitative_details_decimal_precision', sa.Integer(), nullable=True),
        sa.Column('valid_coded_value_set_reference', sa.String(), nullable=True),
        sa.Column('valid_coded_value_set_type', postgresql.ENUM('ValueSet', name='observation_definition_value_set_reference_type', create_type=False), nullable=True),
        sa.Column('valid_coded_value_set_id', sa.BigInteger(), nullable=True),
        sa.Column('valid_coded_value_set_display', sa.String(), nullable=True),
        sa.Column('normal_coded_value_set_reference', sa.String(), nullable=True),
        sa.Column('normal_coded_value_set_type', postgresql.ENUM('ValueSet', name='observation_definition_value_set_reference_type', create_type=False), nullable=True),
        sa.Column('normal_coded_value_set_id', sa.BigInteger(), nullable=True),
        sa.Column('normal_coded_value_set_display', sa.String(), nullable=True),
        sa.Column('abnormal_coded_value_set_reference', sa.String(), nullable=True),
        sa.Column('abnormal_coded_value_set_type', postgresql.ENUM('ValueSet', name='observation_definition_value_set_reference_type', create_type=False), nullable=True),
        sa.Column('abnormal_coded_value_set_id', sa.BigInteger(), nullable=True),
        sa.Column('abnormal_coded_value_set_display', sa.String(), nullable=True),
        sa.Column('critical_coded_value_set_reference', sa.String(), nullable=True),
        sa.Column('critical_coded_value_set_type', postgresql.ENUM('ValueSet', name='observation_definition_value_set_reference_type', create_type=False), nullable=True),
        sa.Column('critical_coded_value_set_id', sa.BigInteger(), nullable=True),
        sa.Column('critical_coded_value_set_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('observation_definition_id'),
    )
    op.create_index(op.f('ix_observation_definition_observation_definition_id'), 'observation_definition', ['observation_definition_id'], unique=True)
    op.create_index(op.f('ix_observation_definition_id'), 'observation_definition', ['id'], unique=False)
    op.create_index(op.f('ix_observation_definition_user_id'), 'observation_definition', ['user_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_tenant_id'), 'observation_definition', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_valid_coded_value_set_id'), 'observation_definition', ['valid_coded_value_set_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_normal_coded_value_set_id'), 'observation_definition', ['normal_coded_value_set_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_abnormal_coded_value_set_id'), 'observation_definition', ['abnormal_coded_value_set_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_critical_coded_value_set_id'), 'observation_definition', ['critical_coded_value_set_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_created_at'), 'observation_definition', ['created_at'], unique=False)
    op.create_index(op.f('ix_observation_definition_updated_at'), 'observation_definition', ['updated_at'], unique=False)

    # ── 2. observation_definition_identifier ───────────────────────────────────
    op.create_table(
        'observation_definition_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('observation_definition_pk', sa.BigInteger(), nullable=False),
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
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['observation_definition_pk'], ['observation_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_definition_identifier_observation_definition_pk'), 'observation_definition_identifier', ['observation_definition_pk'], unique=False)
    op.create_index(op.f('ix_observation_definition_identifier_assigner_id'), 'observation_definition_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_identifier_tenant_id'), 'observation_definition_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_identifier_created_at'), 'observation_definition_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_observation_definition_identifier_updated_at'), 'observation_definition_identifier', ['updated_at'], unique=False)

    # ── 3. observation_definition_identifier_type_coding ───────────────────────
    op.create_table(
        'observation_definition_identifier_type_coding',
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
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['identifier_id'], ['observation_definition_identifier.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_definition_identifier_type_coding_identifier_id'), 'observation_definition_identifier_type_coding', ['identifier_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_identifier_type_coding_tenant_id'), 'observation_definition_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_identifier_type_coding_created_at'), 'observation_definition_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_observation_definition_identifier_type_coding_updated_at'), 'observation_definition_identifier_type_coding', ['updated_at'], unique=False)

    # ── 4. observation_definition_category ─────────────────────────────────────
    op.create_table(
        'observation_definition_category',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('observation_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['observation_definition_pk'], ['observation_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_definition_category_observation_definition_pk'), 'observation_definition_category', ['observation_definition_pk'], unique=False)
    op.create_index(op.f('ix_observation_definition_category_tenant_id'), 'observation_definition_category', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_category_created_at'), 'observation_definition_category', ['created_at'], unique=False)
    op.create_index(op.f('ix_observation_definition_category_updated_at'), 'observation_definition_category', ['updated_at'], unique=False)

    # ── 5. observation_definition_category_coding ──────────────────────────────
    op.create_table(
        'observation_definition_category_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('category_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['observation_definition_category.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_definition_category_coding_category_id'), 'observation_definition_category_coding', ['category_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_category_coding_tenant_id'), 'observation_definition_category_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_category_coding_created_at'), 'observation_definition_category_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_observation_definition_category_coding_updated_at'), 'observation_definition_category_coding', ['updated_at'], unique=False)

    # ── 6. observation_definition_code_coding ──────────────────────────────────
    op.create_table(
        'observation_definition_code_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('observation_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['observation_definition_pk'], ['observation_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_definition_code_coding_observation_definition_pk'), 'observation_definition_code_coding', ['observation_definition_pk'], unique=False)
    op.create_index(op.f('ix_observation_definition_code_coding_tenant_id'), 'observation_definition_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_code_coding_created_at'), 'observation_definition_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_observation_definition_code_coding_updated_at'), 'observation_definition_code_coding', ['updated_at'], unique=False)

    # ── 7. observation_definition_method_coding ────────────────────────────────
    op.create_table(
        'observation_definition_method_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('observation_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['observation_definition_pk'], ['observation_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_definition_method_coding_observation_definition_pk'), 'observation_definition_method_coding', ['observation_definition_pk'], unique=False)
    op.create_index(op.f('ix_observation_definition_method_coding_tenant_id'), 'observation_definition_method_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_method_coding_created_at'), 'observation_definition_method_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_observation_definition_method_coding_updated_at'), 'observation_definition_method_coding', ['updated_at'], unique=False)

    # ── 8. observation_definition_quantitative_details_customary_unit_coding ──
    op.create_table(
        'observation_definition_quantitative_details_customary_unit_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('observation_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['observation_definition_pk'], ['observation_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_definition_quantitative_details_customary_unit_coding_observation_definition_pk'), 'observation_definition_quantitative_details_customary_unit_coding', ['observation_definition_pk'], unique=False)
    op.create_index(op.f('ix_observation_definition_quantitative_details_customary_unit_coding_tenant_id'), 'observation_definition_quantitative_details_customary_unit_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_quantitative_details_customary_unit_coding_created_at'), 'observation_definition_quantitative_details_customary_unit_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_observation_definition_quantitative_details_customary_unit_coding_updated_at'), 'observation_definition_quantitative_details_customary_unit_coding', ['updated_at'], unique=False)

    # ── 9. observation_definition_quantitative_details_unit_coding ─────────────
    op.create_table(
        'observation_definition_quantitative_details_unit_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('observation_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['observation_definition_pk'], ['observation_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_definition_quantitative_details_unit_coding_observation_definition_pk'), 'observation_definition_quantitative_details_unit_coding', ['observation_definition_pk'], unique=False)
    op.create_index(op.f('ix_observation_definition_quantitative_details_unit_coding_tenant_id'), 'observation_definition_quantitative_details_unit_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_quantitative_details_unit_coding_created_at'), 'observation_definition_quantitative_details_unit_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_observation_definition_quantitative_details_unit_coding_updated_at'), 'observation_definition_quantitative_details_unit_coding', ['updated_at'], unique=False)

    # ── 10. observation_definition_qualified_interval ──────────────────────────
    op.create_table(
        'observation_definition_qualified_interval',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('observation_definition_pk', sa.BigInteger(), nullable=False),
        sa.Column('category', postgresql.ENUM('reference', 'critical', 'absolute', name='observation_definition_qualified_interval_category', create_type=False), nullable=True),
        sa.Column('range_low_value', sa.Numeric(), nullable=True),
        sa.Column('range_low_unit', sa.String(), nullable=True),
        sa.Column('range_low_system', sa.String(), nullable=True),
        sa.Column('range_low_code', sa.String(), nullable=True),
        sa.Column('range_high_value', sa.Numeric(), nullable=True),
        sa.Column('range_high_unit', sa.String(), nullable=True),
        sa.Column('range_high_system', sa.String(), nullable=True),
        sa.Column('range_high_code', sa.String(), nullable=True),
        sa.Column('context_text', sa.String(), nullable=True),
        sa.Column('gender', postgresql.ENUM('male', 'female', 'other', 'unknown', name='observation_definition_gender', create_type=False), nullable=True),
        sa.Column('age_low_value', sa.Numeric(), nullable=True),
        sa.Column('age_low_unit', sa.String(), nullable=True),
        sa.Column('age_low_system', sa.String(), nullable=True),
        sa.Column('age_low_code', sa.String(), nullable=True),
        sa.Column('age_high_value', sa.Numeric(), nullable=True),
        sa.Column('age_high_unit', sa.String(), nullable=True),
        sa.Column('age_high_system', sa.String(), nullable=True),
        sa.Column('age_high_code', sa.String(), nullable=True),
        sa.Column('gestational_age_low_value', sa.Numeric(), nullable=True),
        sa.Column('gestational_age_low_unit', sa.String(), nullable=True),
        sa.Column('gestational_age_low_system', sa.String(), nullable=True),
        sa.Column('gestational_age_low_code', sa.String(), nullable=True),
        sa.Column('gestational_age_high_value', sa.Numeric(), nullable=True),
        sa.Column('gestational_age_high_unit', sa.String(), nullable=True),
        sa.Column('gestational_age_high_system', sa.String(), nullable=True),
        sa.Column('gestational_age_high_code', sa.String(), nullable=True),
        sa.Column('condition', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['observation_definition_pk'], ['observation_definition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_definition_qualified_interval_observation_definition_pk'), 'observation_definition_qualified_interval', ['observation_definition_pk'], unique=False)
    op.create_index(op.f('ix_observation_definition_qualified_interval_tenant_id'), 'observation_definition_qualified_interval', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_qualified_interval_created_at'), 'observation_definition_qualified_interval', ['created_at'], unique=False)
    op.create_index(op.f('ix_observation_definition_qualified_interval_updated_at'), 'observation_definition_qualified_interval', ['updated_at'], unique=False)

    # ── 11. observation_definition_qualified_interval_context_coding ───────────
    op.create_table(
        'observation_definition_qualified_interval_context_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('qualified_interval_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['qualified_interval_id'], ['observation_definition_qualified_interval.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_definition_qualified_interval_context_coding_qualified_interval_id'), 'observation_definition_qualified_interval_context_coding', ['qualified_interval_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_qualified_interval_context_coding_tenant_id'), 'observation_definition_qualified_interval_context_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_qualified_interval_context_coding_created_at'), 'observation_definition_qualified_interval_context_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_observation_definition_qualified_interval_context_coding_updated_at'), 'observation_definition_qualified_interval_context_coding', ['updated_at'], unique=False)

    # ── 12. observation_definition_qualified_interval_applies_to ───────────────
    op.create_table(
        'observation_definition_qualified_interval_applies_to',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('qualified_interval_id', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['qualified_interval_id'], ['observation_definition_qualified_interval.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_definition_qualified_interval_applies_to_qualified_interval_id'), 'observation_definition_qualified_interval_applies_to', ['qualified_interval_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_qualified_interval_applies_to_tenant_id'), 'observation_definition_qualified_interval_applies_to', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_qualified_interval_applies_to_created_at'), 'observation_definition_qualified_interval_applies_to', ['created_at'], unique=False)
    op.create_index(op.f('ix_observation_definition_qualified_interval_applies_to_updated_at'), 'observation_definition_qualified_interval_applies_to', ['updated_at'], unique=False)

    # ── 13. observation_definition_qualified_interval_applies_to_coding ────────
    op.create_table(
        'observation_definition_qualified_interval_applies_to_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('applies_to_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['applies_to_id'], ['observation_definition_qualified_interval_applies_to.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_observation_definition_qualified_interval_applies_to_coding_applies_to_id'), 'observation_definition_qualified_interval_applies_to_coding', ['applies_to_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_qualified_interval_applies_to_coding_tenant_id'), 'observation_definition_qualified_interval_applies_to_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_observation_definition_qualified_interval_applies_to_coding_created_at'), 'observation_definition_qualified_interval_applies_to_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_observation_definition_qualified_interval_applies_to_coding_updated_at'), 'observation_definition_qualified_interval_applies_to_coding', ['updated_at'], unique=False)


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_table('observation_definition_qualified_interval_applies_to_coding')
    op.drop_table('observation_definition_qualified_interval_applies_to')
    op.drop_table('observation_definition_qualified_interval_context_coding')
    op.drop_table('observation_definition_qualified_interval')
    op.drop_table('observation_definition_quantitative_details_unit_coding')
    op.drop_table('observation_definition_quantitative_details_customary_unit_coding')
    op.drop_table('observation_definition_method_coding')
    op.drop_table('observation_definition_code_coding')
    op.drop_table('observation_definition_category_coding')
    op.drop_table('observation_definition_category')
    op.drop_table('observation_definition_identifier_type_coding')
    op.drop_table('observation_definition_identifier')
    op.drop_table('observation_definition')

    op.execute("DROP SEQUENCE IF EXISTS observation_definition_pub_seq")
    op.execute("DROP TYPE IF EXISTS observation_definition_value_set_reference_type")
    op.execute("DROP TYPE IF EXISTS observation_definition_qualified_interval_category")
    op.execute("DROP TYPE IF EXISTS observation_definition_gender")
    op.execute("DROP TYPE IF EXISTS observation_definition_permitted_data_type")
