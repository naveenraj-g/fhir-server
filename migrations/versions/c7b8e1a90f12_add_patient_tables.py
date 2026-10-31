"""add_patient_tables

Revision ID: c7b8e1a90f12
Revises: 5fcb63494189
Create Date: 2026-10-30 13:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c7b8e1a90f12'
down_revision: Union[str, None] = '5fcb63494189'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE patient_link_type AS ENUM ('replaced_by', 'replaces', 'refer', 'seealso')")
    op.execute("CREATE TYPE patient_link_other_type AS ENUM ('Patient', 'RelatedPerson')")
    op.execute("CREATE TYPE patient_general_practitioner_reference_type AS ENUM ('Organization', 'Practitioner', 'PractitionerRole')")
    op.execute("CREATE SEQUENCE IF NOT EXISTS patient_pub_seq START 10000 INCREMENT 1")

    # Main patient table
    op.create_table(
        'patient',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('patient_id', sa.BigInteger(), server_default=sa.text("nextval('patient_pub_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('gender', postgresql.ENUM('male', 'female', 'other', 'unknown', name='administrative_gender', create_type=False), nullable=True),
        sa.Column('birth_date', sa.Date(), nullable=True),
        sa.Column('deceased_boolean', sa.Boolean(), nullable=True),
        sa.Column('deceased_date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('marital_status_text', sa.String(), nullable=True),
        sa.Column('multiple_birth_boolean', sa.Boolean(), nullable=True),
        sa.Column('multiple_birth_integer', sa.Integer(), nullable=True),
        sa.Column('managing_organization_reference', sa.String(), nullable=True),
        sa.Column('managing_organization_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
        sa.Column('managing_organization_id', sa.BigInteger(), nullable=True),
        sa.Column('managing_organization_display', sa.String(), nullable=True),
        sa.Column('managing_organization_identifier_system', sa.String(), nullable=True),
        sa.Column('managing_organization_identifier_value', sa.String(), nullable=True),
        sa.Column('managing_organization_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('managing_organization_identifier_type_text', sa.String(), nullable=True),
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('patient_id')
    )
    op.create_index(op.f('ix_patient_id'), 'patient', ['id'], unique=False)
    op.create_index(op.f('ix_patient_patient_id'), 'patient', ['patient_id'], unique=True)
    op.create_index(op.f('ix_patient_user_id'), 'patient', ['user_id'], unique=False)
    op.create_index(op.f('ix_patient_tenant_id'), 'patient', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_patient_created_at'), 'patient', ['created_at'], unique=False)
    op.create_index(op.f('ix_patient_updated_at'), 'patient', ['updated_at'], unique=False)
    op.create_index(op.f('ix_patient_managing_organization_id'), 'patient', ['managing_organization_id'], unique=False)

    # patient_name
    op.create_table(
        'patient_name',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('patient_pk', sa.BigInteger(), nullable=False),
        sa.Column('use', postgresql.ENUM('usual', 'official', 'temp', 'nickname', 'anonymous', 'old', 'maiden', name='human_name_use', create_type=False), nullable=True),
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
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['patient_pk'], ['patient.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patient_name_patient_pk'), 'patient_name', ['patient_pk'], unique=False)
    op.create_index(op.f('ix_patient_name_tenant_id'), 'patient_name', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_patient_name_created_at'), 'patient_name', ['created_at'], unique=False)
    op.create_index(op.f('ix_patient_name_updated_at'), 'patient_name', ['updated_at'], unique=False)

    # patient_identifier
    op.create_table(
        'patient_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('patient_pk', sa.BigInteger(), nullable=False),
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
        sa.Column('assigner_identifier_type_text', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_user_selected', sa.Boolean(), nullable=True),
        sa.Column('assigner_identifier_system', sa.String(), nullable=True),
        sa.Column('assigner_identifier_value', sa.String(), nullable=True),
        sa.Column('assigner_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('assigner_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['patient_pk'], ['patient.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patient_identifier_patient_pk'), 'patient_identifier', ['patient_pk'], unique=False)
    op.create_index(op.f('ix_patient_identifier_assigner_id'), 'patient_identifier', ['assigner_id'], unique=False)
    op.create_index(op.f('ix_patient_identifier_tenant_id'), 'patient_identifier', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_patient_identifier_created_at'), 'patient_identifier', ['created_at'], unique=False)
    op.create_index(op.f('ix_patient_identifier_updated_at'), 'patient_identifier', ['updated_at'], unique=False)

    # patient_identifier_type_coding
    op.create_table(
        'patient_identifier_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('patient_identifier_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['patient_identifier_id'], ['patient_identifier.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patient_identifier_type_coding_patient_identifier_id'), 'patient_identifier_type_coding', ['patient_identifier_id'], unique=False)
    op.create_index(op.f('ix_patient_identifier_type_coding_tenant_id'), 'patient_identifier_type_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_patient_identifier_type_coding_created_at'), 'patient_identifier_type_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_patient_identifier_type_coding_updated_at'), 'patient_identifier_type_coding', ['updated_at'], unique=False)

    # patient_telecom
    op.create_table(
        'patient_telecom',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('patient_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', postgresql.ENUM('phone', 'fax', 'email', 'pager', 'url', 'sms', 'other', name='contact_point_system', create_type=False), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('use', postgresql.ENUM('home', 'work', 'temp', 'old', 'mobile', name='contact_point_use', create_type=False), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['patient_pk'], ['patient.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patient_telecom_patient_pk'), 'patient_telecom', ['patient_pk'], unique=False)
    op.create_index(op.f('ix_patient_telecom_tenant_id'), 'patient_telecom', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_patient_telecom_created_at'), 'patient_telecom', ['created_at'], unique=False)
    op.create_index(op.f('ix_patient_telecom_updated_at'), 'patient_telecom', ['updated_at'], unique=False)

    # patient_address
    op.create_table(
        'patient_address',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('patient_pk', sa.BigInteger(), nullable=False),
        sa.Column('use', postgresql.ENUM('home', 'work', 'temp', 'old', 'billing', name='address_use', create_type=False), nullable=True),
        sa.Column('type', postgresql.ENUM('postal', 'physical', 'both', name='address_type', create_type=False), nullable=True),
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
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['patient_pk'], ['patient.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patient_address_patient_pk'), 'patient_address', ['patient_pk'], unique=False)
    op.create_index(op.f('ix_patient_address_tenant_id'), 'patient_address', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_patient_address_created_at'), 'patient_address', ['created_at'], unique=False)
    op.create_index(op.f('ix_patient_address_updated_at'), 'patient_address', ['updated_at'], unique=False)

    # patient_photo
    op.create_table(
        'patient_photo',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('patient_pk', sa.BigInteger(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=True),
        sa.Column('language', sa.String(), nullable=True),
        sa.Column('data', sa.LargeBinary(), nullable=True),
        sa.Column('url', sa.String(), nullable=True),
        sa.Column('size', sa.BigInteger(), nullable=True),
        sa.Column('hash', sa.LargeBinary(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('creation', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['patient_pk'], ['patient.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patient_photo_patient_pk'), 'patient_photo', ['patient_pk'], unique=False)
    op.create_index(op.f('ix_patient_photo_tenant_id'), 'patient_photo', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_patient_photo_created_at'), 'patient_photo', ['created_at'], unique=False)
    op.create_index(op.f('ix_patient_photo_updated_at'), 'patient_photo', ['updated_at'], unique=False)

    # patient_marital_status_coding
    op.create_table(
        'patient_marital_status_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('patient_pk', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['patient_pk'], ['patient.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patient_marital_status_coding_patient_pk'), 'patient_marital_status_coding', ['patient_pk'], unique=False)
    op.create_index(op.f('ix_patient_marital_status_coding_tenant_id'), 'patient_marital_status_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_patient_marital_status_coding_created_at'), 'patient_marital_status_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_patient_marital_status_coding_updated_at'), 'patient_marital_status_coding', ['updated_at'], unique=False)

    # patient_communication
    op.create_table(
        'patient_communication',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('patient_pk', sa.BigInteger(), nullable=False),
        sa.Column('language_text', sa.String(), nullable=True),
        sa.Column('preferred', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['patient_pk'], ['patient.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patient_communication_patient_pk'), 'patient_communication', ['patient_pk'], unique=False)
    op.create_index(op.f('ix_patient_communication_tenant_id'), 'patient_communication', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_patient_communication_created_at'), 'patient_communication', ['created_at'], unique=False)
    op.create_index(op.f('ix_patient_communication_updated_at'), 'patient_communication', ['updated_at'], unique=False)

    # patient_communication_language_coding
    op.create_table(
        'patient_communication_language_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('patient_communication_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['patient_communication_id'], ['patient_communication.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patient_communication_language_coding_patient_communication_id'), 'patient_communication_language_coding', ['patient_communication_id'], unique=False)
    op.create_index(op.f('ix_patient_communication_language_coding_tenant_id'), 'patient_communication_language_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_patient_communication_language_coding_created_at'), 'patient_communication_language_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_patient_communication_language_coding_updated_at'), 'patient_communication_language_coding', ['updated_at'], unique=False)

    # patient_general_practitioner
    op.create_table(
        'patient_general_practitioner',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('patient_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Organization', 'Practitioner', 'PractitionerRole', name='patient_general_practitioner_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('reference_identifier_system', sa.String(), nullable=True),
        sa.Column('reference_identifier_value', sa.String(), nullable=True),
        sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('reference_identifier_type_text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['patient_pk'], ['patient.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patient_general_practitioner_patient_pk'), 'patient_general_practitioner', ['patient_pk'], unique=False)
    op.create_index(op.f('ix_patient_general_practitioner_reference_id'), 'patient_general_practitioner', ['reference_id'], unique=False)
    op.create_index(op.f('ix_patient_general_practitioner_tenant_id'), 'patient_general_practitioner', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_patient_general_practitioner_created_at'), 'patient_general_practitioner', ['created_at'], unique=False)
    op.create_index(op.f('ix_patient_general_practitioner_updated_at'), 'patient_general_practitioner', ['updated_at'], unique=False)

    # patient_link
    op.create_table(
        'patient_link',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('patient_pk', sa.BigInteger(), nullable=False),
        sa.Column('other_reference', sa.String(), nullable=True),
        sa.Column('other_type', postgresql.ENUM('Patient', 'RelatedPerson', name='patient_link_other_type', create_type=False), nullable=True),
        sa.Column('other_id', sa.BigInteger(), nullable=True),
        sa.Column('other_display', sa.String(), nullable=True),
        sa.Column('other_identifier_system', sa.String(), nullable=True),
        sa.Column('other_identifier_value', sa.String(), nullable=True),
        sa.Column('other_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('other_identifier_type_text', sa.String(), nullable=True),
        sa.Column('type', postgresql.ENUM('replaced_by', 'replaces', 'refer', 'seealso', name='patient_link_type', create_type=False), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['patient_pk'], ['patient.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patient_link_patient_pk'), 'patient_link', ['patient_pk'], unique=False)
    op.create_index(op.f('ix_patient_link_other_id'), 'patient_link', ['other_id'], unique=False)
    op.create_index(op.f('ix_patient_link_tenant_id'), 'patient_link', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_patient_link_created_at'), 'patient_link', ['created_at'], unique=False)
    op.create_index(op.f('ix_patient_link_updated_at'), 'patient_link', ['updated_at'], unique=False)

    # patient_contact
    op.create_table(
        'patient_contact',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('patient_pk', sa.BigInteger(), nullable=False),
        sa.Column('gender', postgresql.ENUM('male', 'female', 'other', 'unknown', name='administrative_gender', create_type=False), nullable=True),
        sa.Column('name_use', postgresql.ENUM('usual', 'official', 'temp', 'nickname', 'anonymous', 'old', 'maiden', name='human_name_use', create_type=False), nullable=True),
        sa.Column('name_text', sa.String(), nullable=True),
        sa.Column('name_family', sa.String(), nullable=True),
        sa.Column('name_given', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('name_prefix', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('name_suffix', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('name_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('name_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('address_use', postgresql.ENUM('home', 'work', 'temp', 'old', 'billing', name='address_use', create_type=False), nullable=True),
        sa.Column('address_type', postgresql.ENUM('postal', 'physical', 'both', name='address_type', create_type=False), nullable=True),
        sa.Column('address_text', sa.String(), nullable=True),
        sa.Column('address_line', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('address_city', sa.String(), nullable=True),
        sa.Column('address_district', sa.String(), nullable=True),
        sa.Column('address_state', sa.String(), nullable=True),
        sa.Column('address_postal_code', sa.String(), nullable=True),
        sa.Column('address_country', sa.String(), nullable=True),
        sa.Column('address_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('address_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('organization_reference', sa.String(), nullable=True),
        sa.Column('organization_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
        sa.Column('organization_id', sa.BigInteger(), nullable=True),
        sa.Column('organization_display', sa.String(), nullable=True),
        sa.Column('organization_identifier_system', sa.String(), nullable=True),
        sa.Column('organization_identifier_value', sa.String(), nullable=True),
        sa.Column('organization_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('organization_identifier_type_text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['patient_pk'], ['patient.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patient_contact_patient_pk'), 'patient_contact', ['patient_pk'], unique=False)
    op.create_index(op.f('ix_patient_contact_organization_id'), 'patient_contact', ['organization_id'], unique=False)
    op.create_index(op.f('ix_patient_contact_tenant_id'), 'patient_contact', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_patient_contact_created_at'), 'patient_contact', ['created_at'], unique=False)
    op.create_index(op.f('ix_patient_contact_updated_at'), 'patient_contact', ['updated_at'], unique=False)

    # patient_contact_relationship
    op.create_table(
        'patient_contact_relationship',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('contact_id', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['contact_id'], ['patient_contact.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patient_contact_relationship_contact_id'), 'patient_contact_relationship', ['contact_id'], unique=False)
    op.create_index(op.f('ix_patient_contact_relationship_tenant_id'), 'patient_contact_relationship', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_patient_contact_relationship_created_at'), 'patient_contact_relationship', ['created_at'], unique=False)
    op.create_index(op.f('ix_patient_contact_relationship_updated_at'), 'patient_contact_relationship', ['updated_at'], unique=False)

    # patient_contact_relationship_coding
    op.create_table(
        'patient_contact_relationship_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('relationship_id', sa.BigInteger(), nullable=False),
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
        sa.ForeignKeyConstraint(['relationship_id'], ['patient_contact_relationship.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patient_contact_relationship_coding_relationship_id'), 'patient_contact_relationship_coding', ['relationship_id'], unique=False)
    op.create_index(op.f('ix_patient_contact_relationship_coding_tenant_id'), 'patient_contact_relationship_coding', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_patient_contact_relationship_coding_created_at'), 'patient_contact_relationship_coding', ['created_at'], unique=False)
    op.create_index(op.f('ix_patient_contact_relationship_coding_updated_at'), 'patient_contact_relationship_coding', ['updated_at'], unique=False)

    # patient_contact_telecom
    op.create_table(
        'patient_contact_telecom',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('contact_id', sa.BigInteger(), nullable=False),
        sa.Column('system', postgresql.ENUM('phone', 'fax', 'email', 'pager', 'url', 'sms', 'other', name='contact_point_system', create_type=False), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('use', postgresql.ENUM('home', 'work', 'temp', 'old', 'mobile', name='contact_point_use', create_type=False), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['contact_id'], ['patient_contact.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_patient_contact_telecom_contact_id'), 'patient_contact_telecom', ['contact_id'], unique=False)
    op.create_index(op.f('ix_patient_contact_telecom_tenant_id'), 'patient_contact_telecom', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_patient_contact_telecom_created_at'), 'patient_contact_telecom', ['created_at'], unique=False)
    op.create_index(op.f('ix_patient_contact_telecom_updated_at'), 'patient_contact_telecom', ['updated_at'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse FK order
    op.drop_table('patient_contact_telecom')
    op.drop_table('patient_contact_relationship_coding')
    op.drop_table('patient_contact_relationship')
    op.drop_table('patient_contact')
    op.drop_table('patient_link')
    op.drop_table('patient_general_practitioner')
    op.drop_table('patient_communication_language_coding')
    op.drop_table('patient_communication')
    op.drop_table('patient_marital_status_coding')
    op.drop_table('patient_photo')
    op.drop_table('patient_address')
    op.drop_table('patient_telecom')
    op.drop_table('patient_identifier_type_coding')
    op.drop_table('patient_identifier')
    op.drop_table('patient_name')
    op.drop_table('patient')

    op.execute("DROP SEQUENCE IF EXISTS patient_pub_seq")
    op.execute("DROP TYPE IF EXISTS patient_general_practitioner_reference_type")
    op.execute("DROP TYPE IF EXISTS patient_link_other_type")
    op.execute("DROP TYPE IF EXISTS patient_link_type")
