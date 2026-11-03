"""add_medication_knowledge_tables

Revision ID: a95c0593c9e4
Revises: 2619de08a361
Create Date: 2026-11-03 15:30:53.199971

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a95c0593c9e4'
down_revision: Union[str, None] = '2619de08a361'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE medication_knowledge_ag_indication_ref_type AS ENUM ('ObservationDefinition')")
    op.execute("CREATE TYPE medication_knowledge_assoc_med_ref_type AS ENUM ('Medication')")
    op.execute("CREATE TYPE medication_knowledge_contraindication_ref_type AS ENUM ('DetectedIssue')")
    op.execute("CREATE TYPE medication_knowledge_ingredient_item_ref_type AS ENUM ('Substance', 'Medication')")
    op.execute("CREATE TYPE medication_knowledge_manufacturer_reference_type AS ENUM ('Organization')")
    op.execute("CREATE TYPE medication_knowledge_monograph_source_ref_type AS ENUM ('DocumentReference', 'Media')")
    op.execute("CREATE TYPE medication_knowledge_quantity_comparator AS ENUM ('lt', 'le', 'ge', 'gt')")
    op.execute("CREATE TYPE medication_knowledge_reg_auth_ref_type AS ENUM ('Organization')")
    op.execute("CREATE TYPE medication_knowledge_related_reference_type AS ENUM ('MedicationKnowledge')")
    op.execute("CREATE TYPE medication_knowledge_status AS ENUM ('active', 'inactive', 'entered-in-error')")
    op.execute('CREATE SEQUENCE IF NOT EXISTS medication_knowledge_pub_seq START WITH 600000 INCREMENT BY 1')
    op.create_table('medication_knowledge',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_id', sa.BigInteger(), nullable=False),
    sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
    sa.Column('code_text', sa.String(), nullable=True),
    sa.Column('status', postgresql.ENUM('active', 'inactive', 'entered-in-error', name='medication_knowledge_status', create_type=False), nullable=True),
    sa.Column('manufacturer_reference', sa.String(), nullable=True),
    sa.Column('manufacturer_type', postgresql.ENUM('Organization', name='medication_knowledge_manufacturer_reference_type', create_type=False), nullable=True),
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
    sa.Column('dose_form_text', sa.String(), nullable=True),
    sa.Column('amount_value', sa.Numeric(), nullable=True),
    sa.Column('amount_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='medication_knowledge_quantity_comparator', create_type=False), nullable=True),
    sa.Column('amount_unit', sa.String(), nullable=True),
    sa.Column('amount_system', sa.String(), nullable=True),
    sa.Column('amount_code', sa.String(), nullable=True),
    sa.Column('synonym', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('preparation_instruction', sa.Text(), nullable=True),
    sa.Column('packaging_type_text', sa.String(), nullable=True),
    sa.Column('packaging_quantity_value', sa.Numeric(), nullable=True),
    sa.Column('packaging_quantity_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='medication_knowledge_quantity_comparator', create_type=False), nullable=True),
    sa.Column('packaging_quantity_unit', sa.String(), nullable=True),
    sa.Column('packaging_quantity_system', sa.String(), nullable=True),
    sa.Column('packaging_quantity_code', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_created_at'), 'medication_knowledge', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_manufacturer_id'), 'medication_knowledge', ['manufacturer_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_medication_knowledge_id'), 'medication_knowledge', ['medication_knowledge_id'], unique=True)
    op.create_index(op.f('ix_medication_knowledge_tenant_id'), 'medication_knowledge', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_updated_at'), 'medication_knowledge', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_admin_guideline',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_pk', sa.BigInteger(), nullable=False),
    sa.Column('indication_codeable_concept_text', sa.String(), nullable=True),
    sa.Column('indication_reference', sa.String(), nullable=True),
    sa.Column('indication_type', postgresql.ENUM('ObservationDefinition', name='medication_knowledge_ag_indication_ref_type', create_type=False), nullable=True),
    sa.Column('indication_id', sa.BigInteger(), nullable=True),
    sa.Column('indication_display', sa.String(), nullable=True),
    sa.Column('indication_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('indication_identifier_type_system', sa.String(), nullable=True),
    sa.Column('indication_identifier_type_version', sa.String(), nullable=True),
    sa.Column('indication_identifier_type_code', sa.String(), nullable=True),
    sa.Column('indication_identifier_type_display', sa.String(), nullable=True),
    sa.Column('indication_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('indication_identifier_type_text', sa.String(), nullable=True),
    sa.Column('indication_identifier_system', sa.String(), nullable=True),
    sa.Column('indication_identifier_value', sa.String(), nullable=True),
    sa.Column('indication_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('indication_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_pk'], ['medication_knowledge.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_admin_guideline_created_at'), 'medication_knowledge_admin_guideline', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_admin_guideline_indication_id'), 'medication_knowledge_admin_guideline', ['indication_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_admin_guideline_medication_knowledge_pk'), 'medication_knowledge_admin_guideline', ['medication_knowledge_pk'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_admin_guideline_tenant_id'), 'medication_knowledge_admin_guideline', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_admin_guideline_updated_at'), 'medication_knowledge_admin_guideline', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_associated_medication',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('Medication', name='medication_knowledge_assoc_med_ref_type', create_type=False), nullable=True),
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
    sa.ForeignKeyConstraint(['medication_knowledge_pk'], ['medication_knowledge.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_associated_medication_created_at'), 'medication_knowledge_associated_medication', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_associated_medication_medication_knowledge_pk'), 'medication_knowledge_associated_medication', ['medication_knowledge_pk'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_associated_medication_reference_id'), 'medication_knowledge_associated_medication', ['reference_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_associated_medication_tenant_id'), 'medication_knowledge_associated_medication', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_associated_medication_updated_at'), 'medication_knowledge_associated_medication', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_code_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_pk', sa.BigInteger(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('display', sa.String(), nullable=True),
    sa.Column('user_selected', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_pk'], ['medication_knowledge.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_code_coding_created_at'), 'medication_knowledge_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_code_coding_medication_knowledge_pk'), 'medication_knowledge_code_coding', ['medication_knowledge_pk'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_code_coding_tenant_id'), 'medication_knowledge_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_code_coding_updated_at'), 'medication_knowledge_code_coding', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_contraindication',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('DetectedIssue', name='medication_knowledge_contraindication_ref_type', create_type=False), nullable=True),
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
    sa.ForeignKeyConstraint(['medication_knowledge_pk'], ['medication_knowledge.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_contraindication_created_at'), 'medication_knowledge_contraindication', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_contraindication_medication_knowledge_pk'), 'medication_knowledge_contraindication', ['medication_knowledge_pk'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_contraindication_reference_id'), 'medication_knowledge_contraindication', ['reference_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_contraindication_tenant_id'), 'medication_knowledge_contraindication', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_contraindication_updated_at'), 'medication_knowledge_contraindication', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_cost',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_pk', sa.BigInteger(), nullable=False),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('source', sa.String(), nullable=True),
    sa.Column('cost_value', sa.Numeric(), nullable=True),
    sa.Column('cost_currency', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_pk'], ['medication_knowledge.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_cost_created_at'), 'medication_knowledge_cost', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_cost_medication_knowledge_pk'), 'medication_knowledge_cost', ['medication_knowledge_pk'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_cost_tenant_id'), 'medication_knowledge_cost', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_cost_updated_at'), 'medication_knowledge_cost', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_dose_form_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_pk', sa.BigInteger(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('display', sa.String(), nullable=True),
    sa.Column('user_selected', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_pk'], ['medication_knowledge.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_dose_form_coding_created_at'), 'medication_knowledge_dose_form_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_dose_form_coding_medication_knowledge_pk'), 'medication_knowledge_dose_form_coding', ['medication_knowledge_pk'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_dose_form_coding_tenant_id'), 'medication_knowledge_dose_form_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_dose_form_coding_updated_at'), 'medication_knowledge_dose_form_coding', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_drug_characteristic',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_pk', sa.BigInteger(), nullable=False),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('value_codeable_concept_text', sa.String(), nullable=True),
    sa.Column('value_string', sa.String(), nullable=True),
    sa.Column('value_quantity_value', sa.Numeric(), nullable=True),
    sa.Column('value_quantity_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='medication_knowledge_quantity_comparator', create_type=False), nullable=True),
    sa.Column('value_quantity_unit', sa.String(), nullable=True),
    sa.Column('value_quantity_system', sa.String(), nullable=True),
    sa.Column('value_quantity_code', sa.String(), nullable=True),
    sa.Column('value_base64_binary', sa.Text(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_pk'], ['medication_knowledge.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_drug_characteristic_created_at'), 'medication_knowledge_drug_characteristic', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_drug_characteristic_medication_knowledge_pk'), 'medication_knowledge_drug_characteristic', ['medication_knowledge_pk'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_drug_characteristic_tenant_id'), 'medication_knowledge_drug_characteristic', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_drug_characteristic_updated_at'), 'medication_knowledge_drug_characteristic', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_ingredient',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_pk', sa.BigInteger(), nullable=False),
    sa.Column('item_codeable_concept_text', sa.String(), nullable=True),
    sa.Column('item_reference', sa.String(), nullable=True),
    sa.Column('item_type', postgresql.ENUM('Substance', 'Medication', name='medication_knowledge_ingredient_item_ref_type', create_type=False), nullable=True),
    sa.Column('item_id', sa.BigInteger(), nullable=True),
    sa.Column('item_display', sa.String(), nullable=True),
    sa.Column('item_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('item_identifier_type_system', sa.String(), nullable=True),
    sa.Column('item_identifier_type_version', sa.String(), nullable=True),
    sa.Column('item_identifier_type_code', sa.String(), nullable=True),
    sa.Column('item_identifier_type_display', sa.String(), nullable=True),
    sa.Column('item_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('item_identifier_type_text', sa.String(), nullable=True),
    sa.Column('item_identifier_system', sa.String(), nullable=True),
    sa.Column('item_identifier_value', sa.String(), nullable=True),
    sa.Column('item_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('item_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('strength_numerator_value', sa.Numeric(), nullable=True),
    sa.Column('strength_numerator_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='medication_knowledge_quantity_comparator', create_type=False), nullable=True),
    sa.Column('strength_numerator_unit', sa.String(), nullable=True),
    sa.Column('strength_numerator_system', sa.String(), nullable=True),
    sa.Column('strength_numerator_code', sa.String(), nullable=True),
    sa.Column('strength_denominator_value', sa.Numeric(), nullable=True),
    sa.Column('strength_denominator_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='medication_knowledge_quantity_comparator', create_type=False), nullable=True),
    sa.Column('strength_denominator_unit', sa.String(), nullable=True),
    sa.Column('strength_denominator_system', sa.String(), nullable=True),
    sa.Column('strength_denominator_code', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_pk'], ['medication_knowledge.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_ingredient_created_at'), 'medication_knowledge_ingredient', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_ingredient_item_id'), 'medication_knowledge_ingredient', ['item_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_ingredient_medication_knowledge_pk'), 'medication_knowledge_ingredient', ['medication_knowledge_pk'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_ingredient_tenant_id'), 'medication_knowledge_ingredient', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_ingredient_updated_at'), 'medication_knowledge_ingredient', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_intended_route',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_pk'], ['medication_knowledge.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_intended_route_created_at'), 'medication_knowledge_intended_route', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_intended_route_medication_knowledge_pk'), 'medication_knowledge_intended_route', ['medication_knowledge_pk'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_intended_route_tenant_id'), 'medication_knowledge_intended_route', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_intended_route_updated_at'), 'medication_knowledge_intended_route', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_kinetics',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_pk', sa.BigInteger(), nullable=False),
    sa.Column('half_life_period_value', sa.Numeric(), nullable=True),
    sa.Column('half_life_period_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='medication_knowledge_quantity_comparator', create_type=False), nullable=True),
    sa.Column('half_life_period_unit', sa.String(), nullable=True),
    sa.Column('half_life_period_system', sa.String(), nullable=True),
    sa.Column('half_life_period_code', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_pk'], ['medication_knowledge.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_kinetics_created_at'), 'medication_knowledge_kinetics', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_kinetics_medication_knowledge_pk'), 'medication_knowledge_kinetics', ['medication_knowledge_pk'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_kinetics_tenant_id'), 'medication_knowledge_kinetics', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_kinetics_updated_at'), 'medication_knowledge_kinetics', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_medicine_classification',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_pk', sa.BigInteger(), nullable=False),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_pk'], ['medication_knowledge.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_medicine_classification_created_at'), 'medication_knowledge_medicine_classification', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_medicine_classification_medication_knowledge_pk'), 'medication_knowledge_medicine_classification', ['medication_knowledge_pk'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_medicine_classification_tenant_id'), 'medication_knowledge_medicine_classification', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_medicine_classification_updated_at'), 'medication_knowledge_medicine_classification', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_monitoring_program',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_pk', sa.BigInteger(), nullable=False),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_pk'], ['medication_knowledge.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_monitoring_program_created_at'), 'medication_knowledge_monitoring_program', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_monitoring_program_medication_knowledge_pk'), 'medication_knowledge_monitoring_program', ['medication_knowledge_pk'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_monitoring_program_tenant_id'), 'medication_knowledge_monitoring_program', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_monitoring_program_updated_at'), 'medication_knowledge_monitoring_program', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_monograph',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_pk', sa.BigInteger(), nullable=False),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('source_reference', sa.String(), nullable=True),
    sa.Column('source_type', postgresql.ENUM('DocumentReference', 'Media', name='medication_knowledge_monograph_source_ref_type', create_type=False), nullable=True),
    sa.Column('source_id', sa.BigInteger(), nullable=True),
    sa.Column('source_display', sa.String(), nullable=True),
    sa.Column('source_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('source_identifier_type_system', sa.String(), nullable=True),
    sa.Column('source_identifier_type_version', sa.String(), nullable=True),
    sa.Column('source_identifier_type_code', sa.String(), nullable=True),
    sa.Column('source_identifier_type_display', sa.String(), nullable=True),
    sa.Column('source_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('source_identifier_type_text', sa.String(), nullable=True),
    sa.Column('source_identifier_system', sa.String(), nullable=True),
    sa.Column('source_identifier_value', sa.String(), nullable=True),
    sa.Column('source_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('source_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_pk'], ['medication_knowledge.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_monograph_created_at'), 'medication_knowledge_monograph', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_monograph_medication_knowledge_pk'), 'medication_knowledge_monograph', ['medication_knowledge_pk'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_monograph_source_id'), 'medication_knowledge_monograph', ['source_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_monograph_tenant_id'), 'medication_knowledge_monograph', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_monograph_updated_at'), 'medication_knowledge_monograph', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_packaging_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_pk', sa.BigInteger(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('display', sa.String(), nullable=True),
    sa.Column('user_selected', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_pk'], ['medication_knowledge.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_packaging_type_coding_created_at'), 'medication_knowledge_packaging_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_packaging_type_coding_medication_knowledge_pk'), 'medication_knowledge_packaging_type_coding', ['medication_knowledge_pk'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_packaging_type_coding_tenant_id'), 'medication_knowledge_packaging_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_packaging_type_coding_updated_at'), 'medication_knowledge_packaging_type_coding', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_product_type',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_pk'], ['medication_knowledge.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_product_type_created_at'), 'medication_knowledge_product_type', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_product_type_medication_knowledge_pk'), 'medication_knowledge_product_type', ['medication_knowledge_pk'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_product_type_tenant_id'), 'medication_knowledge_product_type', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_product_type_updated_at'), 'medication_knowledge_product_type', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_regulatory',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_pk', sa.BigInteger(), nullable=False),
    sa.Column('regulatory_authority_reference', sa.String(), nullable=True),
    sa.Column('regulatory_authority_type', postgresql.ENUM('Organization', name='medication_knowledge_reg_auth_ref_type', create_type=False), nullable=True),
    sa.Column('regulatory_authority_id', sa.BigInteger(), nullable=True),
    sa.Column('regulatory_authority_display', sa.String(), nullable=True),
    sa.Column('regulatory_authority_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('regulatory_authority_identifier_type_system', sa.String(), nullable=True),
    sa.Column('regulatory_authority_identifier_type_version', sa.String(), nullable=True),
    sa.Column('regulatory_authority_identifier_type_code', sa.String(), nullable=True),
    sa.Column('regulatory_authority_identifier_type_display', sa.String(), nullable=True),
    sa.Column('regulatory_authority_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('regulatory_authority_identifier_type_text', sa.String(), nullable=True),
    sa.Column('regulatory_authority_identifier_system', sa.String(), nullable=True),
    sa.Column('regulatory_authority_identifier_value', sa.String(), nullable=True),
    sa.Column('regulatory_authority_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('regulatory_authority_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('max_dispense_quantity_value', sa.Numeric(), nullable=True),
    sa.Column('max_dispense_quantity_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='medication_knowledge_quantity_comparator', create_type=False), nullable=True),
    sa.Column('max_dispense_quantity_unit', sa.String(), nullable=True),
    sa.Column('max_dispense_quantity_system', sa.String(), nullable=True),
    sa.Column('max_dispense_quantity_code', sa.String(), nullable=True),
    sa.Column('max_dispense_period_value', sa.Numeric(), nullable=True),
    sa.Column('max_dispense_period_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='medication_knowledge_quantity_comparator', create_type=False), nullable=True),
    sa.Column('max_dispense_period_unit', sa.String(), nullable=True),
    sa.Column('max_dispense_period_system', sa.String(), nullable=True),
    sa.Column('max_dispense_period_code', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_pk'], ['medication_knowledge.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_regulatory_created_at'), 'medication_knowledge_regulatory', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_regulatory_medication_knowledge_pk'), 'medication_knowledge_regulatory', ['medication_knowledge_pk'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_regulatory_regulatory_authority_id'), 'medication_knowledge_regulatory', ['regulatory_authority_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_regulatory_tenant_id'), 'medication_knowledge_regulatory', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_regulatory_updated_at'), 'medication_knowledge_regulatory', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_related',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_pk', sa.BigInteger(), nullable=False),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_pk'], ['medication_knowledge.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_related_created_at'), 'medication_knowledge_related', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_related_medication_knowledge_pk'), 'medication_knowledge_related', ['medication_knowledge_pk'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_related_tenant_id'), 'medication_knowledge_related', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_related_updated_at'), 'medication_knowledge_related', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_ag_dosage',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_admin_guideline_id', sa.BigInteger(), nullable=False),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('dosage', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_admin_guideline_id'], ['medication_knowledge_admin_guideline.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_ag_dosage_created_at'), 'medication_knowledge_ag_dosage', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_ag_dosage_medication_knowledge_admin_guideline_id'), 'medication_knowledge_ag_dosage', ['medication_knowledge_admin_guideline_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_ag_dosage_tenant_id'), 'medication_knowledge_ag_dosage', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_ag_dosage_updated_at'), 'medication_knowledge_ag_dosage', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_ag_indication_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_admin_guideline_id', sa.BigInteger(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('display', sa.String(), nullable=True),
    sa.Column('user_selected', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_admin_guideline_id'], ['medication_knowledge_admin_guideline.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_ag_indication_coding_created_at'), 'medication_knowledge_ag_indication_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_ag_indication_coding_medication_knowledge_admin_guideline_id'), 'medication_knowledge_ag_indication_coding', ['medication_knowledge_admin_guideline_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_ag_indication_coding_tenant_id'), 'medication_knowledge_ag_indication_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_ag_indication_coding_updated_at'), 'medication_knowledge_ag_indication_coding', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_ag_patient_char',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_admin_guideline_id', sa.BigInteger(), nullable=False),
    sa.Column('characteristic_codeable_concept_text', sa.String(), nullable=True),
    sa.Column('characteristic_quantity_value', sa.Numeric(), nullable=True),
    sa.Column('characteristic_quantity_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='medication_knowledge_quantity_comparator', create_type=False), nullable=True),
    sa.Column('characteristic_quantity_unit', sa.String(), nullable=True),
    sa.Column('characteristic_quantity_system', sa.String(), nullable=True),
    sa.Column('characteristic_quantity_code', sa.String(), nullable=True),
    sa.Column('value', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_admin_guideline_id'], ['medication_knowledge_admin_guideline.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_ag_patient_char_created_at'), 'medication_knowledge_ag_patient_char', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_ag_patient_char_medication_knowledge_admin_guideline_id'), 'medication_knowledge_ag_patient_char', ['medication_knowledge_admin_guideline_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_ag_patient_char_tenant_id'), 'medication_knowledge_ag_patient_char', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_ag_patient_char_updated_at'), 'medication_knowledge_ag_patient_char', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_cost_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_cost_id', sa.BigInteger(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('display', sa.String(), nullable=True),
    sa.Column('user_selected', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_cost_id'], ['medication_knowledge_cost.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_cost_type_coding_created_at'), 'medication_knowledge_cost_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_cost_type_coding_medication_knowledge_cost_id'), 'medication_knowledge_cost_type_coding', ['medication_knowledge_cost_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_cost_type_coding_tenant_id'), 'medication_knowledge_cost_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_cost_type_coding_updated_at'), 'medication_knowledge_cost_type_coding', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_drug_char_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_drug_characteristic_id', sa.BigInteger(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('display', sa.String(), nullable=True),
    sa.Column('user_selected', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_drug_characteristic_id'], ['medication_knowledge_drug_characteristic.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_drug_char_type_coding_created_at'), 'medication_knowledge_drug_char_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_drug_char_type_coding_medication_knowledge_drug_characteristic_id'), 'medication_knowledge_drug_char_type_coding', ['medication_knowledge_drug_characteristic_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_drug_char_type_coding_tenant_id'), 'medication_knowledge_drug_char_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_drug_char_type_coding_updated_at'), 'medication_knowledge_drug_char_type_coding', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_drug_char_val_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_drug_characteristic_id', sa.BigInteger(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('display', sa.String(), nullable=True),
    sa.Column('user_selected', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_drug_characteristic_id'], ['medication_knowledge_drug_characteristic.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_drug_char_val_coding_created_at'), 'medication_knowledge_drug_char_val_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_drug_char_val_coding_medication_knowledge_drug_characteristic_id'), 'medication_knowledge_drug_char_val_coding', ['medication_knowledge_drug_characteristic_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_drug_char_val_coding_tenant_id'), 'medication_knowledge_drug_char_val_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_drug_char_val_coding_updated_at'), 'medication_knowledge_drug_char_val_coding', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_ingredient_item_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_ingredient_id', sa.BigInteger(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('display', sa.String(), nullable=True),
    sa.Column('user_selected', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_ingredient_id'], ['medication_knowledge_ingredient.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_ingredient_item_coding_created_at'), 'medication_knowledge_ingredient_item_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_ingredient_item_coding_medication_knowledge_ingredient_id'), 'medication_knowledge_ingredient_item_coding', ['medication_knowledge_ingredient_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_ingredient_item_coding_tenant_id'), 'medication_knowledge_ingredient_item_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_ingredient_item_coding_updated_at'), 'medication_knowledge_ingredient_item_coding', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_intended_route_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_intended_route_id', sa.BigInteger(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('display', sa.String(), nullable=True),
    sa.Column('user_selected', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_intended_route_id'], ['medication_knowledge_intended_route.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_intended_route_coding_created_at'), 'medication_knowledge_intended_route_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_intended_route_coding_medication_knowledge_intended_route_id'), 'medication_knowledge_intended_route_coding', ['medication_knowledge_intended_route_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_intended_route_coding_tenant_id'), 'medication_knowledge_intended_route_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_intended_route_coding_updated_at'), 'medication_knowledge_intended_route_coding', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_kinetics_auc',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_kinetics_id', sa.BigInteger(), nullable=False),
    sa.Column('value', sa.Numeric(), nullable=True),
    sa.Column('comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='medication_knowledge_quantity_comparator', create_type=False), nullable=True),
    sa.Column('unit', sa.String(), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_kinetics_id'], ['medication_knowledge_kinetics.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_kinetics_auc_created_at'), 'medication_knowledge_kinetics_auc', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_kinetics_auc_medication_knowledge_kinetics_id'), 'medication_knowledge_kinetics_auc', ['medication_knowledge_kinetics_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_kinetics_auc_tenant_id'), 'medication_knowledge_kinetics_auc', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_kinetics_auc_updated_at'), 'medication_knowledge_kinetics_auc', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_kinetics_ld50',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_kinetics_id', sa.BigInteger(), nullable=False),
    sa.Column('value', sa.Numeric(), nullable=True),
    sa.Column('comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='medication_knowledge_quantity_comparator', create_type=False), nullable=True),
    sa.Column('unit', sa.String(), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_kinetics_id'], ['medication_knowledge_kinetics.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_kinetics_ld50_created_at'), 'medication_knowledge_kinetics_ld50', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_kinetics_ld50_medication_knowledge_kinetics_id'), 'medication_knowledge_kinetics_ld50', ['medication_knowledge_kinetics_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_kinetics_ld50_tenant_id'), 'medication_knowledge_kinetics_ld50', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_kinetics_ld50_updated_at'), 'medication_knowledge_kinetics_ld50', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_med_class_item',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_medicine_classification_id', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_medicine_classification_id'], ['medication_knowledge_medicine_classification.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_med_class_item_created_at'), 'medication_knowledge_med_class_item', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_med_class_item_medication_knowledge_medicine_classification_id'), 'medication_knowledge_med_class_item', ['medication_knowledge_medicine_classification_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_med_class_item_tenant_id'), 'medication_knowledge_med_class_item', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_med_class_item_updated_at'), 'medication_knowledge_med_class_item', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_med_class_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_medicine_classification_id', sa.BigInteger(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('display', sa.String(), nullable=True),
    sa.Column('user_selected', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_medicine_classification_id'], ['medication_knowledge_medicine_classification.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_med_class_type_coding_created_at'), 'medication_knowledge_med_class_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_med_class_type_coding_medication_knowledge_medicine_classification_id'), 'medication_knowledge_med_class_type_coding', ['medication_knowledge_medicine_classification_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_med_class_type_coding_tenant_id'), 'medication_knowledge_med_class_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_med_class_type_coding_updated_at'), 'medication_knowledge_med_class_type_coding', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_monitoring_program_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_monitoring_program_id', sa.BigInteger(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('display', sa.String(), nullable=True),
    sa.Column('user_selected', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_monitoring_program_id'], ['medication_knowledge_monitoring_program.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_monitoring_program_type_coding_tenant_id'), 'medication_knowledge_monitoring_program_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_monitoring_program_type_coding_updated_at'), 'medication_knowledge_monitoring_program_type_coding', ['updated_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_monitoring_program_type_coding_medication_knowledge_monitoring_program_id'), 'medication_knowledge_monitoring_program_type_coding', ['medication_knowledge_monitoring_program_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_monitoring_program_type_coding_created_at'), 'medication_knowledge_monitoring_program_type_coding', ['created_at'], unique=False)
    op.create_table('medication_knowledge_monograph_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_monograph_id', sa.BigInteger(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('display', sa.String(), nullable=True),
    sa.Column('user_selected', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_monograph_id'], ['medication_knowledge_monograph.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_monograph_type_coding_created_at'), 'medication_knowledge_monograph_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_monograph_type_coding_medication_knowledge_monograph_id'), 'medication_knowledge_monograph_type_coding', ['medication_knowledge_monograph_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_monograph_type_coding_tenant_id'), 'medication_knowledge_monograph_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_monograph_type_coding_updated_at'), 'medication_knowledge_monograph_type_coding', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_product_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_product_type_id', sa.BigInteger(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('display', sa.String(), nullable=True),
    sa.Column('user_selected', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_product_type_id'], ['medication_knowledge_product_type.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_product_type_coding_created_at'), 'medication_knowledge_product_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_product_type_coding_medication_knowledge_product_type_id'), 'medication_knowledge_product_type_coding', ['medication_knowledge_product_type_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_product_type_coding_tenant_id'), 'medication_knowledge_product_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_product_type_coding_updated_at'), 'medication_knowledge_product_type_coding', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_reg_sched',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_regulatory_id', sa.BigInteger(), nullable=False),
    sa.Column('schedule_text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_regulatory_id'], ['medication_knowledge_regulatory.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_reg_sched_created_at'), 'medication_knowledge_reg_sched', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_reg_sched_medication_knowledge_regulatory_id'), 'medication_knowledge_reg_sched', ['medication_knowledge_regulatory_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_reg_sched_tenant_id'), 'medication_knowledge_reg_sched', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_reg_sched_updated_at'), 'medication_knowledge_reg_sched', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_reg_sub',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_regulatory_id', sa.BigInteger(), nullable=False),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('allowed', sa.Boolean(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_regulatory_id'], ['medication_knowledge_regulatory.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_reg_sub_created_at'), 'medication_knowledge_reg_sub', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_reg_sub_medication_knowledge_regulatory_id'), 'medication_knowledge_reg_sub', ['medication_knowledge_regulatory_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_reg_sub_tenant_id'), 'medication_knowledge_reg_sub', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_reg_sub_updated_at'), 'medication_knowledge_reg_sub', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_related_reference',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_related_id', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', postgresql.ENUM('MedicationKnowledge', name='medication_knowledge_related_reference_type', create_type=False), nullable=True),
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
    sa.ForeignKeyConstraint(['medication_knowledge_related_id'], ['medication_knowledge_related.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_related_reference_created_at'), 'medication_knowledge_related_reference', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_related_reference_medication_knowledge_related_id'), 'medication_knowledge_related_reference', ['medication_knowledge_related_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_related_reference_reference_id'), 'medication_knowledge_related_reference', ['reference_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_related_reference_tenant_id'), 'medication_knowledge_related_reference', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_related_reference_updated_at'), 'medication_knowledge_related_reference', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_related_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_related_id', sa.BigInteger(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('display', sa.String(), nullable=True),
    sa.Column('user_selected', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_related_id'], ['medication_knowledge_related.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_related_type_coding_created_at'), 'medication_knowledge_related_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_related_type_coding_medication_knowledge_related_id'), 'medication_knowledge_related_type_coding', ['medication_knowledge_related_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_related_type_coding_tenant_id'), 'medication_knowledge_related_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_related_type_coding_updated_at'), 'medication_knowledge_related_type_coding', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_ag_dosage_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_ag_dosage_id', sa.BigInteger(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('display', sa.String(), nullable=True),
    sa.Column('user_selected', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_ag_dosage_id'], ['medication_knowledge_ag_dosage.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_ag_dosage_type_coding_created_at'), 'medication_knowledge_ag_dosage_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_ag_dosage_type_coding_medication_knowledge_ag_dosage_id'), 'medication_knowledge_ag_dosage_type_coding', ['medication_knowledge_ag_dosage_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_ag_dosage_type_coding_tenant_id'), 'medication_knowledge_ag_dosage_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_ag_dosage_type_coding_updated_at'), 'medication_knowledge_ag_dosage_type_coding', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_ag_patient_char_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_ag_patient_char_id', sa.BigInteger(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('display', sa.String(), nullable=True),
    sa.Column('user_selected', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_ag_patient_char_id'], ['medication_knowledge_ag_patient_char.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_ag_patient_char_coding_created_at'), 'medication_knowledge_ag_patient_char_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_ag_patient_char_coding_medication_knowledge_ag_patient_char_id'), 'medication_knowledge_ag_patient_char_coding', ['medication_knowledge_ag_patient_char_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_ag_patient_char_coding_tenant_id'), 'medication_knowledge_ag_patient_char_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_ag_patient_char_coding_updated_at'), 'medication_knowledge_ag_patient_char_coding', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_med_class_item_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_med_class_item_id', sa.BigInteger(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('display', sa.String(), nullable=True),
    sa.Column('user_selected', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_med_class_item_id'], ['medication_knowledge_med_class_item.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_med_class_item_coding_created_at'), 'medication_knowledge_med_class_item_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_med_class_item_coding_medication_knowledge_med_class_item_id'), 'medication_knowledge_med_class_item_coding', ['medication_knowledge_med_class_item_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_med_class_item_coding_tenant_id'), 'medication_knowledge_med_class_item_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_med_class_item_coding_updated_at'), 'medication_knowledge_med_class_item_coding', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_reg_sched_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_reg_sched_id', sa.BigInteger(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('display', sa.String(), nullable=True),
    sa.Column('user_selected', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_reg_sched_id'], ['medication_knowledge_reg_sched.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_reg_sched_coding_created_at'), 'medication_knowledge_reg_sched_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_reg_sched_coding_medication_knowledge_reg_sched_id'), 'medication_knowledge_reg_sched_coding', ['medication_knowledge_reg_sched_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_reg_sched_coding_tenant_id'), 'medication_knowledge_reg_sched_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_reg_sched_coding_updated_at'), 'medication_knowledge_reg_sched_coding', ['updated_at'], unique=False)
    op.create_table('medication_knowledge_reg_sub_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('medication_knowledge_reg_sub_id', sa.BigInteger(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('code', sa.String(), nullable=True),
    sa.Column('display', sa.String(), nullable=True),
    sa.Column('user_selected', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['medication_knowledge_reg_sub_id'], ['medication_knowledge_reg_sub.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_knowledge_reg_sub_type_coding_created_at'), 'medication_knowledge_reg_sub_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_reg_sub_type_coding_medication_knowledge_reg_sub_id'), 'medication_knowledge_reg_sub_type_coding', ['medication_knowledge_reg_sub_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_reg_sub_type_coding_tenant_id'), 'medication_knowledge_reg_sub_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_knowledge_reg_sub_type_coding_updated_at'), 'medication_knowledge_reg_sub_type_coding', ['updated_at'], unique=False)
    op.drop_index(op.f('ix_observation_definition_quantitative_details_customar_5853'), table_name='observation_definition_quantitative_details_customary_unit_codi')


def downgrade() -> None:
    op.drop_table('medication_knowledge_reg_sub_type_coding')
    op.drop_table('medication_knowledge_reg_sched_coding')
    op.drop_table('medication_knowledge_med_class_item_coding')
    op.drop_table('medication_knowledge_ag_patient_char_coding')
    op.drop_table('medication_knowledge_ag_dosage_type_coding')
    op.drop_table('medication_knowledge_related_type_coding')
    op.drop_table('medication_knowledge_related_reference')
    op.drop_table('medication_knowledge_reg_sub')
    op.drop_table('medication_knowledge_reg_sched')
    op.drop_table('medication_knowledge_product_type_coding')
    op.drop_table('medication_knowledge_monograph_type_coding')
    op.drop_table('medication_knowledge_monitoring_program_type_coding')
    op.drop_table('medication_knowledge_med_class_type_coding')
    op.drop_table('medication_knowledge_med_class_item')
    op.drop_table('medication_knowledge_kinetics_ld50')
    op.drop_table('medication_knowledge_kinetics_auc')
    op.drop_table('medication_knowledge_intended_route_coding')
    op.drop_table('medication_knowledge_ingredient_item_coding')
    op.drop_table('medication_knowledge_drug_char_val_coding')
    op.drop_table('medication_knowledge_drug_char_type_coding')
    op.drop_table('medication_knowledge_cost_type_coding')
    op.drop_table('medication_knowledge_ag_patient_char')
    op.drop_table('medication_knowledge_ag_indication_coding')
    op.drop_table('medication_knowledge_ag_dosage')
    op.drop_table('medication_knowledge_related')
    op.drop_table('medication_knowledge_regulatory')
    op.drop_table('medication_knowledge_product_type')
    op.drop_table('medication_knowledge_packaging_type_coding')
    op.drop_table('medication_knowledge_monograph')
    op.drop_table('medication_knowledge_monitoring_program')
    op.drop_table('medication_knowledge_medicine_classification')
    op.drop_table('medication_knowledge_kinetics')
    op.drop_table('medication_knowledge_intended_route')
    op.drop_table('medication_knowledge_ingredient')
    op.drop_table('medication_knowledge_drug_characteristic')
    op.drop_table('medication_knowledge_dose_form_coding')
    op.drop_table('medication_knowledge_cost')
    op.drop_table('medication_knowledge_contraindication')
    op.drop_table('medication_knowledge_code_coding')
    op.drop_table('medication_knowledge_associated_medication')
    op.drop_table('medication_knowledge_admin_guideline')
    op.drop_table('medication_knowledge')
    op.execute('DROP SEQUENCE IF EXISTS medication_knowledge_pub_seq')
    op.execute('DROP TYPE IF EXISTS medication_knowledge_status')
    op.execute('DROP TYPE IF EXISTS medication_knowledge_related_reference_type')
    op.execute('DROP TYPE IF EXISTS medication_knowledge_reg_auth_ref_type')
    op.execute('DROP TYPE IF EXISTS medication_knowledge_quantity_comparator')
    op.execute('DROP TYPE IF EXISTS medication_knowledge_monograph_source_ref_type')
    op.execute('DROP TYPE IF EXISTS medication_knowledge_manufacturer_reference_type')
    op.execute('DROP TYPE IF EXISTS medication_knowledge_ingredient_item_ref_type')
    op.execute('DROP TYPE IF EXISTS medication_knowledge_contraindication_ref_type')
    op.execute('DROP TYPE IF EXISTS medication_knowledge_assoc_med_ref_type')
    op.execute('DROP TYPE IF EXISTS medication_knowledge_ag_indication_ref_type')
