"""add_medication_tables

Revision ID: 2619de08a361
Revises: df4782485581
Create Date: 2026-11-03 14:37:38.825208

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2619de08a361'
down_revision: Union[str, None] = 'df4782485581'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE medication_identifier_assigner_reference_type AS ENUM ('Organization')")
    op.execute("CREATE TYPE medication_ingredient_item_reference_type AS ENUM ('Substance', 'Medication')")
    op.execute("CREATE TYPE medication_manufacturer_reference_type AS ENUM ('Organization')")
    op.execute("CREATE TYPE medication_quantity_comparator AS ENUM ('lt', 'le', 'ge', 'gt')")
    op.execute("CREATE TYPE medication_status AS ENUM ('active', 'inactive', 'entered-in-error')")
    op.execute('CREATE SEQUENCE IF NOT EXISTS medication_pub_seq START 250000 INCREMENT 1')

    # Main table
    op.create_table(
        'medication',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_id', sa.BigInteger(), nullable=False),
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
        sa.Column('code_text', sa.String(), nullable=True),
        sa.Column('status', postgresql.ENUM('active', 'inactive', 'entered-in-error', name='medication_status', create_type=False), nullable=True),
        sa.Column('manufacturer_reference', sa.String(), nullable=True),
        sa.Column('manufacturer_type', postgresql.ENUM('Organization', name='medication_manufacturer_reference_type', create_type=False), nullable=True),
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
        sa.Column('form_text', sa.String(), nullable=True),
        sa.Column('amount_numerator_value', sa.Numeric(), nullable=True),
        sa.Column('amount_numerator_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='medication_quantity_comparator', create_type=False), nullable=True),
        sa.Column('amount_numerator_unit', sa.String(), nullable=True),
        sa.Column('amount_numerator_system', sa.String(), nullable=True),
        sa.Column('amount_numerator_code', sa.String(), nullable=True),
        sa.Column('amount_denominator_value', sa.Numeric(), nullable=True),
        sa.Column('amount_denominator_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='medication_quantity_comparator', create_type=False), nullable=True),
        sa.Column('amount_denominator_unit', sa.String(), nullable=True),
        sa.Column('amount_denominator_system', sa.String(), nullable=True),
        sa.Column('amount_denominator_code', sa.String(), nullable=True),
        sa.Column('batch_lot_number', sa.String(), nullable=True),
        sa.Column('batch_expiration_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_created_at'), 'medication', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_manufacturer_id'), 'medication', ['manufacturer_id'], unique=False)
    op.create_index(op.f('ix_medication_medication_id'), 'medication', ['medication_id'], unique=True)
    op.create_index(op.f('ix_medication_tenant_id'), 'medication', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_updated_at'), 'medication', ['updated_at'], unique=False)

    # medication_code_coding
    op.create_table(
        'medication_code_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['medication_pk'], ['medication.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_code_coding_created_at'), 'medication_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_code_coding_medication_pk'), 'medication_code_coding', ['medication_pk'], unique=False)
    op.create_index(op.f('ix_medication_code_coding_tenant_id'), 'medication_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_code_coding_updated_at'), 'medication_code_coding', ['updated_at'], unique=False)

    # medication_form_coding
    op.create_table(
        'medication_form_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['medication_pk'], ['medication.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_form_coding_created_at'), 'medication_form_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_form_coding_medication_pk'), 'medication_form_coding', ['medication_pk'], unique=False)
    op.create_index(op.f('ix_medication_form_coding_tenant_id'), 'medication_form_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_form_coding_updated_at'), 'medication_form_coding', ['updated_at'], unique=False)

    # medication_identifier
    op.create_table(
        'medication_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_pk', sa.BigInteger(), nullable=False),
        sa.Column('use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigner_reference', sa.String(), nullable=True),
        sa.Column('assigner_type', postgresql.ENUM('Organization', name='medication_identifier_assigner_reference_type', create_type=False), nullable=True),
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
        sa.ForeignKeyConstraint(['medication_pk'], ['medication.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_identifier_assigner_id'), 'medication_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_medication_identifier_created_at'), 'medication_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_identifier_medication_pk'), 'medication_identifier', ['medication_pk'], unique=False)
    op.create_index(op.f('ix_medication_identifier_tenant_id'), 'medication_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_identifier_updated_at'), 'medication_identifier', ['updated_at'], unique=False)

    # medication_identifier_type_coding
    op.create_table(
        'medication_identifier_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_identifier_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['medication_identifier_id'], ['medication_identifier.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_identifier_type_coding_created_at'), 'medication_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_identifier_type_coding_medication_identifier_id'), 'medication_identifier_type_coding', ['medication_identifier_id'], unique=False)
    op.create_index(op.f('ix_medication_identifier_type_coding_tenant_id'), 'medication_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_identifier_type_coding_updated_at'), 'medication_identifier_type_coding', ['updated_at'], unique=False)

    # medication_ingredient
    op.create_table(
        'medication_ingredient',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_pk', sa.BigInteger(), nullable=False),
        sa.Column('item_codeable_concept_text', sa.String(), nullable=True),
        sa.Column('item_reference', sa.String(), nullable=True),
        sa.Column('item_type', postgresql.ENUM('Substance', 'Medication', name='medication_ingredient_item_reference_type', create_type=False), nullable=True),
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
        sa.Column('strength_numerator_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='medication_quantity_comparator', create_type=False), nullable=True),
        sa.Column('strength_numerator_unit', sa.String(), nullable=True),
        sa.Column('strength_numerator_system', sa.String(), nullable=True),
        sa.Column('strength_numerator_code', sa.String(), nullable=True),
        sa.Column('strength_denominator_value', sa.Numeric(), nullable=True),
        sa.Column('strength_denominator_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='medication_quantity_comparator', create_type=False), nullable=True),
        sa.Column('strength_denominator_unit', sa.String(), nullable=True),
        sa.Column('strength_denominator_system', sa.String(), nullable=True),
        sa.Column('strength_denominator_code', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['medication_pk'], ['medication.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_ingredient_created_at'), 'medication_ingredient', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_ingredient_item_id'), 'medication_ingredient', ['item_id'], unique=False)
    op.create_index(op.f('ix_medication_ingredient_medication_pk'), 'medication_ingredient', ['medication_pk'], unique=False)
    op.create_index(op.f('ix_medication_ingredient_tenant_id'), 'medication_ingredient', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_ingredient_updated_at'), 'medication_ingredient', ['updated_at'], unique=False)

    # medication_ingredient_item_coding
    op.create_table(
        'medication_ingredient_item_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('medication_ingredient_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['medication_ingredient_id'], ['medication_ingredient.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_ingredient_item_coding_created_at'), 'medication_ingredient_item_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_medication_ingredient_item_coding_medication_ingredient_id'), 'medication_ingredient_item_coding', ['medication_ingredient_id'], unique=False)
    op.create_index(op.f('ix_medication_ingredient_item_coding_tenant_id'), 'medication_ingredient_item_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_medication_ingredient_item_coding_updated_at'), 'medication_ingredient_item_coding', ['updated_at'], unique=False)


def downgrade() -> None:
    op.drop_table('medication_ingredient_item_coding')
    op.drop_table('medication_ingredient')
    op.drop_table('medication_identifier_type_coding')
    op.drop_table('medication_identifier')
    op.drop_table('medication_form_coding')
    op.drop_table('medication_code_coding')
    op.drop_table('medication')

    op.execute('DROP SEQUENCE IF EXISTS medication_pub_seq')

    op.execute('DROP TYPE IF EXISTS medication_ingredient_item_reference_type')
    op.execute('DROP TYPE IF EXISTS medication_identifier_assigner_reference_type')
    op.execute('DROP TYPE IF EXISTS medication_manufacturer_reference_type')
    op.execute('DROP TYPE IF EXISTS medication_quantity_comparator')
    op.execute('DROP TYPE IF EXISTS medication_status')
