"""add_specimen_definition_tables

Revision ID: 286d55bd92c4
Revises: b0692334ff35
Create Date: 2026-11-03 00:31:44.800619

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '286d55bd92c4'
down_revision: Union[str, None] = 'b0692334ff35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enums
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE specimen_definition_preference AS ENUM (
                'preferred', 'alternate'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE specimen_definition_quantity_comparator AS ENUM (
                'lt', 'le', 'ge', 'gt'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE specimen_definition_additive_reference_type AS ENUM (
                'Substance'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # 2. Sequence
    op.execute("CREATE SEQUENCE IF NOT EXISTS specimen_definition_pub_seq START WITH 550000 INCREMENT BY 1;")

    # 3. Tables
    op.create_table('specimen_definition',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('specimen_definition_id', sa.BigInteger(), server_default=sa.text("nextval('specimen_definition_pub_seq')"), nullable=False),
    sa.Column('identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('identifier_type_text', sa.String(), nullable=True),
    sa.Column('identifier_system', sa.String(), nullable=True),
    sa.Column('identifier_value', sa.String(), nullable=True),
    sa.Column('identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('identifier_assigner_reference', sa.String(), nullable=True),
    sa.Column('identifier_assigner_id', sa.BigInteger(), nullable=True),
    sa.Column('identifier_assigner_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
    sa.Column('identifier_assigner_display', sa.String(), nullable=True),
    sa.Column('identifier_assigner_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('identifier_assigner_identifier_type_system', sa.String(), nullable=True),
    sa.Column('identifier_assigner_identifier_type_version', sa.String(), nullable=True),
    sa.Column('identifier_assigner_identifier_type_code', sa.String(), nullable=True),
    sa.Column('identifier_assigner_identifier_type_display', sa.String(), nullable=True),
    sa.Column('identifier_assigner_identifier_type_text', sa.String(), nullable=True),
    sa.Column('identifier_assigner_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('identifier_assigner_identifier_system', sa.String(), nullable=True),
    sa.Column('identifier_assigner_identifier_value', sa.String(), nullable=True),
    sa.Column('identifier_assigner_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('identifier_assigner_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('type_collected_text', sa.String(), nullable=True),
    sa.Column('time_aspect', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_definition_created_at'), 'specimen_definition', ['created_at'], unique=False)
    op.create_index(op.f('ix_specimen_definition_id'), 'specimen_definition', ['id'], unique=False)
    op.create_index(op.f('ix_specimen_definition_identifier_assigner_id'), 'specimen_definition', ['identifier_assigner_id'], unique=False)
    op.create_index(op.f('ix_specimen_definition_specimen_definition_id'), 'specimen_definition', ['specimen_definition_id'], unique=True)
    op.create_index(op.f('ix_specimen_definition_tenant_id'), 'specimen_definition', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_specimen_definition_updated_at'), 'specimen_definition', ['updated_at'], unique=False)

    op.create_table('specimen_definition_identifier_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('specimen_definition_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['specimen_definition_pk'], ['specimen_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_definition_identifier_type_coding_created_at'), 'specimen_definition_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_specimen_definition_identifier_type_coding_specimen_definition_pk'), 'specimen_definition_identifier_type_coding', ['specimen_definition_pk'], unique=False)
    op.create_index(op.f('ix_specimen_definition_identifier_type_coding_tenant_id'), 'specimen_definition_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_specimen_definition_identifier_type_coding_updated_at'), 'specimen_definition_identifier_type_coding', ['updated_at'], unique=False)

    op.create_table('specimen_definition_type_collected_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('specimen_definition_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['specimen_definition_pk'], ['specimen_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_definition_type_collected_coding_created_at'), 'specimen_definition_type_collected_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_specimen_definition_type_collected_coding_specimen_definition_pk'), 'specimen_definition_type_collected_coding', ['specimen_definition_pk'], unique=False)
    op.create_index(op.f('ix_specimen_definition_type_collected_coding_tenant_id'), 'specimen_definition_type_collected_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_specimen_definition_type_collected_coding_updated_at'), 'specimen_definition_type_collected_coding', ['updated_at'], unique=False)

    op.create_table('specimen_definition_patient_preparation',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('specimen_definition_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['specimen_definition_pk'], ['specimen_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_definition_patient_preparation_created_at'), 'specimen_definition_patient_preparation', ['created_at'], unique=False)
    op.create_index(op.f('ix_specimen_definition_patient_preparation_specimen_definition_pk'), 'specimen_definition_patient_preparation', ['specimen_definition_pk'], unique=False)
    op.create_index(op.f('ix_specimen_definition_patient_preparation_tenant_id'), 'specimen_definition_patient_preparation', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_specimen_definition_patient_preparation_updated_at'), 'specimen_definition_patient_preparation', ['updated_at'], unique=False)

    op.create_table('specimen_definition_patient_preparation_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('patient_preparation_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['patient_preparation_pk'], ['specimen_definition_patient_preparation.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_definition_patient_preparation_coding_created_at'), 'specimen_definition_patient_preparation_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_specimen_definition_patient_preparation_coding_patient_preparation_pk'), 'specimen_definition_patient_preparation_coding', ['patient_preparation_pk'], unique=False)
    op.create_index(op.f('ix_specimen_definition_patient_preparation_coding_tenant_id'), 'specimen_definition_patient_preparation_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_specimen_definition_patient_preparation_coding_updated_at'), 'specimen_definition_patient_preparation_coding', ['updated_at'], unique=False)

    op.create_table('specimen_definition_collection',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('specimen_definition_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['specimen_definition_pk'], ['specimen_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_definition_collection_created_at'), 'specimen_definition_collection', ['created_at'], unique=False)
    op.create_index(op.f('ix_specimen_definition_collection_specimen_definition_pk'), 'specimen_definition_collection', ['specimen_definition_pk'], unique=False)
    op.create_index(op.f('ix_specimen_definition_collection_tenant_id'), 'specimen_definition_collection', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_specimen_definition_collection_updated_at'), 'specimen_definition_collection', ['updated_at'], unique=False)

    op.create_table('specimen_definition_collection_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('collection_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['collection_pk'], ['specimen_definition_collection.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_definition_collection_coding_collection_pk'), 'specimen_definition_collection_coding', ['collection_pk'], unique=False)
    op.create_index(op.f('ix_specimen_definition_collection_coding_created_at'), 'specimen_definition_collection_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_specimen_definition_collection_coding_tenant_id'), 'specimen_definition_collection_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_specimen_definition_collection_coding_updated_at'), 'specimen_definition_collection_coding', ['updated_at'], unique=False)

    op.create_table('specimen_definition_type_tested',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('specimen_definition_pk', sa.BigInteger(), nullable=False),
    sa.Column('is_derived', sa.Boolean(), nullable=True),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('preference', postgresql.ENUM('preferred', 'alternate', name='specimen_definition_preference', create_type=False), nullable=False),
    sa.Column('requirement', sa.String(), nullable=True),
    sa.Column('retention_time_value', sa.Numeric(), nullable=True),
    sa.Column('retention_time_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='specimen_definition_quantity_comparator', create_type=False), nullable=True),
    sa.Column('retention_time_unit', sa.String(), nullable=True),
    sa.Column('retention_time_system', sa.String(), nullable=True),
    sa.Column('retention_time_code', sa.String(), nullable=True),
    sa.Column('container_description', sa.String(), nullable=True),
    sa.Column('container_preparation', sa.String(), nullable=True),
    sa.Column('container_material_text', sa.String(), nullable=True),
    sa.Column('container_type_text', sa.String(), nullable=True),
    sa.Column('container_cap_text', sa.String(), nullable=True),
    sa.Column('container_capacity_value', sa.Numeric(), nullable=True),
    sa.Column('container_capacity_unit', sa.String(), nullable=True),
    sa.Column('container_capacity_system', sa.String(), nullable=True),
    sa.Column('container_capacity_code', sa.String(), nullable=True),
    sa.Column('container_minimum_volume_string', sa.String(), nullable=True),
    sa.Column('container_minimum_volume_quantity_value', sa.Numeric(), nullable=True),
    sa.Column('container_minimum_volume_quantity_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='specimen_definition_quantity_comparator', create_type=False), nullable=True),
    sa.Column('container_minimum_volume_quantity_unit', sa.String(), nullable=True),
    sa.Column('container_minimum_volume_quantity_system', sa.String(), nullable=True),
    sa.Column('container_minimum_volume_quantity_code', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['specimen_definition_pk'], ['specimen_definition.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_definition_type_tested_created_at'), 'specimen_definition_type_tested', ['created_at'], unique=False)
    op.create_index(op.f('ix_specimen_definition_type_tested_specimen_definition_pk'), 'specimen_definition_type_tested', ['specimen_definition_pk'], unique=False)
    op.create_index(op.f('ix_specimen_definition_type_tested_tenant_id'), 'specimen_definition_type_tested', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_specimen_definition_type_tested_updated_at'), 'specimen_definition_type_tested', ['updated_at'], unique=False)

    op.create_table('specimen_definition_type_tested_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('type_tested_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['type_tested_pk'], ['specimen_definition_type_tested.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_definition_type_tested_type_coding_created_at'), 'specimen_definition_type_tested_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_specimen_definition_type_tested_type_coding_tenant_id'), 'specimen_definition_type_tested_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_specimen_definition_type_tested_type_coding_type_tested_pk'), 'specimen_definition_type_tested_type_coding', ['type_tested_pk'], unique=False)
    op.create_index(op.f('ix_specimen_definition_type_tested_type_coding_updated_at'), 'specimen_definition_type_tested_type_coding', ['updated_at'], unique=False)

    op.create_table('specimen_definition_container_material_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('type_tested_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['type_tested_pk'], ['specimen_definition_type_tested.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_definition_container_material_coding_created_at'), 'specimen_definition_container_material_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_specimen_definition_container_material_coding_tenant_id'), 'specimen_definition_container_material_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_specimen_definition_container_material_coding_type_tested_pk'), 'specimen_definition_container_material_coding', ['type_tested_pk'], unique=False)
    op.create_index(op.f('ix_specimen_definition_container_material_coding_updated_at'), 'specimen_definition_container_material_coding', ['updated_at'], unique=False)

    op.create_table('specimen_definition_container_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('type_tested_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['type_tested_pk'], ['specimen_definition_type_tested.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_definition_container_type_coding_created_at'), 'specimen_definition_container_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_specimen_definition_container_type_coding_tenant_id'), 'specimen_definition_container_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_specimen_definition_container_type_coding_type_tested_pk'), 'specimen_definition_container_type_coding', ['type_tested_pk'], unique=False)
    op.create_index(op.f('ix_specimen_definition_container_type_coding_updated_at'), 'specimen_definition_container_type_coding', ['updated_at'], unique=False)

    op.create_table('specimen_definition_container_cap_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('type_tested_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['type_tested_pk'], ['specimen_definition_type_tested.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_definition_container_cap_coding_created_at'), 'specimen_definition_container_cap_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_specimen_definition_container_cap_coding_tenant_id'), 'specimen_definition_container_cap_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_specimen_definition_container_cap_coding_type_tested_pk'), 'specimen_definition_container_cap_coding', ['type_tested_pk'], unique=False)
    op.create_index(op.f('ix_specimen_definition_container_cap_coding_updated_at'), 'specimen_definition_container_cap_coding', ['updated_at'], unique=False)

    op.create_table('specimen_definition_container_additive',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('type_tested_pk', sa.BigInteger(), nullable=False),
    sa.Column('additive_codeable_concept_text', sa.String(), nullable=True),
    sa.Column('additive_reference_reference', sa.String(), nullable=True),
    sa.Column('additive_reference_type', postgresql.ENUM('Substance', name='specimen_definition_additive_reference_type', create_type=False), nullable=True),
    sa.Column('additive_reference_id', sa.BigInteger(), nullable=True),
    sa.Column('additive_reference_display', sa.String(), nullable=True),
    sa.Column('additive_reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
    sa.Column('additive_reference_identifier_type_system', sa.String(), nullable=True),
    sa.Column('additive_reference_identifier_type_version', sa.String(), nullable=True),
    sa.Column('additive_reference_identifier_type_code', sa.String(), nullable=True),
    sa.Column('additive_reference_identifier_type_display', sa.String(), nullable=True),
    sa.Column('additive_reference_identifier_type_text', sa.String(), nullable=True),
    sa.Column('additive_reference_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('additive_reference_identifier_system', sa.String(), nullable=True),
    sa.Column('additive_reference_identifier_value', sa.String(), nullable=True),
    sa.Column('additive_reference_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('additive_reference_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['type_tested_pk'], ['specimen_definition_type_tested.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_definition_container_additive_additive_reference_id'), 'specimen_definition_container_additive', ['additive_reference_id'], unique=False)
    op.create_index(op.f('ix_specimen_definition_container_additive_created_at'), 'specimen_definition_container_additive', ['created_at'], unique=False)
    op.create_index(op.f('ix_specimen_definition_container_additive_tenant_id'), 'specimen_definition_container_additive', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_specimen_definition_container_additive_type_tested_pk'), 'specimen_definition_container_additive', ['type_tested_pk'], unique=False)
    op.create_index(op.f('ix_specimen_definition_container_additive_updated_at'), 'specimen_definition_container_additive', ['updated_at'], unique=False)

    op.create_table('specimen_definition_container_additive_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('container_additive_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['container_additive_pk'], ['specimen_definition_container_additive.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_definition_container_additive_coding_container_additive_pk'), 'specimen_definition_container_additive_coding', ['container_additive_pk'], unique=False)
    op.create_index(op.f('ix_specimen_definition_container_additive_coding_created_at'), 'specimen_definition_container_additive_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_specimen_definition_container_additive_coding_tenant_id'), 'specimen_definition_container_additive_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_specimen_definition_container_additive_coding_updated_at'), 'specimen_definition_container_additive_coding', ['updated_at'], unique=False)

    op.create_table('specimen_definition_type_tested_rejection_criterion',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('type_tested_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['type_tested_pk'], ['specimen_definition_type_tested.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_definition_type_tested_rejection_criterion_created_at'), 'specimen_definition_type_tested_rejection_criterion', ['created_at'], unique=False)
    op.create_index(op.f('ix_specimen_definition_type_tested_rejection_criterion_tenant_id'), 'specimen_definition_type_tested_rejection_criterion', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_specimen_definition_type_tested_rejection_criterion_type_tested_pk'), 'specimen_definition_type_tested_rejection_criterion', ['type_tested_pk'], unique=False)
    op.create_index(op.f('ix_specimen_definition_type_tested_rejection_criterion_updated_at'), 'specimen_definition_type_tested_rejection_criterion', ['updated_at'], unique=False)

    op.create_table('specimen_definition_type_tested_rejection_criterion_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('rejection_criterion_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['rejection_criterion_pk'], ['specimen_definition_type_tested_rejection_criterion.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_definition_type_tested_rejection_criterion_coding_created_at'), 'specimen_definition_type_tested_rejection_criterion_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_specimen_definition_type_tested_rejection_criterion_coding_rejection_criterion_pk'), 'specimen_definition_type_tested_rejection_criterion_coding', ['rejection_criterion_pk'], unique=False)
    op.create_index(op.f('ix_specimen_definition_type_tested_rejection_criterion_coding_tenant_id'), 'specimen_definition_type_tested_rejection_criterion_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_specimen_definition_type_tested_rejection_criterion_coding_updated_at'), 'specimen_definition_type_tested_rejection_criterion_coding', ['updated_at'], unique=False)

    op.create_table('specimen_definition_type_tested_handling',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('type_tested_pk', sa.BigInteger(), nullable=False),
    sa.Column('temperature_qualifier_text', sa.String(), nullable=True),
    sa.Column('temperature_range_low_value', sa.Numeric(), nullable=True),
    sa.Column('temperature_range_low_unit', sa.String(), nullable=True),
    sa.Column('temperature_range_low_system', sa.String(), nullable=True),
    sa.Column('temperature_range_low_code', sa.String(), nullable=True),
    sa.Column('temperature_range_high_value', sa.Numeric(), nullable=True),
    sa.Column('temperature_range_high_unit', sa.String(), nullable=True),
    sa.Column('temperature_range_high_system', sa.String(), nullable=True),
    sa.Column('temperature_range_high_code', sa.String(), nullable=True),
    sa.Column('max_duration_value', sa.Numeric(), nullable=True),
    sa.Column('max_duration_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='specimen_definition_quantity_comparator', create_type=False), nullable=True),
    sa.Column('max_duration_unit', sa.String(), nullable=True),
    sa.Column('max_duration_system', sa.String(), nullable=True),
    sa.Column('max_duration_code', sa.String(), nullable=True),
    sa.Column('instruction', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['type_tested_pk'], ['specimen_definition_type_tested.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_definition_type_tested_handling_created_at'), 'specimen_definition_type_tested_handling', ['created_at'], unique=False)
    op.create_index(op.f('ix_specimen_definition_type_tested_handling_tenant_id'), 'specimen_definition_type_tested_handling', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_specimen_definition_type_tested_handling_type_tested_pk'), 'specimen_definition_type_tested_handling', ['type_tested_pk'], unique=False)
    op.create_index(op.f('ix_specimen_definition_type_tested_handling_updated_at'), 'specimen_definition_type_tested_handling', ['updated_at'], unique=False)

    op.create_table('specimen_definition_handling_temp_qual_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('handling_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['handling_pk'], ['specimen_definition_type_tested_handling.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_definition_handling_temp_qual_coding_created_at'), 'specimen_definition_handling_temp_qual_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_specimen_definition_handling_temp_qual_coding_handling_pk'), 'specimen_definition_handling_temp_qual_coding', ['handling_pk'], unique=False)
    op.create_index(op.f('ix_specimen_definition_handling_temp_qual_coding_tenant_id'), 'specimen_definition_handling_temp_qual_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_specimen_definition_handling_temp_qual_coding_updated_at'), 'specimen_definition_handling_temp_qual_coding', ['updated_at'], unique=False)


def downgrade() -> None:
    # 1. Drop tables in reverse FK order
    op.drop_table('specimen_definition_handling_temp_qual_coding')
    op.drop_table('specimen_definition_type_tested_handling')
    op.drop_table('specimen_definition_type_tested_rejection_criterion_coding')
    op.drop_table('specimen_definition_type_tested_rejection_criterion')
    op.drop_table('specimen_definition_container_additive_coding')
    op.drop_table('specimen_definition_container_additive')
    op.drop_table('specimen_definition_container_cap_coding')
    op.drop_table('specimen_definition_container_type_coding')
    op.drop_table('specimen_definition_container_material_coding')
    op.drop_table('specimen_definition_type_tested_type_coding')
    op.drop_table('specimen_definition_type_tested')
    op.drop_table('specimen_definition_collection_coding')
    op.drop_table('specimen_definition_collection')
    op.drop_table('specimen_definition_patient_preparation_coding')
    op.drop_table('specimen_definition_patient_preparation')
    op.drop_table('specimen_definition_type_collected_coding')
    op.drop_table('specimen_definition_identifier_type_coding')
    op.drop_table('specimen_definition')

    # 2. Drop sequence
    op.execute("DROP SEQUENCE IF EXISTS specimen_definition_pub_seq")

    # 3. Drop enums
    op.execute("DROP TYPE IF EXISTS specimen_definition_additive_reference_type")
    op.execute("DROP TYPE IF EXISTS specimen_definition_quantity_comparator")
    op.execute("DROP TYPE IF EXISTS specimen_definition_preference")
