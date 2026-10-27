"""baseline schema

Revision ID: a8a83f60bc23
Revises: 
Create Date: 2026-10-25 00:30:42.793624

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

_address_type = postgresql.ENUM('postal', 'physical', 'both', name="address_type", create_type=False)
_address_use = postgresql.ENUM('home', 'work', 'temp', 'old', 'billing', name="address_use", create_type=False)
_administrative_gender = postgresql.ENUM('male', 'female', 'other', 'unknown', name="administrative_gender", create_type=False)
_contact_point_system = postgresql.ENUM('phone', 'fax', 'email', 'pager', 'url', 'sms', 'other', name="contact_point_system", create_type=False)
_contact_point_use = postgresql.ENUM('home', 'work', 'temp', 'old', 'mobile', name="contact_point_use", create_type=False)
_fhir_profile_scope_level = postgresql.ENUM('base', 'country', 'organization', name="fhir_profile_scope_level", create_type=False)
_fhir_profile_status = postgresql.ENUM('draft', 'active', 'retired', 'unknown', name="fhir_profile_status", create_type=False)
_healthcare_service_coverage_area_reference_type = postgresql.ENUM('Location', name="healthcare_service_coverage_area_reference_type", create_type=False)
_healthcare_service_endpoint_reference_type = postgresql.ENUM('Endpoint', name="healthcare_service_endpoint_reference_type", create_type=False)
_healthcare_service_location_reference_type = postgresql.ENUM('Location', name="healthcare_service_location_reference_type", create_type=False)
_human_name_use = postgresql.ENUM('usual', 'official', 'temp', 'nickname', 'anonymous', 'old', 'maiden', name="human_name_use", create_type=False)
_identifier_use = postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name="identifier_use", create_type=False)
_location_endpoint_reference_type = postgresql.ENUM('Endpoint', name="location_endpoint_reference_type", create_type=False)
_location_mode = postgresql.ENUM('instance', 'kind', name="location_mode", create_type=False)
_location_part_of_reference_type = postgresql.ENUM('Location', name="location_part_of_reference_type", create_type=False)
_location_status = postgresql.ENUM('active', 'suspended', 'inactive', name="location_status", create_type=False)
_organization_endpoint_ref_type = postgresql.ENUM('Endpoint', name="organization_endpoint_ref_type", create_type=False)
_organization_reference_type = postgresql.ENUM('Organization', name="organization_reference_type", create_type=False)
_practitioner_reference_type = postgresql.ENUM('Practitioner', name="practitioner_reference_type", create_type=False)
_practitioner_role_endpoint_reference_type = postgresql.ENUM('Endpoint', name="practitioner_role_endpoint_reference_type", create_type=False)
_practitioner_role_healthcare_service_reference_type = postgresql.ENUM('HealthcareService', name="practitioner_role_healthcare_service_reference_type", create_type=False)
_practitioner_role_location_reference_type = postgresql.ENUM('Location', name="practitioner_role_location_reference_type", create_type=False)
_schedule_actor_reference_type = postgresql.ENUM('Patient', 'Practitioner', 'PractitionerRole', 'RelatedPerson', 'Device', 'HealthcareService', 'Location', name="schedule_actor_reference_type", create_type=False)
_schedule_reference_type = postgresql.ENUM('Schedule', name="schedule_reference_type", create_type=False)
_slot_status = postgresql.ENUM('busy', 'free', 'busy_unavailable', 'busy_tentative', 'entered_in_error', name="slot_status", create_type=False)

# revision identifiers, used by Alembic.
revision: str = 'a8a83f60bc23'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- explicit enum type creation, using the SAME shared objects ---
    # --- referenced by the columns below (see /fhir-db-model's enum rule) ---
    _address_type.create(op.get_bind(), checkfirst=True)
    _address_use.create(op.get_bind(), checkfirst=True)
    _administrative_gender.create(op.get_bind(), checkfirst=True)
    _contact_point_system.create(op.get_bind(), checkfirst=True)
    _contact_point_use.create(op.get_bind(), checkfirst=True)
    _fhir_profile_scope_level.create(op.get_bind(), checkfirst=True)
    _fhir_profile_status.create(op.get_bind(), checkfirst=True)
    _healthcare_service_coverage_area_reference_type.create(op.get_bind(), checkfirst=True)
    _healthcare_service_endpoint_reference_type.create(op.get_bind(), checkfirst=True)
    _healthcare_service_location_reference_type.create(op.get_bind(), checkfirst=True)
    _human_name_use.create(op.get_bind(), checkfirst=True)
    _identifier_use.create(op.get_bind(), checkfirst=True)
    _location_endpoint_reference_type.create(op.get_bind(), checkfirst=True)
    _location_mode.create(op.get_bind(), checkfirst=True)
    _location_part_of_reference_type.create(op.get_bind(), checkfirst=True)
    _location_status.create(op.get_bind(), checkfirst=True)
    _organization_endpoint_ref_type.create(op.get_bind(), checkfirst=True)
    _organization_reference_type.create(op.get_bind(), checkfirst=True)
    _practitioner_reference_type.create(op.get_bind(), checkfirst=True)
    _practitioner_role_endpoint_reference_type.create(op.get_bind(), checkfirst=True)
    _practitioner_role_healthcare_service_reference_type.create(op.get_bind(), checkfirst=True)
    _practitioner_role_location_reference_type.create(op.get_bind(), checkfirst=True)
    _schedule_actor_reference_type.create(op.get_bind(), checkfirst=True)
    _schedule_reference_type.create(op.get_bind(), checkfirst=True)
    _slot_status.create(op.get_bind(), checkfirst=True)

    # ### commands auto generated by Alembic - please adjust! ###
    op.execute('CREATE SEQUENCE IF NOT EXISTS healthcare_service_pub_seq START 150000 INCREMENT 1')
    op.execute('CREATE SEQUENCE IF NOT EXISTS location_pub_seq START 230000 INCREMENT 1')
    op.execute('CREATE SEQUENCE IF NOT EXISTS organization_pub_seq START 190000 INCREMENT 1')
    op.execute('CREATE SEQUENCE IF NOT EXISTS practitioner_pub_seq START 30000 INCREMENT 1')
    op.execute('CREATE SEQUENCE IF NOT EXISTS practitioner_role_pub_seq START 140000 INCREMENT 1')
    op.execute('CREATE SEQUENCE IF NOT EXISTS schedule_pub_seq START 200000 INCREMENT 1')
    op.execute('CREATE SEQUENCE IF NOT EXISTS slot_pub_seq START 220000 INCREMENT 1')
    op.create_table('fhir_profile',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('resource_type', sa.String(), nullable=False),
    sa.Column('scope_level', _fhir_profile_scope_level, nullable=False),
    sa.Column('scope_id', sa.String(), nullable=True),
    sa.Column('parent_profile_id', sa.BigInteger(), nullable=True),
    sa.Column('canonical_url', sa.String(), nullable=False),
    sa.Column('version', sa.String(), server_default=sa.text("'1'"), nullable=False),
    sa.Column('status', _fhir_profile_status, server_default=sa.text("'draft'"), nullable=False),
    sa.Column('structure_definition', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['parent_profile_id'], ['fhir_profile.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('canonical_url', 'version', name='uq_fhir_profile_url_version')
    )
    op.create_index('ix_fhir_profile_resource_type', 'fhir_profile', ['resource_type'], unique=False)
    op.create_index('ix_fhir_profile_scope_id', 'fhir_profile', ['scope_id'], unique=False)
    op.create_index('ix_fhir_profile_scope_level', 'fhir_profile', ['scope_level'], unique=False)
    op.create_index('uq_fhir_profile_active_scoped', 'fhir_profile', ['resource_type', 'scope_level', 'scope_id'], unique=True, postgresql_where=sa.text("status = 'active' AND scope_id IS NOT NULL"), sqlite_where=sa.text("status = 'active' AND scope_id IS NOT NULL"))
    op.create_index('uq_fhir_profile_base_singleton', 'fhir_profile', ['resource_type'], unique=True, postgresql_where=sa.text('scope_id IS NULL'), sqlite_where=sa.text('scope_id IS NULL'))
    op.create_table('healthcare_service',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_id', sa.BigInteger(), server_default=sa.text("nextval('healthcare_service_pub_seq')"), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('provided_by_reference', sa.String(), nullable=True),
    sa.Column('provided_by_type', _organization_reference_type, nullable=True),
    sa.Column('provided_by_id', sa.BigInteger(), nullable=True),
    sa.Column('provided_by_display', sa.String(), nullable=True),
    sa.Column('provided_by_identifier_use', _identifier_use, nullable=True),
    sa.Column('provided_by_identifier_type_system', sa.String(), nullable=True),
    sa.Column('provided_by_identifier_type_version', sa.String(), nullable=True),
    sa.Column('provided_by_identifier_type_code', sa.String(), nullable=True),
    sa.Column('provided_by_identifier_type_display', sa.String(), nullable=True),
    sa.Column('provided_by_identifier_type_text', sa.String(), nullable=True),
    sa.Column('provided_by_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('provided_by_identifier_system', sa.String(), nullable=True),
    sa.Column('provided_by_identifier_value', sa.String(), nullable=True),
    sa.Column('provided_by_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('provided_by_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('extra_details', sa.Text(), nullable=True),
    sa.Column('photo_content_type', sa.String(), nullable=True),
    sa.Column('photo_language', sa.String(), nullable=True),
    sa.Column('photo_data', sa.Text(), nullable=True),
    sa.Column('photo_url', sa.String(), nullable=True),
    sa.Column('photo_size', sa.Integer(), nullable=True),
    sa.Column('photo_hash', sa.String(), nullable=True),
    sa.Column('photo_title', sa.String(), nullable=True),
    sa.Column('photo_creation', sa.DateTime(timezone=True), nullable=True),
    sa.Column('appointment_required', sa.Boolean(), nullable=True),
    sa.Column('availability_exceptions', sa.Text(), nullable=True),
    sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_healthcare_service_created_at'), 'healthcare_service', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_healthcare_service_id'), 'healthcare_service', ['healthcare_service_id'], unique=True)
    op.create_index(op.f('ix_healthcare_service_id'), 'healthcare_service', ['id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_name'), 'healthcare_service', ['name'], unique=False)
    op.create_index(op.f('ix_healthcare_service_provided_by_id'), 'healthcare_service', ['provided_by_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_tenant_id'), 'healthcare_service', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_updated_at'), 'healthcare_service', ['updated_at'], unique=False)
    op.create_table('location',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('location_id', sa.BigInteger(), server_default=sa.text("nextval('location_pub_seq')"), nullable=False),
    sa.Column('status', _location_status, nullable=True),
    sa.Column('operational_status_system', sa.String(), nullable=True),
    sa.Column('operational_status_version', sa.String(), nullable=True),
    sa.Column('operational_status_code', sa.String(), nullable=True),
    sa.Column('operational_status_display', sa.String(), nullable=True),
    sa.Column('operational_status_user_selected', sa.Boolean(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('mode', _location_mode, nullable=True),
    sa.Column('physical_type_text', sa.String(), nullable=True),
    sa.Column('managing_organization_reference', sa.String(), nullable=True),
    sa.Column('managing_organization_type', _organization_reference_type, nullable=True),
    sa.Column('managing_organization_id', sa.BigInteger(), nullable=True),
    sa.Column('managing_organization_display', sa.String(), nullable=True),
    sa.Column('managing_organization_identifier_use', _identifier_use, nullable=True),
    sa.Column('managing_organization_identifier_type_system', sa.String(), nullable=True),
    sa.Column('managing_organization_identifier_type_version', sa.String(), nullable=True),
    sa.Column('managing_organization_identifier_type_code', sa.String(), nullable=True),
    sa.Column('managing_organization_identifier_type_display', sa.String(), nullable=True),
    sa.Column('managing_organization_identifier_type_text', sa.String(), nullable=True),
    sa.Column('managing_organization_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('managing_organization_identifier_system', sa.String(), nullable=True),
    sa.Column('managing_organization_identifier_value', sa.String(), nullable=True),
    sa.Column('managing_organization_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('managing_organization_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('part_of_reference', sa.String(), nullable=True),
    sa.Column('part_of_type', _location_part_of_reference_type, nullable=True),
    sa.Column('part_of_id', sa.BigInteger(), nullable=True),
    sa.Column('part_of_display', sa.String(), nullable=True),
    sa.Column('part_of_identifier_use', _identifier_use, nullable=True),
    sa.Column('part_of_identifier_type_system', sa.String(), nullable=True),
    sa.Column('part_of_identifier_type_version', sa.String(), nullable=True),
    sa.Column('part_of_identifier_type_code', sa.String(), nullable=True),
    sa.Column('part_of_identifier_type_display', sa.String(), nullable=True),
    sa.Column('part_of_identifier_type_text', sa.String(), nullable=True),
    sa.Column('part_of_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('part_of_identifier_system', sa.String(), nullable=True),
    sa.Column('part_of_identifier_value', sa.String(), nullable=True),
    sa.Column('part_of_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('part_of_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('availability_exceptions', sa.Text(), nullable=True),
    sa.Column('position_longitude', sa.Numeric(precision=18, scale=8), nullable=True),
    sa.Column('position_latitude', sa.Numeric(precision=18, scale=8), nullable=True),
    sa.Column('position_altitude', sa.Numeric(precision=18, scale=8), nullable=True),
    sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
    sa.Column('address_use', _address_use, nullable=True),
    sa.Column('address_type', _address_type, nullable=True),
    sa.Column('address_text', sa.String(), nullable=True),
    sa.Column('address_line', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('address_city', sa.String(), nullable=True),
    sa.Column('address_district', sa.String(), nullable=True),
    sa.Column('address_state', sa.String(), nullable=True),
    sa.Column('address_postal_code', sa.String(), nullable=True),
    sa.Column('address_country', sa.String(), nullable=True),
    sa.Column('address_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('address_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint('(position_longitude IS NULL) = (position_latitude IS NULL)', name='ck_location_position_lat_long_together'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_location_created_at'), 'location', ['created_at'], unique=False)
    op.create_index(op.f('ix_location_id'), 'location', ['id'], unique=False)
    op.create_index(op.f('ix_location_location_id'), 'location', ['location_id'], unique=True)
    op.create_index(op.f('ix_location_managing_organization_id'), 'location', ['managing_organization_id'], unique=False)
    op.create_index(op.f('ix_location_name'), 'location', ['name'], unique=False)
    op.create_index(op.f('ix_location_part_of_id'), 'location', ['part_of_id'], unique=False)
    op.create_index(op.f('ix_location_tenant_id'), 'location', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_location_updated_at'), 'location', ['updated_at'], unique=False)
    op.create_table('organization',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('organization_id', sa.BigInteger(), server_default=sa.text("nextval('organization_pub_seq')"), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('partof_reference', sa.String(), nullable=True),
    sa.Column('partof_id', sa.BigInteger(), nullable=True),
    sa.Column('partof_type', _organization_reference_type, nullable=True),
    sa.Column('partof_display', sa.String(), nullable=True),
    sa.Column('partof_identifier_use', _identifier_use, nullable=True),
    sa.Column('partof_identifier_type_system', sa.String(), nullable=True),
    sa.Column('partof_identifier_type_version', sa.String(), nullable=True),
    sa.Column('partof_identifier_type_code', sa.String(), nullable=True),
    sa.Column('partof_identifier_type_display', sa.String(), nullable=True),
    sa.Column('partof_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('partof_identifier_type_text', sa.String(), nullable=True),
    sa.Column('partof_identifier_system', sa.String(), nullable=True),
    sa.Column('partof_identifier_value', sa.String(), nullable=True),
    sa.Column('partof_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('partof_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_created_at'), 'organization', ['created_at'], unique=False)
    op.create_index(op.f('ix_organization_id'), 'organization', ['id'], unique=False)
    op.create_index(op.f('ix_organization_organization_id'), 'organization', ['organization_id'], unique=True)
    op.create_index(op.f('ix_organization_partof_id'), 'organization', ['partof_id'], unique=False)
    op.create_index(op.f('ix_organization_tenant_id'), 'organization', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_organization_updated_at'), 'organization', ['updated_at'], unique=False)
    op.create_table('practitioner',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('practitioner_id', sa.BigInteger(), server_default=sa.text("nextval('practitioner_pub_seq')"), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('gender', _administrative_gender, nullable=True),
    sa.Column('birth_date', sa.Date(), nullable=True),
    sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practitioner_created_at'), 'practitioner', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_id'), 'practitioner', ['id'], unique=False)
    op.create_index(op.f('ix_practitioner_practitioner_id'), 'practitioner', ['practitioner_id'], unique=True)
    op.create_index(op.f('ix_practitioner_tenant_id'), 'practitioner', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_updated_at'), 'practitioner', ['updated_at'], unique=False)
    op.create_index(op.f('ix_practitioner_user_id'), 'practitioner', ['user_id'], unique=False)
    op.create_table('practitioner_role',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('practitioner_role_id', sa.BigInteger(), server_default=sa.text("nextval('practitioner_role_pub_seq')"), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('practitioner_reference', sa.String(), nullable=True),
    sa.Column('practitioner_type', _practitioner_reference_type, nullable=True),
    sa.Column('practitioner_id', sa.BigInteger(), nullable=True),
    sa.Column('practitioner_display', sa.String(), nullable=True),
    sa.Column('practitioner_identifier_use', _identifier_use, nullable=True),
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
    sa.Column('organization_reference', sa.String(), nullable=True),
    sa.Column('organization_type', _organization_reference_type, nullable=True),
    sa.Column('organization_id', sa.BigInteger(), nullable=True),
    sa.Column('organization_display', sa.String(), nullable=True),
    sa.Column('organization_identifier_use', _identifier_use, nullable=True),
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
    sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practitioner_role_created_at'), 'practitioner_role', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_id'), 'practitioner_role', ['id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_organization_id'), 'practitioner_role', ['organization_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_practitioner_id'), 'practitioner_role', ['practitioner_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_practitioner_role_id'), 'practitioner_role', ['practitioner_role_id'], unique=True)
    op.create_index(op.f('ix_practitioner_role_tenant_id'), 'practitioner_role', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_updated_at'), 'practitioner_role', ['updated_at'], unique=False)
    op.create_table('schedule',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('schedule_id', sa.BigInteger(), server_default=sa.text("nextval('schedule_pub_seq')"), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('planning_horizon_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('planning_horizon_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedule_created_at'), 'schedule', ['created_at'], unique=False)
    op.create_index(op.f('ix_schedule_id'), 'schedule', ['id'], unique=False)
    op.create_index(op.f('ix_schedule_schedule_id'), 'schedule', ['schedule_id'], unique=True)
    op.create_index(op.f('ix_schedule_tenant_id'), 'schedule', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_schedule_updated_at'), 'schedule', ['updated_at'], unique=False)
    op.create_table('slot',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('slot_id', sa.BigInteger(), server_default=sa.text("nextval('slot_pub_seq')"), nullable=False),
    sa.Column('schedule_reference', sa.String(), nullable=True),
    sa.Column('schedule_type', _schedule_reference_type, nullable=False),
    sa.Column('schedule_id', sa.BigInteger(), nullable=False),
    sa.Column('schedule_display', sa.String(), nullable=True),
    sa.Column('schedule_identifier_use', _identifier_use, nullable=True),
    sa.Column('schedule_identifier_type_system', sa.String(), nullable=True),
    sa.Column('schedule_identifier_type_version', sa.String(), nullable=True),
    sa.Column('schedule_identifier_type_code', sa.String(), nullable=True),
    sa.Column('schedule_identifier_type_display', sa.String(), nullable=True),
    sa.Column('schedule_identifier_type_text', sa.String(), nullable=True),
    sa.Column('schedule_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('schedule_identifier_system', sa.String(), nullable=True),
    sa.Column('schedule_identifier_value', sa.String(), nullable=True),
    sa.Column('schedule_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('schedule_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', _slot_status, nullable=False),
    sa.Column('start', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end', sa.DateTime(timezone=True), nullable=False),
    sa.Column('appointment_type_text', sa.String(), nullable=True),
    sa.Column('overbooked', sa.Boolean(), nullable=True),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_slot_created_at'), 'slot', ['created_at'], unique=False)
    op.create_index(op.f('ix_slot_id'), 'slot', ['id'], unique=False)
    op.create_index(op.f('ix_slot_schedule_id'), 'slot', ['schedule_id'], unique=False)
    op.create_index(op.f('ix_slot_slot_id'), 'slot', ['slot_id'], unique=True)
    op.create_index(op.f('ix_slot_tenant_id'), 'slot', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_slot_updated_at'), 'slot', ['updated_at'], unique=False)
    op.create_table('terminology_code_system',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('canonical_url', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('fhir_version', sa.String(), nullable=True),
    sa.Column('publisher', sa.String(), nullable=True),
    sa.Column('jurisdiction', sa.String(), nullable=True),
    sa.Column('content_mode', sa.String(), nullable=True),
    sa.Column('experimental', sa.Boolean(), nullable=True),
    sa.Column('active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_terminology_code_system_canonical_url'), 'terminology_code_system', ['canonical_url'], unique=True)
    op.create_table('terminology_value_set',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('canonical_url', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('version', sa.String(), nullable=True),
    sa.Column('fhir_version', sa.String(), nullable=True),
    sa.Column('binding_strength', sa.String(), nullable=False),
    sa.Column('experimental', sa.Boolean(), nullable=True),
    sa.Column('active', sa.Boolean(), server_default=sa.text('true'), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_terminology_value_set_canonical_url'), 'terminology_value_set', ['canonical_url'], unique=True)
    op.create_table('healthcare_service_available_time',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_pk', sa.BigInteger(), nullable=False),
    sa.Column('days_of_week', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('all_day', sa.Boolean(), nullable=True),
    sa.Column('available_start_time', sa.Time(), nullable=True),
    sa.Column('available_end_time', sa.Time(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['healthcare_service_pk'], ['healthcare_service.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_healthcare_service_available_time_created_at'), 'healthcare_service_available_time', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_available_time_healthcare_service_pk'), 'healthcare_service_available_time', ['healthcare_service_pk'], unique=False)
    op.create_index(op.f('ix_healthcare_service_available_time_tenant_id'), 'healthcare_service_available_time', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_available_time_updated_at'), 'healthcare_service_available_time', ['updated_at'], unique=False)
    op.create_table('healthcare_service_category',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['healthcare_service_pk'], ['healthcare_service.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_healthcare_service_category_created_at'), 'healthcare_service_category', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_category_healthcare_service_pk'), 'healthcare_service_category', ['healthcare_service_pk'], unique=False)
    op.create_index(op.f('ix_healthcare_service_category_tenant_id'), 'healthcare_service_category', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_category_updated_at'), 'healthcare_service_category', ['updated_at'], unique=False)
    op.create_table('healthcare_service_characteristic',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['healthcare_service_pk'], ['healthcare_service.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_healthcare_service_characteristic_created_at'), 'healthcare_service_characteristic', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_characteristic_healthcare_service_pk'), 'healthcare_service_characteristic', ['healthcare_service_pk'], unique=False)
    op.create_index(op.f('ix_healthcare_service_characteristic_tenant_id'), 'healthcare_service_characteristic', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_characteristic_updated_at'), 'healthcare_service_characteristic', ['updated_at'], unique=False)
    op.create_table('healthcare_service_communication',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['healthcare_service_pk'], ['healthcare_service.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_healthcare_service_communication_created_at'), 'healthcare_service_communication', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_communication_healthcare_service_pk'), 'healthcare_service_communication', ['healthcare_service_pk'], unique=False)
    op.create_index(op.f('ix_healthcare_service_communication_tenant_id'), 'healthcare_service_communication', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_communication_updated_at'), 'healthcare_service_communication', ['updated_at'], unique=False)
    op.create_table('healthcare_service_coverage_area',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', _healthcare_service_coverage_area_reference_type, nullable=True),
    sa.Column('reference_id', sa.BigInteger(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_use', _identifier_use, nullable=True),
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
    sa.ForeignKeyConstraint(['healthcare_service_pk'], ['healthcare_service.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('healthcare_service_pk', 'reference_type', 'reference_id', name='uq_healthcare_service_coverage_area_reference')
    )
    op.create_index(op.f('ix_healthcare_service_coverage_area_created_at'), 'healthcare_service_coverage_area', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_coverage_area_healthcare_service_pk'), 'healthcare_service_coverage_area', ['healthcare_service_pk'], unique=False)
    op.create_index(op.f('ix_healthcare_service_coverage_area_reference_id'), 'healthcare_service_coverage_area', ['reference_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_coverage_area_tenant_id'), 'healthcare_service_coverage_area', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_coverage_area_updated_at'), 'healthcare_service_coverage_area', ['updated_at'], unique=False)
    op.create_table('healthcare_service_eligibility',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_pk', sa.BigInteger(), nullable=False),
    sa.Column('code_text', sa.String(), nullable=True),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['healthcare_service_pk'], ['healthcare_service.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_healthcare_service_eligibility_created_at'), 'healthcare_service_eligibility', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_eligibility_healthcare_service_pk'), 'healthcare_service_eligibility', ['healthcare_service_pk'], unique=False)
    op.create_index(op.f('ix_healthcare_service_eligibility_tenant_id'), 'healthcare_service_eligibility', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_eligibility_updated_at'), 'healthcare_service_eligibility', ['updated_at'], unique=False)
    op.create_table('healthcare_service_endpoint',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', _healthcare_service_endpoint_reference_type, nullable=True),
    sa.Column('reference_id', sa.BigInteger(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_use', _identifier_use, nullable=True),
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
    sa.ForeignKeyConstraint(['healthcare_service_pk'], ['healthcare_service.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('healthcare_service_pk', 'reference_type', 'reference_id', name='uq_healthcare_service_endpoint_reference')
    )
    op.create_index(op.f('ix_healthcare_service_endpoint_created_at'), 'healthcare_service_endpoint', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_endpoint_healthcare_service_pk'), 'healthcare_service_endpoint', ['healthcare_service_pk'], unique=False)
    op.create_index(op.f('ix_healthcare_service_endpoint_reference_id'), 'healthcare_service_endpoint', ['reference_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_endpoint_tenant_id'), 'healthcare_service_endpoint', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_endpoint_updated_at'), 'healthcare_service_endpoint', ['updated_at'], unique=False)
    op.create_table('healthcare_service_identifier',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_pk', sa.BigInteger(), nullable=False),
    sa.Column('use', _identifier_use, nullable=True),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('assigner_reference', sa.String(), nullable=True),
    sa.Column('assigner_type', _organization_reference_type, nullable=True),
    sa.Column('assigner_id', sa.BigInteger(), nullable=True),
    sa.Column('assigner_display', sa.String(), nullable=True),
    sa.Column('assigner_identifier_use', _identifier_use, nullable=True),
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
    sa.ForeignKeyConstraint(['healthcare_service_pk'], ['healthcare_service.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('system', 'value', name='uq_healthcare_service_identifier_system_value')
    )
    op.create_index(op.f('ix_healthcare_service_identifier_assigner_id'), 'healthcare_service_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_identifier_created_at'), 'healthcare_service_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_identifier_healthcare_service_pk'), 'healthcare_service_identifier', ['healthcare_service_pk'], unique=False)
    op.create_index(op.f('ix_healthcare_service_identifier_tenant_id'), 'healthcare_service_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_identifier_updated_at'), 'healthcare_service_identifier', ['updated_at'], unique=False)
    op.create_table('healthcare_service_location',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', _healthcare_service_location_reference_type, nullable=True),
    sa.Column('reference_id', sa.BigInteger(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_use', _identifier_use, nullable=True),
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
    sa.ForeignKeyConstraint(['healthcare_service_pk'], ['healthcare_service.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('healthcare_service_pk', 'reference_type', 'reference_id', name='uq_healthcare_service_location_reference')
    )
    op.create_index(op.f('ix_healthcare_service_location_created_at'), 'healthcare_service_location', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_location_healthcare_service_pk'), 'healthcare_service_location', ['healthcare_service_pk'], unique=False)
    op.create_index(op.f('ix_healthcare_service_location_reference_id'), 'healthcare_service_location', ['reference_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_location_tenant_id'), 'healthcare_service_location', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_location_updated_at'), 'healthcare_service_location', ['updated_at'], unique=False)
    op.create_table('healthcare_service_not_available',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_pk', sa.BigInteger(), nullable=False),
    sa.Column('description', sa.String(), nullable=False),
    sa.Column('during_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('during_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['healthcare_service_pk'], ['healthcare_service.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_healthcare_service_not_available_created_at'), 'healthcare_service_not_available', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_not_available_healthcare_service_pk'), 'healthcare_service_not_available', ['healthcare_service_pk'], unique=False)
    op.create_index(op.f('ix_healthcare_service_not_available_tenant_id'), 'healthcare_service_not_available', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_not_available_updated_at'), 'healthcare_service_not_available', ['updated_at'], unique=False)
    op.create_table('healthcare_service_program',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['healthcare_service_pk'], ['healthcare_service.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_healthcare_service_program_created_at'), 'healthcare_service_program', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_program_healthcare_service_pk'), 'healthcare_service_program', ['healthcare_service_pk'], unique=False)
    op.create_index(op.f('ix_healthcare_service_program_tenant_id'), 'healthcare_service_program', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_program_updated_at'), 'healthcare_service_program', ['updated_at'], unique=False)
    op.create_table('healthcare_service_referral_method',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['healthcare_service_pk'], ['healthcare_service.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_healthcare_service_referral_method_created_at'), 'healthcare_service_referral_method', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_referral_method_healthcare_service_pk'), 'healthcare_service_referral_method', ['healthcare_service_pk'], unique=False)
    op.create_index(op.f('ix_healthcare_service_referral_method_tenant_id'), 'healthcare_service_referral_method', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_referral_method_updated_at'), 'healthcare_service_referral_method', ['updated_at'], unique=False)
    op.create_table('healthcare_service_service_provision_code',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['healthcare_service_pk'], ['healthcare_service.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_healthcare_service_service_provision_code_created_at'), 'healthcare_service_service_provision_code', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_service_provision_code_healthcare_service_pk'), 'healthcare_service_service_provision_code', ['healthcare_service_pk'], unique=False)
    op.create_index(op.f('ix_healthcare_service_service_provision_code_tenant_id'), 'healthcare_service_service_provision_code', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_service_provision_code_updated_at'), 'healthcare_service_service_provision_code', ['updated_at'], unique=False)
    op.create_table('healthcare_service_specialty',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['healthcare_service_pk'], ['healthcare_service.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_healthcare_service_specialty_created_at'), 'healthcare_service_specialty', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_specialty_healthcare_service_pk'), 'healthcare_service_specialty', ['healthcare_service_pk'], unique=False)
    op.create_index(op.f('ix_healthcare_service_specialty_tenant_id'), 'healthcare_service_specialty', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_specialty_updated_at'), 'healthcare_service_specialty', ['updated_at'], unique=False)
    op.create_table('healthcare_service_telecom',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_pk', sa.BigInteger(), nullable=False),
    sa.Column('system', _contact_point_system, nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('use', _contact_point_use, nullable=True),
    sa.Column('rank', sa.Integer(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['healthcare_service_pk'], ['healthcare_service.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_healthcare_service_telecom_created_at'), 'healthcare_service_telecom', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_telecom_healthcare_service_pk'), 'healthcare_service_telecom', ['healthcare_service_pk'], unique=False)
    op.create_index(op.f('ix_healthcare_service_telecom_tenant_id'), 'healthcare_service_telecom', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_telecom_updated_at'), 'healthcare_service_telecom', ['updated_at'], unique=False)
    op.create_table('healthcare_service_type',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['healthcare_service_pk'], ['healthcare_service.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_healthcare_service_type_created_at'), 'healthcare_service_type', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_type_healthcare_service_pk'), 'healthcare_service_type', ['healthcare_service_pk'], unique=False)
    op.create_index(op.f('ix_healthcare_service_type_tenant_id'), 'healthcare_service_type', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_type_updated_at'), 'healthcare_service_type', ['updated_at'], unique=False)
    op.create_table('location_alias',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('location_pk', sa.BigInteger(), nullable=False),
    sa.Column('value', sa.String(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['location_pk'], ['location.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_location_alias_created_at'), 'location_alias', ['created_at'], unique=False)
    op.create_index(op.f('ix_location_alias_location_pk'), 'location_alias', ['location_pk'], unique=False)
    op.create_index(op.f('ix_location_alias_tenant_id'), 'location_alias', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_location_alias_updated_at'), 'location_alias', ['updated_at'], unique=False)
    op.create_table('location_endpoint',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('location_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', _location_endpoint_reference_type, nullable=True),
    sa.Column('reference_id', sa.BigInteger(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_use', _identifier_use, nullable=True),
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
    sa.ForeignKeyConstraint(['location_pk'], ['location.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('location_pk', 'reference_type', 'reference_id', name='uq_location_endpoint_reference')
    )
    op.create_index(op.f('ix_location_endpoint_created_at'), 'location_endpoint', ['created_at'], unique=False)
    op.create_index(op.f('ix_location_endpoint_location_pk'), 'location_endpoint', ['location_pk'], unique=False)
    op.create_index(op.f('ix_location_endpoint_reference_id'), 'location_endpoint', ['reference_id'], unique=False)
    op.create_index(op.f('ix_location_endpoint_tenant_id'), 'location_endpoint', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_location_endpoint_updated_at'), 'location_endpoint', ['updated_at'], unique=False)
    op.create_table('location_hours_of_operation',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('location_pk', sa.BigInteger(), nullable=False),
    sa.Column('days_of_week', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('all_day', sa.Boolean(), nullable=True),
    sa.Column('opening_time', sa.Time(), nullable=True),
    sa.Column('closing_time', sa.Time(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['location_pk'], ['location.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_location_hours_of_operation_created_at'), 'location_hours_of_operation', ['created_at'], unique=False)
    op.create_index(op.f('ix_location_hours_of_operation_location_pk'), 'location_hours_of_operation', ['location_pk'], unique=False)
    op.create_index(op.f('ix_location_hours_of_operation_tenant_id'), 'location_hours_of_operation', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_location_hours_of_operation_updated_at'), 'location_hours_of_operation', ['updated_at'], unique=False)
    op.create_table('location_identifier',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('location_pk', sa.BigInteger(), nullable=False),
    sa.Column('use', _identifier_use, nullable=True),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('assigner_reference', sa.String(), nullable=True),
    sa.Column('assigner_type', _organization_reference_type, nullable=True),
    sa.Column('assigner_id', sa.BigInteger(), nullable=True),
    sa.Column('assigner_display', sa.String(), nullable=True),
    sa.Column('assigner_identifier_use', _identifier_use, nullable=True),
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
    sa.ForeignKeyConstraint(['location_pk'], ['location.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('system', 'value', name='uq_location_identifier_system_value')
    )
    op.create_index(op.f('ix_location_identifier_assigner_id'), 'location_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_location_identifier_created_at'), 'location_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_location_identifier_location_pk'), 'location_identifier', ['location_pk'], unique=False)
    op.create_index(op.f('ix_location_identifier_tenant_id'), 'location_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_location_identifier_updated_at'), 'location_identifier', ['updated_at'], unique=False)
    op.create_table('location_physical_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('location_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['location_pk'], ['location.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_location_physical_type_coding_created_at'), 'location_physical_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_location_physical_type_coding_location_pk'), 'location_physical_type_coding', ['location_pk'], unique=False)
    op.create_index(op.f('ix_location_physical_type_coding_tenant_id'), 'location_physical_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_location_physical_type_coding_updated_at'), 'location_physical_type_coding', ['updated_at'], unique=False)
    op.create_table('location_telecom',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('location_pk', sa.BigInteger(), nullable=False),
    sa.Column('system', _contact_point_system, nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('use', _contact_point_use, nullable=True),
    sa.Column('rank', sa.Integer(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['location_pk'], ['location.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_location_telecom_created_at'), 'location_telecom', ['created_at'], unique=False)
    op.create_index(op.f('ix_location_telecom_location_pk'), 'location_telecom', ['location_pk'], unique=False)
    op.create_index(op.f('ix_location_telecom_tenant_id'), 'location_telecom', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_location_telecom_updated_at'), 'location_telecom', ['updated_at'], unique=False)
    op.create_table('location_type',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('location_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['location_pk'], ['location.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_location_type_created_at'), 'location_type', ['created_at'], unique=False)
    op.create_index(op.f('ix_location_type_location_pk'), 'location_type', ['location_pk'], unique=False)
    op.create_index(op.f('ix_location_type_tenant_id'), 'location_type', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_location_type_updated_at'), 'location_type', ['updated_at'], unique=False)
    op.create_table('organization_address',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('organization_pk', sa.BigInteger(), nullable=False),
    sa.Column('use', _address_use, nullable=True),
    sa.Column('type', _address_type, nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('line', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('city', sa.String(), nullable=True),
    sa.Column('district', sa.String(), nullable=True),
    sa.Column('state', sa.String(), nullable=True),
    sa.Column('postal_code', sa.String(), nullable=True),
    sa.Column('country', sa.String(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['organization_pk'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_address_created_at'), 'organization_address', ['created_at'], unique=False)
    op.create_index(op.f('ix_organization_address_organization_pk'), 'organization_address', ['organization_pk'], unique=False)
    op.create_index(op.f('ix_organization_address_tenant_id'), 'organization_address', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_organization_address_updated_at'), 'organization_address', ['updated_at'], unique=False)
    op.create_table('organization_alias',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('organization_pk', sa.BigInteger(), nullable=False),
    sa.Column('value', sa.String(), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['organization_pk'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_alias_created_at'), 'organization_alias', ['created_at'], unique=False)
    op.create_index(op.f('ix_organization_alias_organization_pk'), 'organization_alias', ['organization_pk'], unique=False)
    op.create_index(op.f('ix_organization_alias_tenant_id'), 'organization_alias', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_organization_alias_updated_at'), 'organization_alias', ['updated_at'], unique=False)
    op.create_table('organization_contact',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('organization_pk', sa.BigInteger(), nullable=False),
    sa.Column('purpose_text', sa.String(), nullable=True),
    sa.Column('name_use', _human_name_use, nullable=True),
    sa.Column('name_text', sa.String(), nullable=True),
    sa.Column('name_family', sa.String(), nullable=True),
    sa.Column('name_given', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('name_prefix', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('name_suffix', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('name_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('name_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('address_use', _address_use, nullable=True),
    sa.Column('address_type', _address_type, nullable=True),
    sa.Column('address_text', sa.String(), nullable=True),
    sa.Column('address_line', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('address_city', sa.String(), nullable=True),
    sa.Column('address_district', sa.String(), nullable=True),
    sa.Column('address_state', sa.String(), nullable=True),
    sa.Column('address_postal_code', sa.String(), nullable=True),
    sa.Column('address_country', sa.String(), nullable=True),
    sa.Column('address_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('address_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['organization_pk'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_contact_created_at'), 'organization_contact', ['created_at'], unique=False)
    op.create_index(op.f('ix_organization_contact_organization_pk'), 'organization_contact', ['organization_pk'], unique=False)
    op.create_index(op.f('ix_organization_contact_tenant_id'), 'organization_contact', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_organization_contact_updated_at'), 'organization_contact', ['updated_at'], unique=False)
    op.create_table('organization_endpoint',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('organization_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_id', sa.BigInteger(), nullable=True),
    sa.Column('reference_type', _organization_endpoint_ref_type, nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_use', _identifier_use, nullable=True),
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
    sa.ForeignKeyConstraint(['organization_pk'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_endpoint_created_at'), 'organization_endpoint', ['created_at'], unique=False)
    op.create_index(op.f('ix_organization_endpoint_organization_pk'), 'organization_endpoint', ['organization_pk'], unique=False)
    op.create_index(op.f('ix_organization_endpoint_reference_id'), 'organization_endpoint', ['reference_id'], unique=False)
    op.create_index(op.f('ix_organization_endpoint_tenant_id'), 'organization_endpoint', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_organization_endpoint_updated_at'), 'organization_endpoint', ['updated_at'], unique=False)
    op.create_table('organization_identifier',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('organization_pk', sa.BigInteger(), nullable=False),
    sa.Column('use', _identifier_use, nullable=True),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('assigner_reference', sa.String(), nullable=True),
    sa.Column('assigner_id', sa.BigInteger(), nullable=True),
    sa.Column('assigner_type', _organization_reference_type, nullable=True),
    sa.Column('assigner_display', sa.String(), nullable=True),
    sa.Column('assigner_identifier_use', _identifier_use, nullable=True),
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
    sa.ForeignKeyConstraint(['organization_pk'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_identifier_assigner_id'), 'organization_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_organization_identifier_created_at'), 'organization_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_organization_identifier_organization_pk'), 'organization_identifier', ['organization_pk'], unique=False)
    op.create_index(op.f('ix_organization_identifier_tenant_id'), 'organization_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_organization_identifier_updated_at'), 'organization_identifier', ['updated_at'], unique=False)
    op.create_table('organization_telecom',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('organization_pk', sa.BigInteger(), nullable=False),
    sa.Column('system', _contact_point_system, nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('use', _contact_point_use, nullable=True),
    sa.Column('rank', sa.Integer(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['organization_pk'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_telecom_created_at'), 'organization_telecom', ['created_at'], unique=False)
    op.create_index(op.f('ix_organization_telecom_organization_pk'), 'organization_telecom', ['organization_pk'], unique=False)
    op.create_index(op.f('ix_organization_telecom_tenant_id'), 'organization_telecom', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_organization_telecom_updated_at'), 'organization_telecom', ['updated_at'], unique=False)
    op.create_table('organization_type',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('organization_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['organization_pk'], ['organization.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_type_created_at'), 'organization_type', ['created_at'], unique=False)
    op.create_index(op.f('ix_organization_type_organization_pk'), 'organization_type', ['organization_pk'], unique=False)
    op.create_index(op.f('ix_organization_type_tenant_id'), 'organization_type', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_organization_type_updated_at'), 'organization_type', ['updated_at'], unique=False)
    op.create_table('practitioner_address',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('practitioner_pk', sa.BigInteger(), nullable=False),
    sa.Column('use', _address_use, nullable=True),
    sa.Column('type', _address_type, nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('line', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('city', sa.String(), nullable=True),
    sa.Column('district', sa.String(), nullable=True),
    sa.Column('state', sa.String(), nullable=True),
    sa.Column('postal_code', sa.String(), nullable=True),
    sa.Column('country', sa.String(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['practitioner_pk'], ['practitioner.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practitioner_address_created_at'), 'practitioner_address', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_address_practitioner_pk'), 'practitioner_address', ['practitioner_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_address_tenant_id'), 'practitioner_address', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_address_updated_at'), 'practitioner_address', ['updated_at'], unique=False)
    op.create_table('practitioner_communication',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('practitioner_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['practitioner_pk'], ['practitioner.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practitioner_communication_created_at'), 'practitioner_communication', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_communication_practitioner_pk'), 'practitioner_communication', ['practitioner_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_communication_tenant_id'), 'practitioner_communication', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_communication_updated_at'), 'practitioner_communication', ['updated_at'], unique=False)
    op.create_table('practitioner_identifier',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('practitioner_pk', sa.BigInteger(), nullable=False),
    sa.Column('use', _identifier_use, nullable=True),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('assigner_reference', sa.String(), nullable=True),
    sa.Column('assigner_id', sa.BigInteger(), nullable=True),
    sa.Column('assigner_type', _organization_reference_type, nullable=True),
    sa.Column('assigner_display', sa.String(), nullable=True),
    sa.Column('assigner_identifier_use', _identifier_use, nullable=True),
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
    sa.ForeignKeyConstraint(['practitioner_pk'], ['practitioner.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practitioner_identifier_assigner_id'), 'practitioner_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_practitioner_identifier_created_at'), 'practitioner_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_identifier_practitioner_pk'), 'practitioner_identifier', ['practitioner_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_identifier_tenant_id'), 'practitioner_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_identifier_updated_at'), 'practitioner_identifier', ['updated_at'], unique=False)
    op.create_table('practitioner_name',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('practitioner_pk', sa.BigInteger(), nullable=False),
    sa.Column('use', _human_name_use, nullable=True),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('family', sa.String(), nullable=True),
    sa.Column('given', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('prefix', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('suffix', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['practitioner_pk'], ['practitioner.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practitioner_name_created_at'), 'practitioner_name', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_name_practitioner_pk'), 'practitioner_name', ['practitioner_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_name_tenant_id'), 'practitioner_name', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_name_updated_at'), 'practitioner_name', ['updated_at'], unique=False)
    op.create_table('practitioner_photo',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('practitioner_pk', sa.BigInteger(), nullable=False),
    sa.Column('content_type', sa.String(), nullable=True),
    sa.Column('language', sa.String(), nullable=True),
    sa.Column('data', sa.Text(), nullable=True),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('size', sa.Integer(), nullable=True),
    sa.Column('hash', sa.String(), nullable=True),
    sa.Column('title', sa.String(), nullable=True),
    sa.Column('creation', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['practitioner_pk'], ['practitioner.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practitioner_photo_created_at'), 'practitioner_photo', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_photo_practitioner_pk'), 'practitioner_photo', ['practitioner_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_photo_tenant_id'), 'practitioner_photo', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_photo_updated_at'), 'practitioner_photo', ['updated_at'], unique=False)
    op.create_table('practitioner_qualification',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('practitioner_pk', sa.BigInteger(), nullable=False),
    sa.Column('code_text', sa.String(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('issuer_reference', sa.String(), nullable=True),
    sa.Column('issuer_id', sa.BigInteger(), nullable=True),
    sa.Column('issuer_type', _organization_reference_type, nullable=True),
    sa.Column('issuer_display', sa.String(), nullable=True),
    sa.Column('issuer_identifier_use', _identifier_use, nullable=True),
    sa.Column('issuer_identifier_type_system', sa.String(), nullable=True),
    sa.Column('issuer_identifier_type_version', sa.String(), nullable=True),
    sa.Column('issuer_identifier_type_code', sa.String(), nullable=True),
    sa.Column('issuer_identifier_type_display', sa.String(), nullable=True),
    sa.Column('issuer_identifier_type_text', sa.String(), nullable=True),
    sa.Column('issuer_identifier_type_user_selected', sa.Boolean(), nullable=True),
    sa.Column('issuer_identifier_system', sa.String(), nullable=True),
    sa.Column('issuer_identifier_value', sa.String(), nullable=True),
    sa.Column('issuer_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('issuer_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['practitioner_pk'], ['practitioner.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practitioner_qualification_created_at'), 'practitioner_qualification', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_qualification_issuer_id'), 'practitioner_qualification', ['issuer_id'], unique=False)
    op.create_index(op.f('ix_practitioner_qualification_practitioner_pk'), 'practitioner_qualification', ['practitioner_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_qualification_tenant_id'), 'practitioner_qualification', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_qualification_updated_at'), 'practitioner_qualification', ['updated_at'], unique=False)
    op.create_table('practitioner_role_available_time',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('practitioner_role_pk', sa.BigInteger(), nullable=False),
    sa.Column('days_of_week', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('all_day', sa.Boolean(), nullable=True),
    sa.Column('available_start_time', sa.Time(), nullable=True),
    sa.Column('available_end_time', sa.Time(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['practitioner_role_pk'], ['practitioner_role.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practitioner_role_available_time_created_at'), 'practitioner_role_available_time', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_available_time_practitioner_role_pk'), 'practitioner_role_available_time', ['practitioner_role_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_role_available_time_tenant_id'), 'practitioner_role_available_time', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_available_time_updated_at'), 'practitioner_role_available_time', ['updated_at'], unique=False)
    op.create_table('practitioner_role_code',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('practitioner_role_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['practitioner_role_pk'], ['practitioner_role.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practitioner_role_code_created_at'), 'practitioner_role_code', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_code_practitioner_role_pk'), 'practitioner_role_code', ['practitioner_role_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_role_code_tenant_id'), 'practitioner_role_code', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_code_updated_at'), 'practitioner_role_code', ['updated_at'], unique=False)
    op.create_table('practitioner_role_endpoint',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('practitioner_role_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', _practitioner_role_endpoint_reference_type, nullable=True),
    sa.Column('reference_id', sa.BigInteger(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_use', _identifier_use, nullable=True),
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
    sa.UniqueConstraint('practitioner_role_pk', 'reference_type', 'reference_id', name='uq_practitioner_role_endpoint_reference')
    )
    op.create_index(op.f('ix_practitioner_role_endpoint_created_at'), 'practitioner_role_endpoint', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_endpoint_practitioner_role_pk'), 'practitioner_role_endpoint', ['practitioner_role_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_role_endpoint_reference_id'), 'practitioner_role_endpoint', ['reference_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_endpoint_tenant_id'), 'practitioner_role_endpoint', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_endpoint_updated_at'), 'practitioner_role_endpoint', ['updated_at'], unique=False)
    op.create_table('practitioner_role_healthcare_service',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('practitioner_role_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', _practitioner_role_healthcare_service_reference_type, nullable=True),
    sa.Column('reference_id', sa.BigInteger(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_use', _identifier_use, nullable=True),
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
    sa.UniqueConstraint('practitioner_role_pk', 'reference_type', 'reference_id', name='uq_practitioner_role_healthcare_service_reference')
    )
    op.create_index(op.f('ix_practitioner_role_healthcare_service_created_at'), 'practitioner_role_healthcare_service', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_healthcare_service_practitioner_role_pk'), 'practitioner_role_healthcare_service', ['practitioner_role_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_role_healthcare_service_reference_id'), 'practitioner_role_healthcare_service', ['reference_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_healthcare_service_tenant_id'), 'practitioner_role_healthcare_service', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_healthcare_service_updated_at'), 'practitioner_role_healthcare_service', ['updated_at'], unique=False)
    op.create_table('practitioner_role_identifier',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('practitioner_role_pk', sa.BigInteger(), nullable=False),
    sa.Column('use', _identifier_use, nullable=True),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('assigner_reference', sa.String(), nullable=True),
    sa.Column('assigner_type', _organization_reference_type, nullable=True),
    sa.Column('assigner_id', sa.BigInteger(), nullable=True),
    sa.Column('assigner_display', sa.String(), nullable=True),
    sa.Column('assigner_identifier_use', _identifier_use, nullable=True),
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
    sa.UniqueConstraint('system', 'value', name='uq_practitioner_role_identifier_system_value')
    )
    op.create_index(op.f('ix_practitioner_role_identifier_assigner_id'), 'practitioner_role_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_identifier_created_at'), 'practitioner_role_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_identifier_practitioner_role_pk'), 'practitioner_role_identifier', ['practitioner_role_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_role_identifier_tenant_id'), 'practitioner_role_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_identifier_updated_at'), 'practitioner_role_identifier', ['updated_at'], unique=False)
    op.create_table('practitioner_role_location',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('practitioner_role_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', _practitioner_role_location_reference_type, nullable=True),
    sa.Column('reference_id', sa.BigInteger(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_use', _identifier_use, nullable=True),
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
    sa.UniqueConstraint('practitioner_role_pk', 'reference_type', 'reference_id', name='uq_practitioner_role_location_reference')
    )
    op.create_index(op.f('ix_practitioner_role_location_created_at'), 'practitioner_role_location', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_location_practitioner_role_pk'), 'practitioner_role_location', ['practitioner_role_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_role_location_reference_id'), 'practitioner_role_location', ['reference_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_location_tenant_id'), 'practitioner_role_location', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_location_updated_at'), 'practitioner_role_location', ['updated_at'], unique=False)
    op.create_table('practitioner_role_not_available',
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
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practitioner_role_not_available_created_at'), 'practitioner_role_not_available', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_not_available_practitioner_role_pk'), 'practitioner_role_not_available', ['practitioner_role_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_role_not_available_tenant_id'), 'practitioner_role_not_available', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_not_available_updated_at'), 'practitioner_role_not_available', ['updated_at'], unique=False)
    op.create_table('practitioner_role_specialty',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('practitioner_role_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['practitioner_role_pk'], ['practitioner_role.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practitioner_role_specialty_created_at'), 'practitioner_role_specialty', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_specialty_practitioner_role_pk'), 'practitioner_role_specialty', ['practitioner_role_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_role_specialty_tenant_id'), 'practitioner_role_specialty', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_specialty_updated_at'), 'practitioner_role_specialty', ['updated_at'], unique=False)
    op.create_table('practitioner_role_telecom',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('practitioner_role_pk', sa.BigInteger(), nullable=False),
    sa.Column('system', _contact_point_system, nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('use', _contact_point_use, nullable=True),
    sa.Column('rank', sa.Integer(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['practitioner_role_pk'], ['practitioner_role.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practitioner_role_telecom_created_at'), 'practitioner_role_telecom', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_telecom_practitioner_role_pk'), 'practitioner_role_telecom', ['practitioner_role_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_role_telecom_tenant_id'), 'practitioner_role_telecom', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_telecom_updated_at'), 'practitioner_role_telecom', ['updated_at'], unique=False)
    op.create_table('practitioner_telecom',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('practitioner_pk', sa.BigInteger(), nullable=False),
    sa.Column('system', _contact_point_system, nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('use', _contact_point_use, nullable=True),
    sa.Column('rank', sa.Integer(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['practitioner_pk'], ['practitioner.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practitioner_telecom_created_at'), 'practitioner_telecom', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_telecom_practitioner_pk'), 'practitioner_telecom', ['practitioner_pk'], unique=False)
    op.create_index(op.f('ix_practitioner_telecom_tenant_id'), 'practitioner_telecom', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_telecom_updated_at'), 'practitioner_telecom', ['updated_at'], unique=False)
    op.create_table('schedule_actor',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('schedule_pk', sa.BigInteger(), nullable=False),
    sa.Column('reference_reference', sa.String(), nullable=True),
    sa.Column('reference_type', _schedule_actor_reference_type, nullable=True),
    sa.Column('reference_id', sa.BigInteger(), nullable=True),
    sa.Column('reference_display', sa.String(), nullable=True),
    sa.Column('reference_identifier_use', _identifier_use, nullable=True),
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
    sa.ForeignKeyConstraint(['schedule_pk'], ['schedule.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('schedule_pk', 'reference_type', 'reference_id', name='uq_schedule_actor_reference')
    )
    op.create_index(op.f('ix_schedule_actor_created_at'), 'schedule_actor', ['created_at'], unique=False)
    op.create_index(op.f('ix_schedule_actor_reference_id'), 'schedule_actor', ['reference_id'], unique=False)
    op.create_index(op.f('ix_schedule_actor_schedule_pk'), 'schedule_actor', ['schedule_pk'], unique=False)
    op.create_index(op.f('ix_schedule_actor_tenant_id'), 'schedule_actor', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_schedule_actor_updated_at'), 'schedule_actor', ['updated_at'], unique=False)
    op.create_table('schedule_identifier',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('schedule_pk', sa.BigInteger(), nullable=False),
    sa.Column('use', _identifier_use, nullable=True),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('assigner_reference', sa.String(), nullable=True),
    sa.Column('assigner_type', _organization_reference_type, nullable=True),
    sa.Column('assigner_id', sa.BigInteger(), nullable=True),
    sa.Column('assigner_display', sa.String(), nullable=True),
    sa.Column('assigner_identifier_use', _identifier_use, nullable=True),
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
    sa.ForeignKeyConstraint(['schedule_pk'], ['schedule.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('system', 'value', name='uq_schedule_identifier_system_value')
    )
    op.create_index(op.f('ix_schedule_identifier_assigner_id'), 'schedule_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_schedule_identifier_created_at'), 'schedule_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_schedule_identifier_schedule_pk'), 'schedule_identifier', ['schedule_pk'], unique=False)
    op.create_index(op.f('ix_schedule_identifier_tenant_id'), 'schedule_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_schedule_identifier_updated_at'), 'schedule_identifier', ['updated_at'], unique=False)
    op.create_table('schedule_service_category',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('schedule_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['schedule_pk'], ['schedule.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedule_service_category_created_at'), 'schedule_service_category', ['created_at'], unique=False)
    op.create_index(op.f('ix_schedule_service_category_schedule_pk'), 'schedule_service_category', ['schedule_pk'], unique=False)
    op.create_index(op.f('ix_schedule_service_category_tenant_id'), 'schedule_service_category', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_schedule_service_category_updated_at'), 'schedule_service_category', ['updated_at'], unique=False)
    op.create_table('schedule_service_type',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('schedule_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['schedule_pk'], ['schedule.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedule_service_type_created_at'), 'schedule_service_type', ['created_at'], unique=False)
    op.create_index(op.f('ix_schedule_service_type_schedule_pk'), 'schedule_service_type', ['schedule_pk'], unique=False)
    op.create_index(op.f('ix_schedule_service_type_tenant_id'), 'schedule_service_type', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_schedule_service_type_updated_at'), 'schedule_service_type', ['updated_at'], unique=False)
    op.create_table('schedule_specialty',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('schedule_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['schedule_pk'], ['schedule.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedule_specialty_created_at'), 'schedule_specialty', ['created_at'], unique=False)
    op.create_index(op.f('ix_schedule_specialty_schedule_pk'), 'schedule_specialty', ['schedule_pk'], unique=False)
    op.create_index(op.f('ix_schedule_specialty_tenant_id'), 'schedule_specialty', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_schedule_specialty_updated_at'), 'schedule_specialty', ['updated_at'], unique=False)
    op.create_table('slot_appointment_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('slot_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['slot_pk'], ['slot.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_slot_appointment_type_coding_created_at'), 'slot_appointment_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_slot_appointment_type_coding_slot_pk'), 'slot_appointment_type_coding', ['slot_pk'], unique=False)
    op.create_index(op.f('ix_slot_appointment_type_coding_tenant_id'), 'slot_appointment_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_slot_appointment_type_coding_updated_at'), 'slot_appointment_type_coding', ['updated_at'], unique=False)
    op.create_table('slot_identifier',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('slot_pk', sa.BigInteger(), nullable=False),
    sa.Column('use', _identifier_use, nullable=True),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('assigner_reference', sa.String(), nullable=True),
    sa.Column('assigner_type', _organization_reference_type, nullable=True),
    sa.Column('assigner_id', sa.BigInteger(), nullable=True),
    sa.Column('assigner_display', sa.String(), nullable=True),
    sa.Column('assigner_identifier_use', _identifier_use, nullable=True),
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
    sa.ForeignKeyConstraint(['slot_pk'], ['slot.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('system', 'value', name='uq_slot_identifier_system_value')
    )
    op.create_index(op.f('ix_slot_identifier_assigner_id'), 'slot_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_slot_identifier_created_at'), 'slot_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_slot_identifier_slot_pk'), 'slot_identifier', ['slot_pk'], unique=False)
    op.create_index(op.f('ix_slot_identifier_tenant_id'), 'slot_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_slot_identifier_updated_at'), 'slot_identifier', ['updated_at'], unique=False)
    op.create_table('slot_service_category',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('slot_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['slot_pk'], ['slot.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_slot_service_category_created_at'), 'slot_service_category', ['created_at'], unique=False)
    op.create_index(op.f('ix_slot_service_category_slot_pk'), 'slot_service_category', ['slot_pk'], unique=False)
    op.create_index(op.f('ix_slot_service_category_tenant_id'), 'slot_service_category', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_slot_service_category_updated_at'), 'slot_service_category', ['updated_at'], unique=False)
    op.create_table('slot_service_type',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('slot_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['slot_pk'], ['slot.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_slot_service_type_created_at'), 'slot_service_type', ['created_at'], unique=False)
    op.create_index(op.f('ix_slot_service_type_slot_pk'), 'slot_service_type', ['slot_pk'], unique=False)
    op.create_index(op.f('ix_slot_service_type_tenant_id'), 'slot_service_type', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_slot_service_type_updated_at'), 'slot_service_type', ['updated_at'], unique=False)
    op.create_table('slot_specialty',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('slot_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['slot_pk'], ['slot.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_slot_specialty_created_at'), 'slot_specialty', ['created_at'], unique=False)
    op.create_index(op.f('ix_slot_specialty_slot_pk'), 'slot_specialty', ['slot_pk'], unique=False)
    op.create_index(op.f('ix_slot_specialty_tenant_id'), 'slot_specialty', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_slot_specialty_updated_at'), 'slot_specialty', ['updated_at'], unique=False)
    op.create_table('terminology_concept',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('code_system_id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(), nullable=False),
    sa.Column('display', sa.String(), nullable=False),
    sa.Column('definition', sa.Text(), nullable=True),
    sa.Column('active', sa.Boolean(), server_default=sa.text('true'), nullable=True),
    sa.Column('deprecated', sa.Boolean(), nullable=True),
    sa.Column('parent_concept_id', sa.Integer(), nullable=True),
    sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True),
    sa.Column('org_id', sa.String(), nullable=True),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['code_system_id'], ['terminology_code_system.id'], ),
    sa.ForeignKeyConstraint(['parent_concept_id'], ['terminology_concept.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_terminology_concept_code'), 'terminology_concept', ['code'], unique=False)
    op.create_index(op.f('ix_terminology_concept_code_system_id'), 'terminology_concept', ['code_system_id'], unique=False)
    op.create_index(op.f('ix_terminology_concept_org_id'), 'terminology_concept', ['org_id'], unique=False)
    op.create_index(op.f('ix_terminology_concept_parent_concept_id'), 'terminology_concept', ['parent_concept_id'], unique=False)
    op.create_index(op.f('ix_terminology_concept_user_id'), 'terminology_concept', ['user_id'], unique=False)
    op.create_index('uq_terminology_concept_system_code_null_org', 'terminology_concept', ['code_system_id', 'code'], unique=True, postgresql_where=sa.text('org_id IS NULL'))
    op.create_index('uq_terminology_concept_system_code_org', 'terminology_concept', ['code_system_id', 'code', 'org_id'], unique=True, postgresql_where=sa.text('org_id IS NOT NULL'))
    op.create_table('terminology_field_binding',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('resource_type', sa.String(), nullable=False),
    sa.Column('field_name', sa.String(), nullable=False),
    sa.Column('value_set_id', sa.Integer(), nullable=False),
    sa.Column('binding_strength', sa.String(), nullable=False),
    sa.Column('multiple_allowed', sa.Boolean(), nullable=True),
    sa.Column('active', sa.Boolean(), server_default=sa.text('true'), nullable=True),
    sa.ForeignKeyConstraint(['value_set_id'], ['terminology_value_set.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('resource_type', 'field_name')
    )
    op.create_index(op.f('ix_terminology_field_binding_resource_type'), 'terminology_field_binding', ['resource_type'], unique=False)
    op.create_index(op.f('ix_terminology_field_binding_value_set_id'), 'terminology_field_binding', ['value_set_id'], unique=False)
    op.create_table('healthcare_service_category_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_category_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['healthcare_service_category_id'], ['healthcare_service_category.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_healthcare_service_category_coding_created_at'), 'healthcare_service_category_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_category_coding_healthcare_service_category_id'), 'healthcare_service_category_coding', ['healthcare_service_category_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_category_coding_tenant_id'), 'healthcare_service_category_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_category_coding_updated_at'), 'healthcare_service_category_coding', ['updated_at'], unique=False)
    op.create_table('healthcare_service_characteristic_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_characteristic_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['healthcare_service_characteristic_id'], ['healthcare_service_characteristic.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_healthcare_service_characteristic_coding_created_at'), 'healthcare_service_characteristic_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_characteristic_coding_healthcare_service_characteristic_id'), 'healthcare_service_characteristic_coding', ['healthcare_service_characteristic_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_characteristic_coding_tenant_id'), 'healthcare_service_characteristic_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_characteristic_coding_updated_at'), 'healthcare_service_characteristic_coding', ['updated_at'], unique=False)
    op.create_table('healthcare_service_communication_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_communication_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['healthcare_service_communication_id'], ['healthcare_service_communication.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_healthcare_service_communication_coding_created_at'), 'healthcare_service_communication_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_communication_coding_healthcare_service_communication_id'), 'healthcare_service_communication_coding', ['healthcare_service_communication_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_communication_coding_tenant_id'), 'healthcare_service_communication_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_communication_coding_updated_at'), 'healthcare_service_communication_coding', ['updated_at'], unique=False)
    op.create_table('healthcare_service_eligibility_code_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_eligibility_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['healthcare_service_eligibility_id'], ['healthcare_service_eligibility.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_healthcare_service_eligibility_code_coding_created_at'), 'healthcare_service_eligibility_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_eligibility_code_coding_healthcare_service_eligibility_id'), 'healthcare_service_eligibility_code_coding', ['healthcare_service_eligibility_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_eligibility_code_coding_tenant_id'), 'healthcare_service_eligibility_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_eligibility_code_coding_updated_at'), 'healthcare_service_eligibility_code_coding', ['updated_at'], unique=False)
    op.create_table('healthcare_service_identifier_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_identifier_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['healthcare_service_identifier_id'], ['healthcare_service_identifier.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_healthcare_service_identifier_type_coding_created_at'), 'healthcare_service_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_identifier_type_coding_healthcare_service_identifier_id'), 'healthcare_service_identifier_type_coding', ['healthcare_service_identifier_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_identifier_type_coding_tenant_id'), 'healthcare_service_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_identifier_type_coding_updated_at'), 'healthcare_service_identifier_type_coding', ['updated_at'], unique=False)
    op.create_table('healthcare_service_program_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_program_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['healthcare_service_program_id'], ['healthcare_service_program.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_healthcare_service_program_coding_created_at'), 'healthcare_service_program_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_program_coding_healthcare_service_program_id'), 'healthcare_service_program_coding', ['healthcare_service_program_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_program_coding_tenant_id'), 'healthcare_service_program_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_program_coding_updated_at'), 'healthcare_service_program_coding', ['updated_at'], unique=False)
    op.create_table('healthcare_service_referral_method_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_referral_method_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['healthcare_service_referral_method_id'], ['healthcare_service_referral_method.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_healthcare_service_referral_method_coding_created_at'), 'healthcare_service_referral_method_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_referral_method_coding_healthcare_service_referral_method_id'), 'healthcare_service_referral_method_coding', ['healthcare_service_referral_method_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_referral_method_coding_tenant_id'), 'healthcare_service_referral_method_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_referral_method_coding_updated_at'), 'healthcare_service_referral_method_coding', ['updated_at'], unique=False)
    op.create_table('healthcare_service_service_provision_code_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_service_provision_code_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['healthcare_service_service_provision_code_id'], ['healthcare_service_service_provision_code.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_healthcare_service_service_provision_code_coding_created_at'), 'healthcare_service_service_provision_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_service_provision_code_coding_healthcare_service_service_provision_code_id'), 'healthcare_service_service_provision_code_coding', ['healthcare_service_service_provision_code_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_service_provision_code_coding_tenant_id'), 'healthcare_service_service_provision_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_service_provision_code_coding_updated_at'), 'healthcare_service_service_provision_code_coding', ['updated_at'], unique=False)
    op.create_table('healthcare_service_specialty_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_specialty_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['healthcare_service_specialty_id'], ['healthcare_service_specialty.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_healthcare_service_specialty_coding_created_at'), 'healthcare_service_specialty_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_specialty_coding_healthcare_service_specialty_id'), 'healthcare_service_specialty_coding', ['healthcare_service_specialty_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_specialty_coding_tenant_id'), 'healthcare_service_specialty_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_specialty_coding_updated_at'), 'healthcare_service_specialty_coding', ['updated_at'], unique=False)
    op.create_table('healthcare_service_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('healthcare_service_type_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['healthcare_service_type_id'], ['healthcare_service_type.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_healthcare_service_type_coding_created_at'), 'healthcare_service_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_healthcare_service_type_coding_healthcare_service_type_id'), 'healthcare_service_type_coding', ['healthcare_service_type_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_type_coding_tenant_id'), 'healthcare_service_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_healthcare_service_type_coding_updated_at'), 'healthcare_service_type_coding', ['updated_at'], unique=False)
    op.create_table('location_identifier_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('location_identifier_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['location_identifier_id'], ['location_identifier.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_location_identifier_type_coding_created_at'), 'location_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_location_identifier_type_coding_location_identifier_id'), 'location_identifier_type_coding', ['location_identifier_id'], unique=False)
    op.create_index(op.f('ix_location_identifier_type_coding_tenant_id'), 'location_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_location_identifier_type_coding_updated_at'), 'location_identifier_type_coding', ['updated_at'], unique=False)
    op.create_table('location_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('location_type_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['location_type_id'], ['location_type.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_location_type_coding_created_at'), 'location_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_location_type_coding_location_type_id'), 'location_type_coding', ['location_type_id'], unique=False)
    op.create_index(op.f('ix_location_type_coding_tenant_id'), 'location_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_location_type_coding_updated_at'), 'location_type_coding', ['updated_at'], unique=False)
    op.create_table('organization_contact_purpose_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('contact_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['contact_id'], ['organization_contact.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_contact_purpose_coding_contact_id'), 'organization_contact_purpose_coding', ['contact_id'], unique=False)
    op.create_index(op.f('ix_organization_contact_purpose_coding_created_at'), 'organization_contact_purpose_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_organization_contact_purpose_coding_tenant_id'), 'organization_contact_purpose_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_organization_contact_purpose_coding_updated_at'), 'organization_contact_purpose_coding', ['updated_at'], unique=False)
    op.create_table('organization_contact_telecom',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('contact_id', sa.BigInteger(), nullable=False),
    sa.Column('system', _contact_point_system, nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('use', _contact_point_use, nullable=True),
    sa.Column('rank', sa.Integer(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['contact_id'], ['organization_contact.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_contact_telecom_contact_id'), 'organization_contact_telecom', ['contact_id'], unique=False)
    op.create_index(op.f('ix_organization_contact_telecom_created_at'), 'organization_contact_telecom', ['created_at'], unique=False)
    op.create_index(op.f('ix_organization_contact_telecom_tenant_id'), 'organization_contact_telecom', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_organization_contact_telecom_updated_at'), 'organization_contact_telecom', ['updated_at'], unique=False)
    op.create_table('organization_identifier_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('organization_identifier_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['organization_identifier_id'], ['organization_identifier.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_identifier_type_coding_created_at'), 'organization_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_organization_identifier_type_coding_organization_identifier_id'), 'organization_identifier_type_coding', ['organization_identifier_id'], unique=False)
    op.create_index(op.f('ix_organization_identifier_type_coding_tenant_id'), 'organization_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_organization_identifier_type_coding_updated_at'), 'organization_identifier_type_coding', ['updated_at'], unique=False)
    op.create_table('organization_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('organization_type_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['organization_type_id'], ['organization_type.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_type_coding_created_at'), 'organization_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_organization_type_coding_organization_type_id'), 'organization_type_coding', ['organization_type_id'], unique=False)
    op.create_index(op.f('ix_organization_type_coding_tenant_id'), 'organization_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_organization_type_coding_updated_at'), 'organization_type_coding', ['updated_at'], unique=False)
    op.create_table('practitioner_communication_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('practitioner_communication_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['practitioner_communication_id'], ['practitioner_communication.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practitioner_communication_coding_created_at'), 'practitioner_communication_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_communication_coding_practitioner_communication_id'), 'practitioner_communication_coding', ['practitioner_communication_id'], unique=False)
    op.create_index(op.f('ix_practitioner_communication_coding_tenant_id'), 'practitioner_communication_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_communication_coding_updated_at'), 'practitioner_communication_coding', ['updated_at'], unique=False)
    op.create_table('practitioner_identifier_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('practitioner_identifier_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['practitioner_identifier_id'], ['practitioner_identifier.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practitioner_identifier_type_coding_created_at'), 'practitioner_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_identifier_type_coding_practitioner_identifier_id'), 'practitioner_identifier_type_coding', ['practitioner_identifier_id'], unique=False)
    op.create_index(op.f('ix_practitioner_identifier_type_coding_tenant_id'), 'practitioner_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_identifier_type_coding_updated_at'), 'practitioner_identifier_type_coding', ['updated_at'], unique=False)
    op.create_table('practitioner_qualification_code_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('practitioner_qualification_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['practitioner_qualification_id'], ['practitioner_qualification.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practitioner_qualification_code_coding_created_at'), 'practitioner_qualification_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_qualification_code_coding_practitioner_qualification_id'), 'practitioner_qualification_code_coding', ['practitioner_qualification_id'], unique=False)
    op.create_index(op.f('ix_practitioner_qualification_code_coding_tenant_id'), 'practitioner_qualification_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_qualification_code_coding_updated_at'), 'practitioner_qualification_code_coding', ['updated_at'], unique=False)
    op.create_table('practitioner_qualification_identifier',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('practitioner_qualification_id', sa.BigInteger(), nullable=False),
    sa.Column('use', _identifier_use, nullable=True),
    sa.Column('type_text', sa.String(), nullable=True),
    sa.Column('system', sa.String(), nullable=True),
    sa.Column('value', sa.String(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('assigner_reference', sa.String(), nullable=True),
    sa.Column('assigner_id', sa.BigInteger(), nullable=True),
    sa.Column('assigner_type', _organization_reference_type, nullable=True),
    sa.Column('assigner_display', sa.String(), nullable=True),
    sa.Column('assigner_identifier_use', _identifier_use, nullable=True),
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
    sa.ForeignKeyConstraint(['practitioner_qualification_id'], ['practitioner_qualification.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practitioner_qualification_identifier_assigner_id'), 'practitioner_qualification_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_practitioner_qualification_identifier_created_at'), 'practitioner_qualification_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_qualification_identifier_practitioner_qualification_id'), 'practitioner_qualification_identifier', ['practitioner_qualification_id'], unique=False)
    op.create_index(op.f('ix_practitioner_qualification_identifier_tenant_id'), 'practitioner_qualification_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_qualification_identifier_updated_at'), 'practitioner_qualification_identifier', ['updated_at'], unique=False)
    op.create_table('practitioner_role_code_coding',
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
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practitioner_role_code_coding_created_at'), 'practitioner_role_code_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_code_coding_practitioner_role_code_id'), 'practitioner_role_code_coding', ['practitioner_role_code_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_code_coding_tenant_id'), 'practitioner_role_code_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_code_coding_updated_at'), 'practitioner_role_code_coding', ['updated_at'], unique=False)
    op.create_table('practitioner_role_identifier_type_coding',
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
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practitioner_role_identifier_type_coding_created_at'), 'practitioner_role_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_identifier_type_coding_practitioner_role_identifier_id'), 'practitioner_role_identifier_type_coding', ['practitioner_role_identifier_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_identifier_type_coding_tenant_id'), 'practitioner_role_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_identifier_type_coding_updated_at'), 'practitioner_role_identifier_type_coding', ['updated_at'], unique=False)
    op.create_table('practitioner_role_specialty_coding',
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
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practitioner_role_specialty_coding_created_at'), 'practitioner_role_specialty_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_role_specialty_coding_practitioner_role_specialty_id'), 'practitioner_role_specialty_coding', ['practitioner_role_specialty_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_specialty_coding_tenant_id'), 'practitioner_role_specialty_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_role_specialty_coding_updated_at'), 'practitioner_role_specialty_coding', ['updated_at'], unique=False)
    op.create_table('schedule_identifier_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('schedule_identifier_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['schedule_identifier_id'], ['schedule_identifier.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedule_identifier_type_coding_created_at'), 'schedule_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_schedule_identifier_type_coding_schedule_identifier_id'), 'schedule_identifier_type_coding', ['schedule_identifier_id'], unique=False)
    op.create_index(op.f('ix_schedule_identifier_type_coding_tenant_id'), 'schedule_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_schedule_identifier_type_coding_updated_at'), 'schedule_identifier_type_coding', ['updated_at'], unique=False)
    op.create_table('schedule_service_category_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('schedule_service_category_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['schedule_service_category_id'], ['schedule_service_category.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedule_service_category_coding_created_at'), 'schedule_service_category_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_schedule_service_category_coding_schedule_service_category_id'), 'schedule_service_category_coding', ['schedule_service_category_id'], unique=False)
    op.create_index(op.f('ix_schedule_service_category_coding_tenant_id'), 'schedule_service_category_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_schedule_service_category_coding_updated_at'), 'schedule_service_category_coding', ['updated_at'], unique=False)
    op.create_table('schedule_service_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('schedule_service_type_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['schedule_service_type_id'], ['schedule_service_type.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedule_service_type_coding_created_at'), 'schedule_service_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_schedule_service_type_coding_schedule_service_type_id'), 'schedule_service_type_coding', ['schedule_service_type_id'], unique=False)
    op.create_index(op.f('ix_schedule_service_type_coding_tenant_id'), 'schedule_service_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_schedule_service_type_coding_updated_at'), 'schedule_service_type_coding', ['updated_at'], unique=False)
    op.create_table('schedule_specialty_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('schedule_specialty_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['schedule_specialty_id'], ['schedule_specialty.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_schedule_specialty_coding_created_at'), 'schedule_specialty_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_schedule_specialty_coding_schedule_specialty_id'), 'schedule_specialty_coding', ['schedule_specialty_id'], unique=False)
    op.create_index(op.f('ix_schedule_specialty_coding_tenant_id'), 'schedule_specialty_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_schedule_specialty_coding_updated_at'), 'schedule_specialty_coding', ['updated_at'], unique=False)
    op.create_table('slot_identifier_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('slot_identifier_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['slot_identifier_id'], ['slot_identifier.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_slot_identifier_type_coding_created_at'), 'slot_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_slot_identifier_type_coding_slot_identifier_id'), 'slot_identifier_type_coding', ['slot_identifier_id'], unique=False)
    op.create_index(op.f('ix_slot_identifier_type_coding_tenant_id'), 'slot_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_slot_identifier_type_coding_updated_at'), 'slot_identifier_type_coding', ['updated_at'], unique=False)
    op.create_table('slot_service_category_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('slot_service_category_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['slot_service_category_id'], ['slot_service_category.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_slot_service_category_coding_created_at'), 'slot_service_category_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_slot_service_category_coding_slot_service_category_id'), 'slot_service_category_coding', ['slot_service_category_id'], unique=False)
    op.create_index(op.f('ix_slot_service_category_coding_tenant_id'), 'slot_service_category_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_slot_service_category_coding_updated_at'), 'slot_service_category_coding', ['updated_at'], unique=False)
    op.create_table('slot_service_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('slot_service_type_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['slot_service_type_id'], ['slot_service_type.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_slot_service_type_coding_created_at'), 'slot_service_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_slot_service_type_coding_slot_service_type_id'), 'slot_service_type_coding', ['slot_service_type_id'], unique=False)
    op.create_index(op.f('ix_slot_service_type_coding_tenant_id'), 'slot_service_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_slot_service_type_coding_updated_at'), 'slot_service_type_coding', ['updated_at'], unique=False)
    op.create_table('slot_specialty_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('slot_specialty_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['slot_specialty_id'], ['slot_specialty.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_slot_specialty_coding_created_at'), 'slot_specialty_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_slot_specialty_coding_slot_specialty_id'), 'slot_specialty_coding', ['slot_specialty_id'], unique=False)
    op.create_index(op.f('ix_slot_specialty_coding_tenant_id'), 'slot_specialty_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_slot_specialty_coding_updated_at'), 'slot_specialty_coding', ['updated_at'], unique=False)
    op.create_table('terminology_concept_embedding',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('concept_id', sa.Integer(), nullable=False),
    sa.Column('embedding', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('model', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['concept_id'], ['terminology_concept.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_terminology_concept_embedding_concept_id'), 'terminology_concept_embedding', ['concept_id'], unique=True)
    op.create_table('terminology_concept_map',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('source_concept_id', sa.Integer(), nullable=False),
    sa.Column('target_concept_id', sa.Integer(), nullable=False),
    sa.Column('mapping_type', sa.String(), nullable=True),
    sa.Column('confidence', sa.Float(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['source_concept_id'], ['terminology_concept.id'], ),
    sa.ForeignKeyConstraint(['target_concept_id'], ['terminology_concept.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('source_concept_id', 'target_concept_id', 'mapping_type')
    )
    op.create_index(op.f('ix_terminology_concept_map_source_concept_id'), 'terminology_concept_map', ['source_concept_id'], unique=False)
    op.create_index(op.f('ix_terminology_concept_map_target_concept_id'), 'terminology_concept_map', ['target_concept_id'], unique=False)
    op.create_table('terminology_concept_synonym',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('concept_id', sa.Integer(), nullable=False),
    sa.Column('synonym', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['concept_id'], ['terminology_concept.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_terminology_concept_synonym_concept_id'), 'terminology_concept_synonym', ['concept_id'], unique=False)
    op.create_table('terminology_concept_translation',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('concept_id', sa.Integer(), nullable=False),
    sa.Column('language_code', sa.String(), nullable=False),
    sa.Column('display', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['concept_id'], ['terminology_concept.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('concept_id', 'language_code')
    )
    op.create_index(op.f('ix_terminology_concept_translation_concept_id'), 'terminology_concept_translation', ['concept_id'], unique=False)
    op.create_table('terminology_display_override',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('concept_id', sa.Integer(), nullable=False),
    sa.Column('org_id', sa.String(), nullable=False),
    sa.Column('display', sa.String(), nullable=False),
    sa.Column('definition', sa.Text(), nullable=True),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['concept_id'], ['terminology_concept.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('concept_id', 'org_id')
    )
    op.create_index(op.f('ix_terminology_display_override_concept_id'), 'terminology_display_override', ['concept_id'], unique=False)
    op.create_index(op.f('ix_terminology_display_override_org_id'), 'terminology_display_override', ['org_id'], unique=False)
    op.create_table('terminology_relationship',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('parent_concept_id', sa.Integer(), nullable=False),
    sa.Column('child_concept_id', sa.Integer(), nullable=False),
    sa.Column('relationship_type', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['child_concept_id'], ['terminology_concept.id'], ),
    sa.ForeignKeyConstraint(['parent_concept_id'], ['terminology_concept.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('parent_concept_id', 'child_concept_id', 'relationship_type')
    )
    op.create_index(op.f('ix_terminology_relationship_child_concept_id'), 'terminology_relationship', ['child_concept_id'], unique=False)
    op.create_index(op.f('ix_terminology_relationship_parent_concept_id'), 'terminology_relationship', ['parent_concept_id'], unique=False)
    op.create_table('terminology_value_set_concept',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('value_set_id', sa.Integer(), nullable=False),
    sa.Column('concept_id', sa.Integer(), nullable=False),
    sa.Column('active', sa.Boolean(), server_default=sa.text('true'), nullable=True),
    sa.ForeignKeyConstraint(['concept_id'], ['terminology_concept.id'], ),
    sa.ForeignKeyConstraint(['value_set_id'], ['terminology_value_set.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('value_set_id', 'concept_id')
    )
    op.create_index(op.f('ix_terminology_value_set_concept_concept_id'), 'terminology_value_set_concept', ['concept_id'], unique=False)
    op.create_index(op.f('ix_terminology_value_set_concept_value_set_id'), 'terminology_value_set_concept', ['value_set_id'], unique=False)
    op.create_table('practitioner_qualification_identifier_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('practitioner_qualification_identifier_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['practitioner_qualification_identifier_id'], ['practitioner_qualification_identifier.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_practitioner_qualification_identifier_type_coding_created_at'), 'practitioner_qualification_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_practitioner_qualification_identifier_type_coding_practitioner_qualification_identifier_id'), 'practitioner_qualification_identifier_type_coding', ['practitioner_qualification_identifier_id'], unique=False)
    op.create_index(op.f('ix_practitioner_qualification_identifier_type_coding_tenant_id'), 'practitioner_qualification_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_practitioner_qualification_identifier_type_coding_updated_at'), 'practitioner_qualification_identifier_type_coding', ['updated_at'], unique=False)
    op.create_table('terminology_audit_log',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('action', sa.String(), nullable=False),
    sa.Column('concept_id', sa.Integer(), nullable=True),
    sa.Column('value_set_id', sa.Integer(), nullable=True),
    sa.Column('display_override_id', sa.Integer(), nullable=True),
    sa.Column('performed_by', sa.String(), nullable=True),
    sa.Column('old_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('new_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['concept_id'], ['terminology_concept.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['display_override_id'], ['terminology_display_override.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['value_set_id'], ['terminology_value_set.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_terminology_audit_log_action'), 'terminology_audit_log', ['action'], unique=False)
    op.create_index(op.f('ix_terminology_audit_log_concept_id'), 'terminology_audit_log', ['concept_id'], unique=False)
    op.create_index(op.f('ix_terminology_audit_log_display_override_id'), 'terminology_audit_log', ['display_override_id'], unique=False)
    op.create_index(op.f('ix_terminology_audit_log_value_set_id'), 'terminology_audit_log', ['value_set_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_terminology_audit_log_value_set_id'), table_name='terminology_audit_log')
    op.drop_index(op.f('ix_terminology_audit_log_display_override_id'), table_name='terminology_audit_log')
    op.drop_index(op.f('ix_terminology_audit_log_concept_id'), table_name='terminology_audit_log')
    op.drop_index(op.f('ix_terminology_audit_log_action'), table_name='terminology_audit_log')
    op.drop_table('terminology_audit_log')
    op.drop_index(op.f('ix_practitioner_qualification_identifier_type_coding_updated_at'), table_name='practitioner_qualification_identifier_type_coding')
    op.drop_index(op.f('ix_practitioner_qualification_identifier_type_coding_tenant_id'), table_name='practitioner_qualification_identifier_type_coding')
    op.drop_index(op.f('ix_practitioner_qualification_identifier_type_coding_practitioner_qualification_identifier_id'), table_name='practitioner_qualification_identifier_type_coding')
    op.drop_index(op.f('ix_practitioner_qualification_identifier_type_coding_created_at'), table_name='practitioner_qualification_identifier_type_coding')
    op.drop_table('practitioner_qualification_identifier_type_coding')
    op.drop_index(op.f('ix_terminology_value_set_concept_value_set_id'), table_name='terminology_value_set_concept')
    op.drop_index(op.f('ix_terminology_value_set_concept_concept_id'), table_name='terminology_value_set_concept')
    op.drop_table('terminology_value_set_concept')
    op.drop_index(op.f('ix_terminology_relationship_parent_concept_id'), table_name='terminology_relationship')
    op.drop_index(op.f('ix_terminology_relationship_child_concept_id'), table_name='terminology_relationship')
    op.drop_table('terminology_relationship')
    op.drop_index(op.f('ix_terminology_display_override_org_id'), table_name='terminology_display_override')
    op.drop_index(op.f('ix_terminology_display_override_concept_id'), table_name='terminology_display_override')
    op.drop_table('terminology_display_override')
    op.drop_index(op.f('ix_terminology_concept_translation_concept_id'), table_name='terminology_concept_translation')
    op.drop_table('terminology_concept_translation')
    op.drop_index(op.f('ix_terminology_concept_synonym_concept_id'), table_name='terminology_concept_synonym')
    op.drop_table('terminology_concept_synonym')
    op.drop_index(op.f('ix_terminology_concept_map_target_concept_id'), table_name='terminology_concept_map')
    op.drop_index(op.f('ix_terminology_concept_map_source_concept_id'), table_name='terminology_concept_map')
    op.drop_table('terminology_concept_map')
    op.drop_index(op.f('ix_terminology_concept_embedding_concept_id'), table_name='terminology_concept_embedding')
    op.drop_table('terminology_concept_embedding')
    op.drop_index(op.f('ix_slot_specialty_coding_updated_at'), table_name='slot_specialty_coding')
    op.drop_index(op.f('ix_slot_specialty_coding_tenant_id'), table_name='slot_specialty_coding')
    op.drop_index(op.f('ix_slot_specialty_coding_slot_specialty_id'), table_name='slot_specialty_coding')
    op.drop_index(op.f('ix_slot_specialty_coding_created_at'), table_name='slot_specialty_coding')
    op.drop_table('slot_specialty_coding')
    op.drop_index(op.f('ix_slot_service_type_coding_updated_at'), table_name='slot_service_type_coding')
    op.drop_index(op.f('ix_slot_service_type_coding_tenant_id'), table_name='slot_service_type_coding')
    op.drop_index(op.f('ix_slot_service_type_coding_slot_service_type_id'), table_name='slot_service_type_coding')
    op.drop_index(op.f('ix_slot_service_type_coding_created_at'), table_name='slot_service_type_coding')
    op.drop_table('slot_service_type_coding')
    op.drop_index(op.f('ix_slot_service_category_coding_updated_at'), table_name='slot_service_category_coding')
    op.drop_index(op.f('ix_slot_service_category_coding_tenant_id'), table_name='slot_service_category_coding')
    op.drop_index(op.f('ix_slot_service_category_coding_slot_service_category_id'), table_name='slot_service_category_coding')
    op.drop_index(op.f('ix_slot_service_category_coding_created_at'), table_name='slot_service_category_coding')
    op.drop_table('slot_service_category_coding')
    op.drop_index(op.f('ix_slot_identifier_type_coding_updated_at'), table_name='slot_identifier_type_coding')
    op.drop_index(op.f('ix_slot_identifier_type_coding_tenant_id'), table_name='slot_identifier_type_coding')
    op.drop_index(op.f('ix_slot_identifier_type_coding_slot_identifier_id'), table_name='slot_identifier_type_coding')
    op.drop_index(op.f('ix_slot_identifier_type_coding_created_at'), table_name='slot_identifier_type_coding')
    op.drop_table('slot_identifier_type_coding')
    op.drop_index(op.f('ix_schedule_specialty_coding_updated_at'), table_name='schedule_specialty_coding')
    op.drop_index(op.f('ix_schedule_specialty_coding_tenant_id'), table_name='schedule_specialty_coding')
    op.drop_index(op.f('ix_schedule_specialty_coding_schedule_specialty_id'), table_name='schedule_specialty_coding')
    op.drop_index(op.f('ix_schedule_specialty_coding_created_at'), table_name='schedule_specialty_coding')
    op.drop_table('schedule_specialty_coding')
    op.drop_index(op.f('ix_schedule_service_type_coding_updated_at'), table_name='schedule_service_type_coding')
    op.drop_index(op.f('ix_schedule_service_type_coding_tenant_id'), table_name='schedule_service_type_coding')
    op.drop_index(op.f('ix_schedule_service_type_coding_schedule_service_type_id'), table_name='schedule_service_type_coding')
    op.drop_index(op.f('ix_schedule_service_type_coding_created_at'), table_name='schedule_service_type_coding')
    op.drop_table('schedule_service_type_coding')
    op.drop_index(op.f('ix_schedule_service_category_coding_updated_at'), table_name='schedule_service_category_coding')
    op.drop_index(op.f('ix_schedule_service_category_coding_tenant_id'), table_name='schedule_service_category_coding')
    op.drop_index(op.f('ix_schedule_service_category_coding_schedule_service_category_id'), table_name='schedule_service_category_coding')
    op.drop_index(op.f('ix_schedule_service_category_coding_created_at'), table_name='schedule_service_category_coding')
    op.drop_table('schedule_service_category_coding')
    op.drop_index(op.f('ix_schedule_identifier_type_coding_updated_at'), table_name='schedule_identifier_type_coding')
    op.drop_index(op.f('ix_schedule_identifier_type_coding_tenant_id'), table_name='schedule_identifier_type_coding')
    op.drop_index(op.f('ix_schedule_identifier_type_coding_schedule_identifier_id'), table_name='schedule_identifier_type_coding')
    op.drop_index(op.f('ix_schedule_identifier_type_coding_created_at'), table_name='schedule_identifier_type_coding')
    op.drop_table('schedule_identifier_type_coding')
    op.drop_index(op.f('ix_practitioner_role_specialty_coding_updated_at'), table_name='practitioner_role_specialty_coding')
    op.drop_index(op.f('ix_practitioner_role_specialty_coding_tenant_id'), table_name='practitioner_role_specialty_coding')
    op.drop_index(op.f('ix_practitioner_role_specialty_coding_practitioner_role_specialty_id'), table_name='practitioner_role_specialty_coding')
    op.drop_index(op.f('ix_practitioner_role_specialty_coding_created_at'), table_name='practitioner_role_specialty_coding')
    op.drop_table('practitioner_role_specialty_coding')
    op.drop_index(op.f('ix_practitioner_role_identifier_type_coding_updated_at'), table_name='practitioner_role_identifier_type_coding')
    op.drop_index(op.f('ix_practitioner_role_identifier_type_coding_tenant_id'), table_name='practitioner_role_identifier_type_coding')
    op.drop_index(op.f('ix_practitioner_role_identifier_type_coding_practitioner_role_identifier_id'), table_name='practitioner_role_identifier_type_coding')
    op.drop_index(op.f('ix_practitioner_role_identifier_type_coding_created_at'), table_name='practitioner_role_identifier_type_coding')
    op.drop_table('practitioner_role_identifier_type_coding')
    op.drop_index(op.f('ix_practitioner_role_code_coding_updated_at'), table_name='practitioner_role_code_coding')
    op.drop_index(op.f('ix_practitioner_role_code_coding_tenant_id'), table_name='practitioner_role_code_coding')
    op.drop_index(op.f('ix_practitioner_role_code_coding_practitioner_role_code_id'), table_name='practitioner_role_code_coding')
    op.drop_index(op.f('ix_practitioner_role_code_coding_created_at'), table_name='practitioner_role_code_coding')
    op.drop_table('practitioner_role_code_coding')
    op.drop_index(op.f('ix_practitioner_qualification_identifier_updated_at'), table_name='practitioner_qualification_identifier')
    op.drop_index(op.f('ix_practitioner_qualification_identifier_tenant_id'), table_name='practitioner_qualification_identifier')
    op.drop_index(op.f('ix_practitioner_qualification_identifier_practitioner_qualification_id'), table_name='practitioner_qualification_identifier')
    op.drop_index(op.f('ix_practitioner_qualification_identifier_created_at'), table_name='practitioner_qualification_identifier')
    op.drop_index(op.f('ix_practitioner_qualification_identifier_assigner_id'), table_name='practitioner_qualification_identifier')
    op.drop_table('practitioner_qualification_identifier')
    op.drop_index(op.f('ix_practitioner_qualification_code_coding_updated_at'), table_name='practitioner_qualification_code_coding')
    op.drop_index(op.f('ix_practitioner_qualification_code_coding_tenant_id'), table_name='practitioner_qualification_code_coding')
    op.drop_index(op.f('ix_practitioner_qualification_code_coding_practitioner_qualification_id'), table_name='practitioner_qualification_code_coding')
    op.drop_index(op.f('ix_practitioner_qualification_code_coding_created_at'), table_name='practitioner_qualification_code_coding')
    op.drop_table('practitioner_qualification_code_coding')
    op.drop_index(op.f('ix_practitioner_identifier_type_coding_updated_at'), table_name='practitioner_identifier_type_coding')
    op.drop_index(op.f('ix_practitioner_identifier_type_coding_tenant_id'), table_name='practitioner_identifier_type_coding')
    op.drop_index(op.f('ix_practitioner_identifier_type_coding_practitioner_identifier_id'), table_name='practitioner_identifier_type_coding')
    op.drop_index(op.f('ix_practitioner_identifier_type_coding_created_at'), table_name='practitioner_identifier_type_coding')
    op.drop_table('practitioner_identifier_type_coding')
    op.drop_index(op.f('ix_practitioner_communication_coding_updated_at'), table_name='practitioner_communication_coding')
    op.drop_index(op.f('ix_practitioner_communication_coding_tenant_id'), table_name='practitioner_communication_coding')
    op.drop_index(op.f('ix_practitioner_communication_coding_practitioner_communication_id'), table_name='practitioner_communication_coding')
    op.drop_index(op.f('ix_practitioner_communication_coding_created_at'), table_name='practitioner_communication_coding')
    op.drop_table('practitioner_communication_coding')
    op.drop_index(op.f('ix_organization_type_coding_updated_at'), table_name='organization_type_coding')
    op.drop_index(op.f('ix_organization_type_coding_tenant_id'), table_name='organization_type_coding')
    op.drop_index(op.f('ix_organization_type_coding_organization_type_id'), table_name='organization_type_coding')
    op.drop_index(op.f('ix_organization_type_coding_created_at'), table_name='organization_type_coding')
    op.drop_table('organization_type_coding')
    op.drop_index(op.f('ix_organization_identifier_type_coding_updated_at'), table_name='organization_identifier_type_coding')
    op.drop_index(op.f('ix_organization_identifier_type_coding_tenant_id'), table_name='organization_identifier_type_coding')
    op.drop_index(op.f('ix_organization_identifier_type_coding_organization_identifier_id'), table_name='organization_identifier_type_coding')
    op.drop_index(op.f('ix_organization_identifier_type_coding_created_at'), table_name='organization_identifier_type_coding')
    op.drop_table('organization_identifier_type_coding')
    op.drop_index(op.f('ix_organization_contact_telecom_updated_at'), table_name='organization_contact_telecom')
    op.drop_index(op.f('ix_organization_contact_telecom_tenant_id'), table_name='organization_contact_telecom')
    op.drop_index(op.f('ix_organization_contact_telecom_created_at'), table_name='organization_contact_telecom')
    op.drop_index(op.f('ix_organization_contact_telecom_contact_id'), table_name='organization_contact_telecom')
    op.drop_table('organization_contact_telecom')
    op.drop_index(op.f('ix_organization_contact_purpose_coding_updated_at'), table_name='organization_contact_purpose_coding')
    op.drop_index(op.f('ix_organization_contact_purpose_coding_tenant_id'), table_name='organization_contact_purpose_coding')
    op.drop_index(op.f('ix_organization_contact_purpose_coding_created_at'), table_name='organization_contact_purpose_coding')
    op.drop_index(op.f('ix_organization_contact_purpose_coding_contact_id'), table_name='organization_contact_purpose_coding')
    op.drop_table('organization_contact_purpose_coding')
    op.drop_index(op.f('ix_location_type_coding_updated_at'), table_name='location_type_coding')
    op.drop_index(op.f('ix_location_type_coding_tenant_id'), table_name='location_type_coding')
    op.drop_index(op.f('ix_location_type_coding_location_type_id'), table_name='location_type_coding')
    op.drop_index(op.f('ix_location_type_coding_created_at'), table_name='location_type_coding')
    op.drop_table('location_type_coding')
    op.drop_index(op.f('ix_location_identifier_type_coding_updated_at'), table_name='location_identifier_type_coding')
    op.drop_index(op.f('ix_location_identifier_type_coding_tenant_id'), table_name='location_identifier_type_coding')
    op.drop_index(op.f('ix_location_identifier_type_coding_location_identifier_id'), table_name='location_identifier_type_coding')
    op.drop_index(op.f('ix_location_identifier_type_coding_created_at'), table_name='location_identifier_type_coding')
    op.drop_table('location_identifier_type_coding')
    op.drop_index(op.f('ix_healthcare_service_type_coding_updated_at'), table_name='healthcare_service_type_coding')
    op.drop_index(op.f('ix_healthcare_service_type_coding_tenant_id'), table_name='healthcare_service_type_coding')
    op.drop_index(op.f('ix_healthcare_service_type_coding_healthcare_service_type_id'), table_name='healthcare_service_type_coding')
    op.drop_index(op.f('ix_healthcare_service_type_coding_created_at'), table_name='healthcare_service_type_coding')
    op.drop_table('healthcare_service_type_coding')
    op.drop_index(op.f('ix_healthcare_service_specialty_coding_updated_at'), table_name='healthcare_service_specialty_coding')
    op.drop_index(op.f('ix_healthcare_service_specialty_coding_tenant_id'), table_name='healthcare_service_specialty_coding')
    op.drop_index(op.f('ix_healthcare_service_specialty_coding_healthcare_service_specialty_id'), table_name='healthcare_service_specialty_coding')
    op.drop_index(op.f('ix_healthcare_service_specialty_coding_created_at'), table_name='healthcare_service_specialty_coding')
    op.drop_table('healthcare_service_specialty_coding')
    op.drop_index(op.f('ix_healthcare_service_service_provision_code_coding_updated_at'), table_name='healthcare_service_service_provision_code_coding')
    op.drop_index(op.f('ix_healthcare_service_service_provision_code_coding_tenant_id'), table_name='healthcare_service_service_provision_code_coding')
    op.drop_index(op.f('ix_healthcare_service_service_provision_code_coding_healthcare_service_service_provision_code_id'), table_name='healthcare_service_service_provision_code_coding')
    op.drop_index(op.f('ix_healthcare_service_service_provision_code_coding_created_at'), table_name='healthcare_service_service_provision_code_coding')
    op.drop_table('healthcare_service_service_provision_code_coding')
    op.drop_index(op.f('ix_healthcare_service_referral_method_coding_updated_at'), table_name='healthcare_service_referral_method_coding')
    op.drop_index(op.f('ix_healthcare_service_referral_method_coding_tenant_id'), table_name='healthcare_service_referral_method_coding')
    op.drop_index(op.f('ix_healthcare_service_referral_method_coding_healthcare_service_referral_method_id'), table_name='healthcare_service_referral_method_coding')
    op.drop_index(op.f('ix_healthcare_service_referral_method_coding_created_at'), table_name='healthcare_service_referral_method_coding')
    op.drop_table('healthcare_service_referral_method_coding')
    op.drop_index(op.f('ix_healthcare_service_program_coding_updated_at'), table_name='healthcare_service_program_coding')
    op.drop_index(op.f('ix_healthcare_service_program_coding_tenant_id'), table_name='healthcare_service_program_coding')
    op.drop_index(op.f('ix_healthcare_service_program_coding_healthcare_service_program_id'), table_name='healthcare_service_program_coding')
    op.drop_index(op.f('ix_healthcare_service_program_coding_created_at'), table_name='healthcare_service_program_coding')
    op.drop_table('healthcare_service_program_coding')
    op.drop_index(op.f('ix_healthcare_service_identifier_type_coding_updated_at'), table_name='healthcare_service_identifier_type_coding')
    op.drop_index(op.f('ix_healthcare_service_identifier_type_coding_tenant_id'), table_name='healthcare_service_identifier_type_coding')
    op.drop_index(op.f('ix_healthcare_service_identifier_type_coding_healthcare_service_identifier_id'), table_name='healthcare_service_identifier_type_coding')
    op.drop_index(op.f('ix_healthcare_service_identifier_type_coding_created_at'), table_name='healthcare_service_identifier_type_coding')
    op.drop_table('healthcare_service_identifier_type_coding')
    op.drop_index(op.f('ix_healthcare_service_eligibility_code_coding_updated_at'), table_name='healthcare_service_eligibility_code_coding')
    op.drop_index(op.f('ix_healthcare_service_eligibility_code_coding_tenant_id'), table_name='healthcare_service_eligibility_code_coding')
    op.drop_index(op.f('ix_healthcare_service_eligibility_code_coding_healthcare_service_eligibility_id'), table_name='healthcare_service_eligibility_code_coding')
    op.drop_index(op.f('ix_healthcare_service_eligibility_code_coding_created_at'), table_name='healthcare_service_eligibility_code_coding')
    op.drop_table('healthcare_service_eligibility_code_coding')
    op.drop_index(op.f('ix_healthcare_service_communication_coding_updated_at'), table_name='healthcare_service_communication_coding')
    op.drop_index(op.f('ix_healthcare_service_communication_coding_tenant_id'), table_name='healthcare_service_communication_coding')
    op.drop_index(op.f('ix_healthcare_service_communication_coding_healthcare_service_communication_id'), table_name='healthcare_service_communication_coding')
    op.drop_index(op.f('ix_healthcare_service_communication_coding_created_at'), table_name='healthcare_service_communication_coding')
    op.drop_table('healthcare_service_communication_coding')
    op.drop_index(op.f('ix_healthcare_service_characteristic_coding_updated_at'), table_name='healthcare_service_characteristic_coding')
    op.drop_index(op.f('ix_healthcare_service_characteristic_coding_tenant_id'), table_name='healthcare_service_characteristic_coding')
    op.drop_index(op.f('ix_healthcare_service_characteristic_coding_healthcare_service_characteristic_id'), table_name='healthcare_service_characteristic_coding')
    op.drop_index(op.f('ix_healthcare_service_characteristic_coding_created_at'), table_name='healthcare_service_characteristic_coding')
    op.drop_table('healthcare_service_characteristic_coding')
    op.drop_index(op.f('ix_healthcare_service_category_coding_updated_at'), table_name='healthcare_service_category_coding')
    op.drop_index(op.f('ix_healthcare_service_category_coding_tenant_id'), table_name='healthcare_service_category_coding')
    op.drop_index(op.f('ix_healthcare_service_category_coding_healthcare_service_category_id'), table_name='healthcare_service_category_coding')
    op.drop_index(op.f('ix_healthcare_service_category_coding_created_at'), table_name='healthcare_service_category_coding')
    op.drop_table('healthcare_service_category_coding')
    op.drop_index(op.f('ix_terminology_field_binding_value_set_id'), table_name='terminology_field_binding')
    op.drop_index(op.f('ix_terminology_field_binding_resource_type'), table_name='terminology_field_binding')
    op.drop_table('terminology_field_binding')
    op.drop_index('uq_terminology_concept_system_code_org', table_name='terminology_concept', postgresql_where=sa.text('org_id IS NOT NULL'))
    op.drop_index('uq_terminology_concept_system_code_null_org', table_name='terminology_concept', postgresql_where=sa.text('org_id IS NULL'))
    op.drop_index(op.f('ix_terminology_concept_user_id'), table_name='terminology_concept')
    op.drop_index(op.f('ix_terminology_concept_parent_concept_id'), table_name='terminology_concept')
    op.drop_index(op.f('ix_terminology_concept_org_id'), table_name='terminology_concept')
    op.drop_index(op.f('ix_terminology_concept_code_system_id'), table_name='terminology_concept')
    op.drop_index(op.f('ix_terminology_concept_code'), table_name='terminology_concept')
    op.drop_table('terminology_concept')
    op.drop_index(op.f('ix_slot_specialty_updated_at'), table_name='slot_specialty')
    op.drop_index(op.f('ix_slot_specialty_tenant_id'), table_name='slot_specialty')
    op.drop_index(op.f('ix_slot_specialty_slot_pk'), table_name='slot_specialty')
    op.drop_index(op.f('ix_slot_specialty_created_at'), table_name='slot_specialty')
    op.drop_table('slot_specialty')
    op.drop_index(op.f('ix_slot_service_type_updated_at'), table_name='slot_service_type')
    op.drop_index(op.f('ix_slot_service_type_tenant_id'), table_name='slot_service_type')
    op.drop_index(op.f('ix_slot_service_type_slot_pk'), table_name='slot_service_type')
    op.drop_index(op.f('ix_slot_service_type_created_at'), table_name='slot_service_type')
    op.drop_table('slot_service_type')
    op.drop_index(op.f('ix_slot_service_category_updated_at'), table_name='slot_service_category')
    op.drop_index(op.f('ix_slot_service_category_tenant_id'), table_name='slot_service_category')
    op.drop_index(op.f('ix_slot_service_category_slot_pk'), table_name='slot_service_category')
    op.drop_index(op.f('ix_slot_service_category_created_at'), table_name='slot_service_category')
    op.drop_table('slot_service_category')
    op.drop_index(op.f('ix_slot_identifier_updated_at'), table_name='slot_identifier')
    op.drop_index(op.f('ix_slot_identifier_tenant_id'), table_name='slot_identifier')
    op.drop_index(op.f('ix_slot_identifier_slot_pk'), table_name='slot_identifier')
    op.drop_index(op.f('ix_slot_identifier_created_at'), table_name='slot_identifier')
    op.drop_index(op.f('ix_slot_identifier_assigner_id'), table_name='slot_identifier')
    op.drop_table('slot_identifier')
    op.drop_index(op.f('ix_slot_appointment_type_coding_updated_at'), table_name='slot_appointment_type_coding')
    op.drop_index(op.f('ix_slot_appointment_type_coding_tenant_id'), table_name='slot_appointment_type_coding')
    op.drop_index(op.f('ix_slot_appointment_type_coding_slot_pk'), table_name='slot_appointment_type_coding')
    op.drop_index(op.f('ix_slot_appointment_type_coding_created_at'), table_name='slot_appointment_type_coding')
    op.drop_table('slot_appointment_type_coding')
    op.drop_index(op.f('ix_schedule_specialty_updated_at'), table_name='schedule_specialty')
    op.drop_index(op.f('ix_schedule_specialty_tenant_id'), table_name='schedule_specialty')
    op.drop_index(op.f('ix_schedule_specialty_schedule_pk'), table_name='schedule_specialty')
    op.drop_index(op.f('ix_schedule_specialty_created_at'), table_name='schedule_specialty')
    op.drop_table('schedule_specialty')
    op.drop_index(op.f('ix_schedule_service_type_updated_at'), table_name='schedule_service_type')
    op.drop_index(op.f('ix_schedule_service_type_tenant_id'), table_name='schedule_service_type')
    op.drop_index(op.f('ix_schedule_service_type_schedule_pk'), table_name='schedule_service_type')
    op.drop_index(op.f('ix_schedule_service_type_created_at'), table_name='schedule_service_type')
    op.drop_table('schedule_service_type')
    op.drop_index(op.f('ix_schedule_service_category_updated_at'), table_name='schedule_service_category')
    op.drop_index(op.f('ix_schedule_service_category_tenant_id'), table_name='schedule_service_category')
    op.drop_index(op.f('ix_schedule_service_category_schedule_pk'), table_name='schedule_service_category')
    op.drop_index(op.f('ix_schedule_service_category_created_at'), table_name='schedule_service_category')
    op.drop_table('schedule_service_category')
    op.drop_index(op.f('ix_schedule_identifier_updated_at'), table_name='schedule_identifier')
    op.drop_index(op.f('ix_schedule_identifier_tenant_id'), table_name='schedule_identifier')
    op.drop_index(op.f('ix_schedule_identifier_schedule_pk'), table_name='schedule_identifier')
    op.drop_index(op.f('ix_schedule_identifier_created_at'), table_name='schedule_identifier')
    op.drop_index(op.f('ix_schedule_identifier_assigner_id'), table_name='schedule_identifier')
    op.drop_table('schedule_identifier')
    op.drop_index(op.f('ix_schedule_actor_updated_at'), table_name='schedule_actor')
    op.drop_index(op.f('ix_schedule_actor_tenant_id'), table_name='schedule_actor')
    op.drop_index(op.f('ix_schedule_actor_schedule_pk'), table_name='schedule_actor')
    op.drop_index(op.f('ix_schedule_actor_reference_id'), table_name='schedule_actor')
    op.drop_index(op.f('ix_schedule_actor_created_at'), table_name='schedule_actor')
    op.drop_table('schedule_actor')
    op.drop_index(op.f('ix_practitioner_telecom_updated_at'), table_name='practitioner_telecom')
    op.drop_index(op.f('ix_practitioner_telecom_tenant_id'), table_name='practitioner_telecom')
    op.drop_index(op.f('ix_practitioner_telecom_practitioner_pk'), table_name='practitioner_telecom')
    op.drop_index(op.f('ix_practitioner_telecom_created_at'), table_name='practitioner_telecom')
    op.drop_table('practitioner_telecom')
    op.drop_index(op.f('ix_practitioner_role_telecom_updated_at'), table_name='practitioner_role_telecom')
    op.drop_index(op.f('ix_practitioner_role_telecom_tenant_id'), table_name='practitioner_role_telecom')
    op.drop_index(op.f('ix_practitioner_role_telecom_practitioner_role_pk'), table_name='practitioner_role_telecom')
    op.drop_index(op.f('ix_practitioner_role_telecom_created_at'), table_name='practitioner_role_telecom')
    op.drop_table('practitioner_role_telecom')
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
    op.drop_index(op.f('ix_practitioner_qualification_updated_at'), table_name='practitioner_qualification')
    op.drop_index(op.f('ix_practitioner_qualification_tenant_id'), table_name='practitioner_qualification')
    op.drop_index(op.f('ix_practitioner_qualification_practitioner_pk'), table_name='practitioner_qualification')
    op.drop_index(op.f('ix_practitioner_qualification_issuer_id'), table_name='practitioner_qualification')
    op.drop_index(op.f('ix_practitioner_qualification_created_at'), table_name='practitioner_qualification')
    op.drop_table('practitioner_qualification')
    op.drop_index(op.f('ix_practitioner_photo_updated_at'), table_name='practitioner_photo')
    op.drop_index(op.f('ix_practitioner_photo_tenant_id'), table_name='practitioner_photo')
    op.drop_index(op.f('ix_practitioner_photo_practitioner_pk'), table_name='practitioner_photo')
    op.drop_index(op.f('ix_practitioner_photo_created_at'), table_name='practitioner_photo')
    op.drop_table('practitioner_photo')
    op.drop_index(op.f('ix_practitioner_name_updated_at'), table_name='practitioner_name')
    op.drop_index(op.f('ix_practitioner_name_tenant_id'), table_name='practitioner_name')
    op.drop_index(op.f('ix_practitioner_name_practitioner_pk'), table_name='practitioner_name')
    op.drop_index(op.f('ix_practitioner_name_created_at'), table_name='practitioner_name')
    op.drop_table('practitioner_name')
    op.drop_index(op.f('ix_practitioner_identifier_updated_at'), table_name='practitioner_identifier')
    op.drop_index(op.f('ix_practitioner_identifier_tenant_id'), table_name='practitioner_identifier')
    op.drop_index(op.f('ix_practitioner_identifier_practitioner_pk'), table_name='practitioner_identifier')
    op.drop_index(op.f('ix_practitioner_identifier_created_at'), table_name='practitioner_identifier')
    op.drop_index(op.f('ix_practitioner_identifier_assigner_id'), table_name='practitioner_identifier')
    op.drop_table('practitioner_identifier')
    op.drop_index(op.f('ix_practitioner_communication_updated_at'), table_name='practitioner_communication')
    op.drop_index(op.f('ix_practitioner_communication_tenant_id'), table_name='practitioner_communication')
    op.drop_index(op.f('ix_practitioner_communication_practitioner_pk'), table_name='practitioner_communication')
    op.drop_index(op.f('ix_practitioner_communication_created_at'), table_name='practitioner_communication')
    op.drop_table('practitioner_communication')
    op.drop_index(op.f('ix_practitioner_address_updated_at'), table_name='practitioner_address')
    op.drop_index(op.f('ix_practitioner_address_tenant_id'), table_name='practitioner_address')
    op.drop_index(op.f('ix_practitioner_address_practitioner_pk'), table_name='practitioner_address')
    op.drop_index(op.f('ix_practitioner_address_created_at'), table_name='practitioner_address')
    op.drop_table('practitioner_address')
    op.drop_index(op.f('ix_organization_type_updated_at'), table_name='organization_type')
    op.drop_index(op.f('ix_organization_type_tenant_id'), table_name='organization_type')
    op.drop_index(op.f('ix_organization_type_organization_pk'), table_name='organization_type')
    op.drop_index(op.f('ix_organization_type_created_at'), table_name='organization_type')
    op.drop_table('organization_type')
    op.drop_index(op.f('ix_organization_telecom_updated_at'), table_name='organization_telecom')
    op.drop_index(op.f('ix_organization_telecom_tenant_id'), table_name='organization_telecom')
    op.drop_index(op.f('ix_organization_telecom_organization_pk'), table_name='organization_telecom')
    op.drop_index(op.f('ix_organization_telecom_created_at'), table_name='organization_telecom')
    op.drop_table('organization_telecom')
    op.drop_index(op.f('ix_organization_identifier_updated_at'), table_name='organization_identifier')
    op.drop_index(op.f('ix_organization_identifier_tenant_id'), table_name='organization_identifier')
    op.drop_index(op.f('ix_organization_identifier_organization_pk'), table_name='organization_identifier')
    op.drop_index(op.f('ix_organization_identifier_created_at'), table_name='organization_identifier')
    op.drop_index(op.f('ix_organization_identifier_assigner_id'), table_name='organization_identifier')
    op.drop_table('organization_identifier')
    op.drop_index(op.f('ix_organization_endpoint_updated_at'), table_name='organization_endpoint')
    op.drop_index(op.f('ix_organization_endpoint_tenant_id'), table_name='organization_endpoint')
    op.drop_index(op.f('ix_organization_endpoint_reference_id'), table_name='organization_endpoint')
    op.drop_index(op.f('ix_organization_endpoint_organization_pk'), table_name='organization_endpoint')
    op.drop_index(op.f('ix_organization_endpoint_created_at'), table_name='organization_endpoint')
    op.drop_table('organization_endpoint')
    op.drop_index(op.f('ix_organization_contact_updated_at'), table_name='organization_contact')
    op.drop_index(op.f('ix_organization_contact_tenant_id'), table_name='organization_contact')
    op.drop_index(op.f('ix_organization_contact_organization_pk'), table_name='organization_contact')
    op.drop_index(op.f('ix_organization_contact_created_at'), table_name='organization_contact')
    op.drop_table('organization_contact')
    op.drop_index(op.f('ix_organization_alias_updated_at'), table_name='organization_alias')
    op.drop_index(op.f('ix_organization_alias_tenant_id'), table_name='organization_alias')
    op.drop_index(op.f('ix_organization_alias_organization_pk'), table_name='organization_alias')
    op.drop_index(op.f('ix_organization_alias_created_at'), table_name='organization_alias')
    op.drop_table('organization_alias')
    op.drop_index(op.f('ix_organization_address_updated_at'), table_name='organization_address')
    op.drop_index(op.f('ix_organization_address_tenant_id'), table_name='organization_address')
    op.drop_index(op.f('ix_organization_address_organization_pk'), table_name='organization_address')
    op.drop_index(op.f('ix_organization_address_created_at'), table_name='organization_address')
    op.drop_table('organization_address')
    op.drop_index(op.f('ix_location_type_updated_at'), table_name='location_type')
    op.drop_index(op.f('ix_location_type_tenant_id'), table_name='location_type')
    op.drop_index(op.f('ix_location_type_location_pk'), table_name='location_type')
    op.drop_index(op.f('ix_location_type_created_at'), table_name='location_type')
    op.drop_table('location_type')
    op.drop_index(op.f('ix_location_telecom_updated_at'), table_name='location_telecom')
    op.drop_index(op.f('ix_location_telecom_tenant_id'), table_name='location_telecom')
    op.drop_index(op.f('ix_location_telecom_location_pk'), table_name='location_telecom')
    op.drop_index(op.f('ix_location_telecom_created_at'), table_name='location_telecom')
    op.drop_table('location_telecom')
    op.drop_index(op.f('ix_location_physical_type_coding_updated_at'), table_name='location_physical_type_coding')
    op.drop_index(op.f('ix_location_physical_type_coding_tenant_id'), table_name='location_physical_type_coding')
    op.drop_index(op.f('ix_location_physical_type_coding_location_pk'), table_name='location_physical_type_coding')
    op.drop_index(op.f('ix_location_physical_type_coding_created_at'), table_name='location_physical_type_coding')
    op.drop_table('location_physical_type_coding')
    op.drop_index(op.f('ix_location_identifier_updated_at'), table_name='location_identifier')
    op.drop_index(op.f('ix_location_identifier_tenant_id'), table_name='location_identifier')
    op.drop_index(op.f('ix_location_identifier_location_pk'), table_name='location_identifier')
    op.drop_index(op.f('ix_location_identifier_created_at'), table_name='location_identifier')
    op.drop_index(op.f('ix_location_identifier_assigner_id'), table_name='location_identifier')
    op.drop_table('location_identifier')
    op.drop_index(op.f('ix_location_hours_of_operation_updated_at'), table_name='location_hours_of_operation')
    op.drop_index(op.f('ix_location_hours_of_operation_tenant_id'), table_name='location_hours_of_operation')
    op.drop_index(op.f('ix_location_hours_of_operation_location_pk'), table_name='location_hours_of_operation')
    op.drop_index(op.f('ix_location_hours_of_operation_created_at'), table_name='location_hours_of_operation')
    op.drop_table('location_hours_of_operation')
    op.drop_index(op.f('ix_location_endpoint_updated_at'), table_name='location_endpoint')
    op.drop_index(op.f('ix_location_endpoint_tenant_id'), table_name='location_endpoint')
    op.drop_index(op.f('ix_location_endpoint_reference_id'), table_name='location_endpoint')
    op.drop_index(op.f('ix_location_endpoint_location_pk'), table_name='location_endpoint')
    op.drop_index(op.f('ix_location_endpoint_created_at'), table_name='location_endpoint')
    op.drop_table('location_endpoint')
    op.drop_index(op.f('ix_location_alias_updated_at'), table_name='location_alias')
    op.drop_index(op.f('ix_location_alias_tenant_id'), table_name='location_alias')
    op.drop_index(op.f('ix_location_alias_location_pk'), table_name='location_alias')
    op.drop_index(op.f('ix_location_alias_created_at'), table_name='location_alias')
    op.drop_table('location_alias')
    op.drop_index(op.f('ix_healthcare_service_type_updated_at'), table_name='healthcare_service_type')
    op.drop_index(op.f('ix_healthcare_service_type_tenant_id'), table_name='healthcare_service_type')
    op.drop_index(op.f('ix_healthcare_service_type_healthcare_service_pk'), table_name='healthcare_service_type')
    op.drop_index(op.f('ix_healthcare_service_type_created_at'), table_name='healthcare_service_type')
    op.drop_table('healthcare_service_type')
    op.drop_index(op.f('ix_healthcare_service_telecom_updated_at'), table_name='healthcare_service_telecom')
    op.drop_index(op.f('ix_healthcare_service_telecom_tenant_id'), table_name='healthcare_service_telecom')
    op.drop_index(op.f('ix_healthcare_service_telecom_healthcare_service_pk'), table_name='healthcare_service_telecom')
    op.drop_index(op.f('ix_healthcare_service_telecom_created_at'), table_name='healthcare_service_telecom')
    op.drop_table('healthcare_service_telecom')
    op.drop_index(op.f('ix_healthcare_service_specialty_updated_at'), table_name='healthcare_service_specialty')
    op.drop_index(op.f('ix_healthcare_service_specialty_tenant_id'), table_name='healthcare_service_specialty')
    op.drop_index(op.f('ix_healthcare_service_specialty_healthcare_service_pk'), table_name='healthcare_service_specialty')
    op.drop_index(op.f('ix_healthcare_service_specialty_created_at'), table_name='healthcare_service_specialty')
    op.drop_table('healthcare_service_specialty')
    op.drop_index(op.f('ix_healthcare_service_service_provision_code_updated_at'), table_name='healthcare_service_service_provision_code')
    op.drop_index(op.f('ix_healthcare_service_service_provision_code_tenant_id'), table_name='healthcare_service_service_provision_code')
    op.drop_index(op.f('ix_healthcare_service_service_provision_code_healthcare_service_pk'), table_name='healthcare_service_service_provision_code')
    op.drop_index(op.f('ix_healthcare_service_service_provision_code_created_at'), table_name='healthcare_service_service_provision_code')
    op.drop_table('healthcare_service_service_provision_code')
    op.drop_index(op.f('ix_healthcare_service_referral_method_updated_at'), table_name='healthcare_service_referral_method')
    op.drop_index(op.f('ix_healthcare_service_referral_method_tenant_id'), table_name='healthcare_service_referral_method')
    op.drop_index(op.f('ix_healthcare_service_referral_method_healthcare_service_pk'), table_name='healthcare_service_referral_method')
    op.drop_index(op.f('ix_healthcare_service_referral_method_created_at'), table_name='healthcare_service_referral_method')
    op.drop_table('healthcare_service_referral_method')
    op.drop_index(op.f('ix_healthcare_service_program_updated_at'), table_name='healthcare_service_program')
    op.drop_index(op.f('ix_healthcare_service_program_tenant_id'), table_name='healthcare_service_program')
    op.drop_index(op.f('ix_healthcare_service_program_healthcare_service_pk'), table_name='healthcare_service_program')
    op.drop_index(op.f('ix_healthcare_service_program_created_at'), table_name='healthcare_service_program')
    op.drop_table('healthcare_service_program')
    op.drop_index(op.f('ix_healthcare_service_not_available_updated_at'), table_name='healthcare_service_not_available')
    op.drop_index(op.f('ix_healthcare_service_not_available_tenant_id'), table_name='healthcare_service_not_available')
    op.drop_index(op.f('ix_healthcare_service_not_available_healthcare_service_pk'), table_name='healthcare_service_not_available')
    op.drop_index(op.f('ix_healthcare_service_not_available_created_at'), table_name='healthcare_service_not_available')
    op.drop_table('healthcare_service_not_available')
    op.drop_index(op.f('ix_healthcare_service_location_updated_at'), table_name='healthcare_service_location')
    op.drop_index(op.f('ix_healthcare_service_location_tenant_id'), table_name='healthcare_service_location')
    op.drop_index(op.f('ix_healthcare_service_location_reference_id'), table_name='healthcare_service_location')
    op.drop_index(op.f('ix_healthcare_service_location_healthcare_service_pk'), table_name='healthcare_service_location')
    op.drop_index(op.f('ix_healthcare_service_location_created_at'), table_name='healthcare_service_location')
    op.drop_table('healthcare_service_location')
    op.drop_index(op.f('ix_healthcare_service_identifier_updated_at'), table_name='healthcare_service_identifier')
    op.drop_index(op.f('ix_healthcare_service_identifier_tenant_id'), table_name='healthcare_service_identifier')
    op.drop_index(op.f('ix_healthcare_service_identifier_healthcare_service_pk'), table_name='healthcare_service_identifier')
    op.drop_index(op.f('ix_healthcare_service_identifier_created_at'), table_name='healthcare_service_identifier')
    op.drop_index(op.f('ix_healthcare_service_identifier_assigner_id'), table_name='healthcare_service_identifier')
    op.drop_table('healthcare_service_identifier')
    op.drop_index(op.f('ix_healthcare_service_endpoint_updated_at'), table_name='healthcare_service_endpoint')
    op.drop_index(op.f('ix_healthcare_service_endpoint_tenant_id'), table_name='healthcare_service_endpoint')
    op.drop_index(op.f('ix_healthcare_service_endpoint_reference_id'), table_name='healthcare_service_endpoint')
    op.drop_index(op.f('ix_healthcare_service_endpoint_healthcare_service_pk'), table_name='healthcare_service_endpoint')
    op.drop_index(op.f('ix_healthcare_service_endpoint_created_at'), table_name='healthcare_service_endpoint')
    op.drop_table('healthcare_service_endpoint')
    op.drop_index(op.f('ix_healthcare_service_eligibility_updated_at'), table_name='healthcare_service_eligibility')
    op.drop_index(op.f('ix_healthcare_service_eligibility_tenant_id'), table_name='healthcare_service_eligibility')
    op.drop_index(op.f('ix_healthcare_service_eligibility_healthcare_service_pk'), table_name='healthcare_service_eligibility')
    op.drop_index(op.f('ix_healthcare_service_eligibility_created_at'), table_name='healthcare_service_eligibility')
    op.drop_table('healthcare_service_eligibility')
    op.drop_index(op.f('ix_healthcare_service_coverage_area_updated_at'), table_name='healthcare_service_coverage_area')
    op.drop_index(op.f('ix_healthcare_service_coverage_area_tenant_id'), table_name='healthcare_service_coverage_area')
    op.drop_index(op.f('ix_healthcare_service_coverage_area_reference_id'), table_name='healthcare_service_coverage_area')
    op.drop_index(op.f('ix_healthcare_service_coverage_area_healthcare_service_pk'), table_name='healthcare_service_coverage_area')
    op.drop_index(op.f('ix_healthcare_service_coverage_area_created_at'), table_name='healthcare_service_coverage_area')
    op.drop_table('healthcare_service_coverage_area')
    op.drop_index(op.f('ix_healthcare_service_communication_updated_at'), table_name='healthcare_service_communication')
    op.drop_index(op.f('ix_healthcare_service_communication_tenant_id'), table_name='healthcare_service_communication')
    op.drop_index(op.f('ix_healthcare_service_communication_healthcare_service_pk'), table_name='healthcare_service_communication')
    op.drop_index(op.f('ix_healthcare_service_communication_created_at'), table_name='healthcare_service_communication')
    op.drop_table('healthcare_service_communication')
    op.drop_index(op.f('ix_healthcare_service_characteristic_updated_at'), table_name='healthcare_service_characteristic')
    op.drop_index(op.f('ix_healthcare_service_characteristic_tenant_id'), table_name='healthcare_service_characteristic')
    op.drop_index(op.f('ix_healthcare_service_characteristic_healthcare_service_pk'), table_name='healthcare_service_characteristic')
    op.drop_index(op.f('ix_healthcare_service_characteristic_created_at'), table_name='healthcare_service_characteristic')
    op.drop_table('healthcare_service_characteristic')
    op.drop_index(op.f('ix_healthcare_service_category_updated_at'), table_name='healthcare_service_category')
    op.drop_index(op.f('ix_healthcare_service_category_tenant_id'), table_name='healthcare_service_category')
    op.drop_index(op.f('ix_healthcare_service_category_healthcare_service_pk'), table_name='healthcare_service_category')
    op.drop_index(op.f('ix_healthcare_service_category_created_at'), table_name='healthcare_service_category')
    op.drop_table('healthcare_service_category')
    op.drop_index(op.f('ix_healthcare_service_available_time_updated_at'), table_name='healthcare_service_available_time')
    op.drop_index(op.f('ix_healthcare_service_available_time_tenant_id'), table_name='healthcare_service_available_time')
    op.drop_index(op.f('ix_healthcare_service_available_time_healthcare_service_pk'), table_name='healthcare_service_available_time')
    op.drop_index(op.f('ix_healthcare_service_available_time_created_at'), table_name='healthcare_service_available_time')
    op.drop_table('healthcare_service_available_time')
    op.drop_index(op.f('ix_terminology_value_set_canonical_url'), table_name='terminology_value_set')
    op.drop_table('terminology_value_set')
    op.drop_index(op.f('ix_terminology_code_system_canonical_url'), table_name='terminology_code_system')
    op.drop_table('terminology_code_system')
    op.drop_index(op.f('ix_slot_updated_at'), table_name='slot')
    op.drop_index(op.f('ix_slot_tenant_id'), table_name='slot')
    op.drop_index(op.f('ix_slot_slot_id'), table_name='slot')
    op.drop_index(op.f('ix_slot_schedule_id'), table_name='slot')
    op.drop_index(op.f('ix_slot_id'), table_name='slot')
    op.drop_index(op.f('ix_slot_created_at'), table_name='slot')
    op.drop_table('slot')
    op.drop_index(op.f('ix_schedule_updated_at'), table_name='schedule')
    op.drop_index(op.f('ix_schedule_tenant_id'), table_name='schedule')
    op.drop_index(op.f('ix_schedule_schedule_id'), table_name='schedule')
    op.drop_index(op.f('ix_schedule_id'), table_name='schedule')
    op.drop_index(op.f('ix_schedule_created_at'), table_name='schedule')
    op.drop_table('schedule')
    op.drop_index(op.f('ix_practitioner_role_updated_at'), table_name='practitioner_role')
    op.drop_index(op.f('ix_practitioner_role_tenant_id'), table_name='practitioner_role')
    op.drop_index(op.f('ix_practitioner_role_practitioner_role_id'), table_name='practitioner_role')
    op.drop_index(op.f('ix_practitioner_role_practitioner_id'), table_name='practitioner_role')
    op.drop_index(op.f('ix_practitioner_role_organization_id'), table_name='practitioner_role')
    op.drop_index(op.f('ix_practitioner_role_id'), table_name='practitioner_role')
    op.drop_index(op.f('ix_practitioner_role_created_at'), table_name='practitioner_role')
    op.drop_table('practitioner_role')
    op.drop_index(op.f('ix_practitioner_user_id'), table_name='practitioner')
    op.drop_index(op.f('ix_practitioner_updated_at'), table_name='practitioner')
    op.drop_index(op.f('ix_practitioner_tenant_id'), table_name='practitioner')
    op.drop_index(op.f('ix_practitioner_practitioner_id'), table_name='practitioner')
    op.drop_index(op.f('ix_practitioner_id'), table_name='practitioner')
    op.drop_index(op.f('ix_practitioner_created_at'), table_name='practitioner')
    op.drop_table('practitioner')
    op.drop_index(op.f('ix_organization_updated_at'), table_name='organization')
    op.drop_index(op.f('ix_organization_tenant_id'), table_name='organization')
    op.drop_index(op.f('ix_organization_partof_id'), table_name='organization')
    op.drop_index(op.f('ix_organization_organization_id'), table_name='organization')
    op.drop_index(op.f('ix_organization_id'), table_name='organization')
    op.drop_index(op.f('ix_organization_created_at'), table_name='organization')
    op.drop_table('organization')
    op.drop_index(op.f('ix_location_updated_at'), table_name='location')
    op.drop_index(op.f('ix_location_tenant_id'), table_name='location')
    op.drop_index(op.f('ix_location_part_of_id'), table_name='location')
    op.drop_index(op.f('ix_location_name'), table_name='location')
    op.drop_index(op.f('ix_location_managing_organization_id'), table_name='location')
    op.drop_index(op.f('ix_location_location_id'), table_name='location')
    op.drop_index(op.f('ix_location_id'), table_name='location')
    op.drop_index(op.f('ix_location_created_at'), table_name='location')
    op.drop_table('location')
    op.drop_index(op.f('ix_healthcare_service_updated_at'), table_name='healthcare_service')
    op.drop_index(op.f('ix_healthcare_service_tenant_id'), table_name='healthcare_service')
    op.drop_index(op.f('ix_healthcare_service_provided_by_id'), table_name='healthcare_service')
    op.drop_index(op.f('ix_healthcare_service_name'), table_name='healthcare_service')
    op.drop_index(op.f('ix_healthcare_service_id'), table_name='healthcare_service')
    op.drop_index(op.f('ix_healthcare_service_healthcare_service_id'), table_name='healthcare_service')
    op.drop_index(op.f('ix_healthcare_service_created_at'), table_name='healthcare_service')
    op.drop_table('healthcare_service')
    op.drop_index('uq_fhir_profile_base_singleton', table_name='fhir_profile', postgresql_where=sa.text('scope_id IS NULL'), sqlite_where=sa.text('scope_id IS NULL'))
    op.drop_index('uq_fhir_profile_active_scoped', table_name='fhir_profile', postgresql_where=sa.text("status = 'active' AND scope_id IS NOT NULL"), sqlite_where=sa.text("status = 'active' AND scope_id IS NOT NULL"))
    op.drop_index('ix_fhir_profile_scope_level', table_name='fhir_profile')
    op.drop_index('ix_fhir_profile_scope_id', table_name='fhir_profile')
    op.drop_index('ix_fhir_profile_resource_type', table_name='fhir_profile')
    op.drop_table('fhir_profile')
    op.execute('DROP SEQUENCE IF EXISTS healthcare_service_pub_seq')
    op.execute('DROP SEQUENCE IF EXISTS location_pub_seq')
    op.execute('DROP SEQUENCE IF EXISTS organization_pub_seq')
    op.execute('DROP SEQUENCE IF EXISTS practitioner_pub_seq')
    op.execute('DROP SEQUENCE IF EXISTS practitioner_role_pub_seq')
    op.execute('DROP SEQUENCE IF EXISTS schedule_pub_seq')
    op.execute('DROP SEQUENCE IF EXISTS slot_pub_seq')
    # ### end Alembic commands ###

    # --- explicit enum type drop (reverse of upgrade()'s creation block) ---
    op.execute("DROP TYPE IF EXISTS slot_status")
    op.execute("DROP TYPE IF EXISTS schedule_reference_type")
    op.execute("DROP TYPE IF EXISTS schedule_actor_reference_type")
    op.execute("DROP TYPE IF EXISTS practitioner_role_location_reference_type")
    op.execute("DROP TYPE IF EXISTS practitioner_role_healthcare_service_reference_type")
    op.execute("DROP TYPE IF EXISTS practitioner_role_endpoint_reference_type")
    op.execute("DROP TYPE IF EXISTS practitioner_reference_type")
    op.execute("DROP TYPE IF EXISTS organization_reference_type")
    op.execute("DROP TYPE IF EXISTS organization_endpoint_ref_type")
    op.execute("DROP TYPE IF EXISTS location_status")
    op.execute("DROP TYPE IF EXISTS location_part_of_reference_type")
    op.execute("DROP TYPE IF EXISTS location_mode")
    op.execute("DROP TYPE IF EXISTS location_endpoint_reference_type")
    op.execute("DROP TYPE IF EXISTS identifier_use")
    op.execute("DROP TYPE IF EXISTS human_name_use")
    op.execute("DROP TYPE IF EXISTS healthcare_service_location_reference_type")
    op.execute("DROP TYPE IF EXISTS healthcare_service_endpoint_reference_type")
    op.execute("DROP TYPE IF EXISTS healthcare_service_coverage_area_reference_type")
    op.execute("DROP TYPE IF EXISTS fhir_profile_status")
    op.execute("DROP TYPE IF EXISTS fhir_profile_scope_level")
    op.execute("DROP TYPE IF EXISTS contact_point_use")
    op.execute("DROP TYPE IF EXISTS contact_point_system")
    op.execute("DROP TYPE IF EXISTS administrative_gender")
    op.execute("DROP TYPE IF EXISTS address_use")
    op.execute("DROP TYPE IF EXISTS address_type")
