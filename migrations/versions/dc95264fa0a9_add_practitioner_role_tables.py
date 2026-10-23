"""add_practitioner_role_tables

Revision ID: dc95264fa0a9
Revises: b6c25b934feb
Create Date: 2026-10-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'dc95264fa0a9'
down_revision: Union[str, None] = 'b6c25b934feb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # New PG enum types this resource introduces — created explicitly so the
    # table columns below can reference them with create_type=False (mirrors
    # every other resource's migration; op.create_table's own implicit
    # CREATE TYPE is avoided so autogenerate never tries to create them a
    # second time on a later revision).
    op.execute("CREATE TYPE practitioner_reference_type AS ENUM ('Practitioner')")
    op.execute(
        "CREATE TYPE practitioner_role_location_reference_type AS ENUM ('Location')"
    )
    op.execute(
        "CREATE TYPE practitioner_role_healthcare_service_reference_type AS ENUM ('HealthcareService')"
    )
    op.execute(
        "CREATE TYPE practitioner_role_endpoint_reference_type AS ENUM ('Endpoint')"
    )
    op.execute(
        "CREATE SEQUENCE IF NOT EXISTS practitioner_role_pub_seq START 140000 INCREMENT 1"
    )

    op.create_table(
        'practitioner_role',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('practitioner_role_id', sa.BigInteger(), server_default=sa.text("nextval('practitioner_role_pub_seq')"), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('practitioner_type', postgresql.ENUM('Practitioner', name='practitioner_reference_type', create_type=False), nullable=True),
        sa.Column('practitioner_id', sa.BigInteger(), nullable=True),
        sa.Column('practitioner_display', sa.String(), nullable=True),
        sa.Column('practitioner_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('practitioner_identifier_type_system', sa.String(), nullable=True),
        sa.Column('practitioner_identifier_type_version', sa.String(), nullable=True),
        sa.Column('practitioner_identifier_type_code', sa.String(), nullable=True),
        sa.Column('practitioner_identifier_type_display', sa.String(), nullable=True),
        sa.Column('practitioner_identifier_type_text', sa.String(), nullable=True),
        sa.Column('practitioner_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('practitioner_identifier_system', sa.String(), nullable=True),
        sa.Column('practitioner_identifier_value', sa.String(), nullable=True),
        sa.Column('practitioner_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('practitioner_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('organization_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
        sa.Column('organization_id', sa.BigInteger(), nullable=True),
        sa.Column('organization_display', sa.String(), nullable=True),
        sa.Column('organization_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('organization_identifier_type_system', sa.String(), nullable=True),
        sa.Column('organization_identifier_type_version', sa.String(), nullable=True),
        sa.Column('organization_identifier_type_code', sa.String(), nullable=True),
        sa.Column('organization_identifier_type_display', sa.String(), nullable=True),
        sa.Column('organization_identifier_type_text', sa.String(), nullable=True),
        sa.Column('organization_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('organization_identifier_system', sa.String(), nullable=True),
        sa.Column('organization_identifier_value', sa.String(), nullable=True),
        sa.Column('organization_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('organization_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('availability_exceptions', sa.Text(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_practitioner_role_created_at'), 'practitioner_role', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_id'), 'practitioner_role', ['id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_organization_id'), 'practitioner_role', ['organization_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_practitioner_id'), 'practitioner_role', ['practitioner_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_practitioner_role_id'), 'practitioner_role', ['practitioner_role_id'], unique=True)
    op.create_index(op.f('ix_practitioner_role_tenant_id'), 'practitioner_role', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_updated_at'), 'practitioner_role', ['updated_at'], unique=False)

    op.create_table(
        'practitioner_role_available_time',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('practitioner_role_pk', sa.BigInteger(), nullable=False),
        sa.Column('days_of_week', sa.Text(), nullable=True),
        sa.Column('all_day', sa.Boolean(), nullable=True),
        sa.Column('available_start_time', sa.Time(), nullable=True),
        sa.Column('available_end_time', sa.Time(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['practitioner_role_pk'], ['practitioner_role.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_practitioner_role_available_time_created_at'), 'practitioner_role_available_time', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_available_time_practitioner_role_pk'), 'practitioner_role_available_time', ['practitioner_role_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_role_available_time_tenant_id'), 'practitioner_role_available_time', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_available_time_updated_at'), 'practitioner_role_available_time', ['updated_at'], unique=False)

    op.create_table(
        'practitioner_role_code',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('practitioner_role_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['practitioner_role_pk'], ['practitioner_role.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_practitioner_role_code_created_at'), 'practitioner_role_code', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_code_practitioner_role_pk'), 'practitioner_role_code', ['practitioner_role_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_role_code_tenant_id'), 'practitioner_role_code', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_code_updated_at'), 'practitioner_role_code', ['updated_at'], unique=False)

    op.create_table(
        'practitioner_role_code_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('practitioner_role_code_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['practitioner_role_code_id'], ['practitioner_role_code.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_practitioner_role_code_coding_created_at'), 'practitioner_role_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_code_coding_practitioner_role_code_id'), 'practitioner_role_code_coding', ['practitioner_role_code_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_code_coding_tenant_id'), 'practitioner_role_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_code_coding_updated_at'), 'practitioner_role_code_coding', ['updated_at'], unique=False)

    op.create_table(
        'practitioner_role_endpoint',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('practitioner_role_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_type', postgresql.ENUM('Endpoint', name='practitioner_role_endpoint_reference_type', create_type=False), nullable=True),
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
        sa.ForeignKeyConstraint(['practitioner_role_pk'], ['practitioner_role.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('practitioner_role_pk', 'reference_type', 'reference_id', name='uq_practitioner_role_endpoint_reference'),
    )
    op.create_index(op.f('ix_practitioner_role_endpoint_created_at'), 'practitioner_role_endpoint', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_endpoint_practitioner_role_pk'), 'practitioner_role_endpoint', ['practitioner_role_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_role_endpoint_reference_id'), 'practitioner_role_endpoint', ['reference_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_endpoint_tenant_id'), 'practitioner_role_endpoint', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_endpoint_updated_at'), 'practitioner_role_endpoint', ['updated_at'], unique=False)

    op.create_table(
        'practitioner_role_healthcare_service',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('practitioner_role_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_type', postgresql.ENUM('HealthcareService', name='practitioner_role_healthcare_service_reference_type', create_type=False), nullable=True),
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
        sa.ForeignKeyConstraint(['practitioner_role_pk'], ['practitioner_role.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('practitioner_role_pk', 'reference_type', 'reference_id', name='uq_practitioner_role_healthcare_service_reference'),
    )
    op.create_index(op.f('ix_practitioner_role_healthcare_service_created_at'), 'practitioner_role_healthcare_service', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_healthcare_service_practitioner_role_pk'), 'practitioner_role_healthcare_service', ['practitioner_role_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_role_healthcare_service_reference_id'), 'practitioner_role_healthcare_service', ['reference_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_healthcare_service_tenant_id'), 'practitioner_role_healthcare_service', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_healthcare_service_updated_at'), 'practitioner_role_healthcare_service', ['updated_at'], unique=False)

    op.create_table(
        'practitioner_role_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('practitioner_role_pk', sa.BigInteger(), nullable=False),
        sa.Column('use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigner_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
        sa.Column('assigner_id', sa.BigInteger(), nullable=True),
        sa.Column('assigner_display', sa.String(), nullable=True),
        sa.Column('assigner_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('assigner_identifier_type_system', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_version', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_code', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_display', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_text', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('assigner_identifier_system', sa.String(), nullable=True),
        sa.Column('assigner_identifier_value', sa.String(), nullable=True),
        sa.Column('assigner_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigner_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['practitioner_role_pk'], ['practitioner_role.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('system', 'value', name='uq_practitioner_role_identifier_system_value'),
    )
    op.create_index(op.f('ix_practitioner_role_identifier_assigner_id'), 'practitioner_role_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_identifier_created_at'), 'practitioner_role_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_identifier_practitioner_role_pk'), 'practitioner_role_identifier', ['practitioner_role_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_role_identifier_tenant_id'), 'practitioner_role_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_identifier_updated_at'), 'practitioner_role_identifier', ['updated_at'], unique=False)

    op.create_table(
        'practitioner_role_identifier_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('practitioner_role_identifier_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['practitioner_role_identifier_id'], ['practitioner_role_identifier.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_practitioner_role_identifier_type_coding_created_at'), 'practitioner_role_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_identifier_type_coding_practitioner_role_identifier_id'), 'practitioner_role_identifier_type_coding', ['practitioner_role_identifier_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_identifier_type_coding_tenant_id'), 'practitioner_role_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_identifier_type_coding_updated_at'), 'practitioner_role_identifier_type_coding', ['updated_at'], unique=False)

    op.create_table(
        'practitioner_role_location',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('practitioner_role_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_type', postgresql.ENUM('Location', name='practitioner_role_location_reference_type', create_type=False), nullable=True),
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
        sa.ForeignKeyConstraint(['practitioner_role_pk'], ['practitioner_role.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('practitioner_role_pk', 'reference_type', 'reference_id', name='uq_practitioner_role_location_reference'),
    )
    op.create_index(op.f('ix_practitioner_role_location_created_at'), 'practitioner_role_location', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_location_practitioner_role_pk'), 'practitioner_role_location', ['practitioner_role_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_role_location_reference_id'), 'practitioner_role_location', ['reference_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_location_tenant_id'), 'practitioner_role_location', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_location_updated_at'), 'practitioner_role_location', ['updated_at'], unique=False)

    op.create_table(
        'practitioner_role_not_available',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('practitioner_role_pk', sa.BigInteger(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('during_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('during_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['practitioner_role_pk'], ['practitioner_role.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_practitioner_role_not_available_created_at'), 'practitioner_role_not_available', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_not_available_practitioner_role_pk'), 'practitioner_role_not_available', ['practitioner_role_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_role_not_available_tenant_id'), 'practitioner_role_not_available', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_not_available_updated_at'), 'practitioner_role_not_available', ['updated_at'], unique=False)

    op.create_table(
        'practitioner_role_specialty',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('practitioner_role_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['practitioner_role_pk'], ['practitioner_role.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_practitioner_role_specialty_created_at'), 'practitioner_role_specialty', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_specialty_practitioner_role_pk'), 'practitioner_role_specialty', ['practitioner_role_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_role_specialty_tenant_id'), 'practitioner_role_specialty', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_specialty_updated_at'), 'practitioner_role_specialty', ['updated_at'], unique=False)

    op.create_table(
        'practitioner_role_specialty_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('practitioner_role_specialty_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['practitioner_role_specialty_id'], ['practitioner_role_specialty.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_practitioner_role_specialty_coding_created_at'), 'practitioner_role_specialty_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_specialty_coding_practitioner_role_specialty_id'), 'practitioner_role_specialty_coding', ['practitioner_role_specialty_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_specialty_coding_tenant_id'), 'practitioner_role_specialty_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_specialty_coding_updated_at'), 'practitioner_role_specialty_coding', ['updated_at'], unique=False)

    op.create_table(
        'practitioner_role_telecom',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('practitioner_role_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', postgresql.ENUM('phone', 'fax', 'email', 'pager', 'url', 'sms', 'other', name='contact_point_system', create_type=False), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('use', postgresql.ENUM('home', 'work', 'temp', 'old', 'mobile', name='contact_point_use', create_type=False), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['practitioner_role_pk'], ['practitioner_role.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_practitioner_role_telecom_created_at'), 'practitioner_role_telecom', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_telecom_practitioner_role_pk'), 'practitioner_role_telecom', ['practitioner_role_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_role_telecom_tenant_id'), 'practitioner_role_telecom', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_telecom_updated_at'), 'practitioner_role_telecom', ['updated_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_practitioner_role_telecom_updated_at'), table_name='practitioner_role_telecom')
    op.drop_index(op.f('ix_practitioner_role_telecom_tenant_id'), table_name='practitioner_role_telecom')
    op.drop_index(op.f('ix_practitioner_role_telecom_practitioner_role_pk'), table_name='practitioner_role_telecom')
    op.drop_index(op.f('ix_practitioner_role_telecom_created_at'), table_name='practitioner_role_telecom')
    op.drop_table('practitioner_role_telecom')

    op.drop_index(op.f('ix_practitioner_role_specialty_coding_updated_at'), table_name='practitioner_role_specialty_coding')
    op.drop_index(op.f('ix_practitioner_role_specialty_coding_tenant_id'), table_name='practitioner_role_specialty_coding')
    op.drop_index(op.f('ix_practitioner_role_specialty_coding_practitioner_role_specialty_id'), table_name='practitioner_role_specialty_coding')
    op.drop_index(op.f('ix_practitioner_role_specialty_coding_created_at'), table_name='practitioner_role_specialty_coding')
    op.drop_table('practitioner_role_specialty_coding')

    op.drop_index(op.f('ix_practitioner_role_specialty_updated_at'), table_name='practitioner_role_specialty')
    op.drop_index(op.f('ix_practitioner_role_specialty_tenant_id'), table_name='practitioner_role_specialty')
    op.drop_index(op.f('ix_practitioner_role_specialty_practitioner_role_pk'), table_name='practitioner_role_specialty')
    op.drop_index(op.f('ix_practitioner_role_specialty_created_at'), table_name='practitioner_role_specialty')
    op.drop_table('practitioner_role_specialty')

    op.drop_index(op.f('ix_practitioner_role_not_available_updated_at'), table_name='practitioner_role_not_available')
    op.drop_index(op.f('ix_practitioner_role_not_available_tenant_id'), table_name='practitioner_role_not_available')
    op.drop_index(op.f('ix_practitioner_role_not_available_practitioner_role_pk'), table_name='practitioner_role_not_available')
    op.drop_index(op.f('ix_practitioner_role_not_available_created_at'), table_name='practitioner_role_not_available')
    op.drop_table('practitioner_role_not_available')

    op.drop_index(op.f('ix_practitioner_role_location_updated_at'), table_name='practitioner_role_location')
    op.drop_index(op.f('ix_practitioner_role_location_tenant_id'), table_name='practitioner_role_location')
    op.drop_index(op.f('ix_practitioner_role_location_reference_id'), table_name='practitioner_role_location')
    op.drop_index(op.f('ix_practitioner_role_location_practitioner_role_pk'), table_name='practitioner_role_location')
    op.drop_index(op.f('ix_practitioner_role_location_created_at'), table_name='practitioner_role_location')
    op.drop_table('practitioner_role_location')

    op.drop_index(op.f('ix_practitioner_role_identifier_type_coding_updated_at'), table_name='practitioner_role_identifier_type_coding')
    op.drop_index(op.f('ix_practitioner_role_identifier_type_coding_tenant_id'), table_name='practitioner_role_identifier_type_coding')
    op.drop_index(op.f('ix_practitioner_role_identifier_type_coding_practitioner_role_identifier_id'), table_name='practitioner_role_identifier_type_coding')
    op.drop_index(op.f('ix_practitioner_role_identifier_type_coding_created_at'), table_name='practitioner_role_identifier_type_coding')
    op.drop_table('practitioner_role_identifier_type_coding')

    op.drop_index(op.f('ix_practitioner_role_identifier_updated_at'), table_name='practitioner_role_identifier')
    op.drop_index(op.f('ix_practitioner_role_identifier_tenant_id'), table_name='practitioner_role_identifier')
    op.drop_index(op.f('ix_practitioner_role_identifier_practitioner_role_pk'), table_name='practitioner_role_identifier')
    op.drop_index(op.f('ix_practitioner_role_identifier_created_at'), table_name='practitioner_role_identifier')
    op.drop_index(op.f('ix_practitioner_role_identifier_assigner_id'), table_name='practitioner_role_identifier')
    op.drop_table('practitioner_role_identifier')

    op.drop_index(op.f('ix_practitioner_role_healthcare_service_updated_at'), table_name='practitioner_role_healthcare_service')
    op.drop_index(op.f('ix_practitioner_role_healthcare_service_tenant_id'), table_name='practitioner_role_healthcare_service')
    op.drop_index(op.f('ix_practitioner_role_healthcare_service_reference_id'), table_name='practitioner_role_healthcare_service')
    op.drop_index(op.f('ix_practitioner_role_healthcare_service_practitioner_role_pk'), table_name='practitioner_role_healthcare_service')
    op.drop_index(op.f('ix_practitioner_role_healthcare_service_created_at'), table_name='practitioner_role_healthcare_service')
    op.drop_table('practitioner_role_healthcare_service')

    op.drop_index(op.f('ix_practitioner_role_endpoint_updated_at'), table_name='practitioner_role_endpoint')
    op.drop_index(op.f('ix_practitioner_role_endpoint_tenant_id'), table_name='practitioner_role_endpoint')
    op.drop_index(op.f('ix_practitioner_role_endpoint_reference_id'), table_name='practitioner_role_endpoint')
    op.drop_index(op.f('ix_practitioner_role_endpoint_practitioner_role_pk'), table_name='practitioner_role_endpoint')
    op.drop_index(op.f('ix_practitioner_role_endpoint_created_at'), table_name='practitioner_role_endpoint')
    op.drop_table('practitioner_role_endpoint')

    op.drop_index(op.f('ix_practitioner_role_code_coding_updated_at'), table_name='practitioner_role_code_coding')
    op.drop_index(op.f('ix_practitioner_role_code_coding_tenant_id'), table_name='practitioner_role_code_coding')
    op.drop_index(op.f('ix_practitioner_role_code_coding_practitioner_role_code_id'), table_name='practitioner_role_code_coding')
    op.drop_index(op.f('ix_practitioner_role_code_coding_created_at'), table_name='practitioner_role_code_coding')
    op.drop_table('practitioner_role_code_coding')

    op.drop_index(op.f('ix_practitioner_role_code_updated_at'), table_name='practitioner_role_code')
    op.drop_index(op.f('ix_practitioner_role_code_tenant_id'), table_name='practitioner_role_code')
    op.drop_index(op.f('ix_practitioner_role_code_practitioner_role_pk'), table_name='practitioner_role_code')
    op.drop_index(op.f('ix_practitioner_role_code_created_at'), table_name='practitioner_role_code')
    op.drop_table('practitioner_role_code')

    op.drop_index(op.f('ix_practitioner_role_available_time_updated_at'), table_name='practitioner_role_available_time')
    op.drop_index(op.f('ix_practitioner_role_available_time_tenant_id'), table_name='practitioner_role_available_time')
    op.drop_index(op.f('ix_practitioner_role_available_time_practitioner_role_pk'), table_name='practitioner_role_available_time')
    op.drop_index(op.f('ix_practitioner_role_available_time_created_at'), table_name='practitioner_role_available_time')
    op.drop_table('practitioner_role_available_time')

    op.drop_index(op.f('ix_practitioner_role_updated_at'), table_name='practitioner_role')
    op.drop_index(op.f('ix_practitioner_role_tenant_id'), table_name='practitioner_role')
    op.drop_index(op.f('ix_practitioner_role_practitioner_role_id'), table_name='practitioner_role')
    op.drop_index(op.f('ix_practitioner_role_practitioner_id'), table_name='practitioner_role')
    op.drop_index(op.f('ix_practitioner_role_organization_id'), table_name='practitioner_role')
    op.drop_index(op.f('ix_practitioner_role_id'), table_name='practitioner_role')
    op.drop_index(op.f('ix_practitioner_role_created_at'), table_name='practitioner_role')
    op.drop_table('practitioner_role')

    op.execute('DROP SEQUENCE IF EXISTS practitioner_role_pub_seq')
    op.execute('DROP TYPE IF EXISTS practitioner_role_endpoint_reference_type')
    op.execute('DROP TYPE IF EXISTS practitioner_role_healthcare_service_reference_type')
    op.execute('DROP TYPE IF EXISTS practitioner_role_location_reference_type')
    op.execute('DROP TYPE IF EXISTS practitioner_reference_type')
