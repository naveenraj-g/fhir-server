"""add_document_reference_tables

Revision ID: f0a1b2c3d4e5
Revises: e9f0a1b2c3d4
Create Date: 2026-10-30 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f0a1b2c3d4e5'
down_revision: Union[str, None] = 'e9f0a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE document_reference_status AS ENUM ('current', 'superseded', 'entered-in-error')")
    op.execute("CREATE TYPE document_reference_doc_status AS ENUM ('preliminary', 'final', 'amended', 'entered-in-error')")
    op.execute("CREATE TYPE document_relationship_type AS ENUM ('replaces', 'transforms', 'signs', 'appends')")
    op.execute("CREATE TYPE document_reference_subject_reference_type AS ENUM ('Patient', 'Practitioner', 'Group', 'Device')")
    op.execute("CREATE TYPE document_reference_author_reference_type AS ENUM ('Practitioner', 'PractitionerRole', 'Organization', 'Device', 'Patient', 'RelatedPerson')")
    op.execute("CREATE TYPE document_reference_authenticator_reference_type AS ENUM ('Practitioner', 'PractitionerRole', 'Organization')")
    op.execute("CREATE TYPE document_reference_target_reference_type AS ENUM ('DocumentReference')")
    op.execute("CREATE TYPE document_reference_context_encounter_reference_type AS ENUM ('Encounter', 'EpisodeOfCare')")
    op.execute("CREATE TYPE document_reference_patient_reference_type AS ENUM ('Patient')")
    op.execute("CREATE SEQUENCE IF NOT EXISTS document_reference_pub_seq START 320000 INCREMENT 1")

    # Main document_reference table
    op.create_table(
        'document_reference',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_reference_id', sa.BigInteger(), server_default=sa.text("nextval('document_reference_pub_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        # masterIdentifier (0..1 Identifier)
        sa.Column('master_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('master_identifier_type_text', sa.String(), nullable=True),
        sa.Column('master_identifier_system', sa.String(), nullable=True),
        sa.Column('master_identifier_value', sa.String(), nullable=True),
        sa.Column('master_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('master_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('master_identifier_assigner_reference', sa.String(), nullable=True),
        sa.Column('master_identifier_assigner_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
        sa.Column('master_identifier_assigner_id', sa.BigInteger(), nullable=True),
        sa.Column('master_identifier_assigner_display', sa.String(), nullable=True),
        sa.Column('master_identifier_assigner_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('master_identifier_assigner_identifier_system', sa.String(), nullable=True),
        sa.Column('master_identifier_assigner_identifier_value', sa.String(), nullable=True),
        sa.Column('master_identifier_assigner_identifier_type_text', sa.String(), nullable=True),
        # status (1..1) & docStatus (0..1)
        sa.Column('status', postgresql.ENUM('current', 'superseded', 'entered-in-error', name='document_reference_status', create_type=False), nullable=False),
        sa.Column('doc_status', postgresql.ENUM('preliminary', 'final', 'amended', 'entered-in-error', name='document_reference_doc_status', create_type=False), nullable=True),
        # type (0..1)
        sa.Column('type_text', sa.String(), nullable=True),
        # subject (0..1 Reference)
        sa.Column('subject_reference', sa.String(), nullable=True),
        sa.Column('subject_type', postgresql.ENUM('Patient', 'Practitioner', 'Group', 'Device', name='document_reference_subject_reference_type', create_type=False), nullable=True),
        sa.Column('subject_id', sa.BigInteger(), nullable=True),
        sa.Column('subject_display', sa.String(), nullable=True),
        # date (0..1)
        sa.Column('date', sa.DateTime(timezone=True), nullable=True),
        # authenticator (0..1 Reference)
        sa.Column('authenticator_reference', sa.String(), nullable=True),
        sa.Column('authenticator_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization', name='document_reference_authenticator_reference_type', create_type=False), nullable=True),
        sa.Column('authenticator_id', sa.BigInteger(), nullable=True),
        sa.Column('authenticator_display', sa.String(), nullable=True),
        # custodian (0..1 Reference)
        sa.Column('custodian_reference', sa.String(), nullable=True),
        sa.Column('custodian_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
        sa.Column('custodian_id', sa.BigInteger(), nullable=True),
        sa.Column('custodian_display', sa.String(), nullable=True),
        # description (0..1)
        sa.Column('description', sa.String(), nullable=True),
        # context (0..1) flattened 0..1 fields
        sa.Column('context_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('context_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('context_facility_type_text', sa.String(), nullable=True),
        sa.Column('context_practice_setting_text', sa.String(), nullable=True),
        sa.Column('context_source_patient_info_reference', sa.String(), nullable=True),
        sa.Column('context_source_patient_info_type', postgresql.ENUM('Patient', name='document_reference_patient_reference_type', create_type=False), nullable=True),
        sa.Column('context_source_patient_info_id', sa.BigInteger(), nullable=True),
        sa.Column('context_source_patient_info_display', sa.String(), nullable=True),
        # extension & audit
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_reference_id'),
    )
    op.create_index(op.f('ix_document_reference_document_reference_id'), 'document_reference', ['document_reference_id'], unique=True)
    op.create_index(op.f('ix_document_reference_user_id'), 'document_reference', ['user_id'], unique=False)
    op.create_index(op.f('ix_document_reference_tenant_id'), 'document_reference', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_document_reference_subject_id'), 'document_reference', ['subject_id'], unique=False)
    op.create_index(op.f('ix_document_reference_master_identifier_assigner_id'), 'document_reference', ['master_identifier_assigner_id'], unique=False)
    op.create_index(op.f('ix_document_reference_authenticator_id'), 'document_reference', ['authenticator_id'], unique=False)
    op.create_index(op.f('ix_document_reference_custodian_id'), 'document_reference', ['custodian_id'], unique=False)
    op.create_index(op.f('ix_document_reference_context_source_patient_info_id'), 'document_reference', ['context_source_patient_info_id'], unique=False)

    # Master identifier type codings
    op.create_table(
        'document_reference_master_identifier_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_reference_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_reference_pk'], ['document_reference.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_document_reference_master_identifier_type_coding_document_reference_pk'), 'document_reference_master_identifier_type_coding', ['document_reference_pk'], unique=False)

    # Identifier child table
    op.create_table(
        'document_reference_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_reference_pk', sa.BigInteger(), nullable=False),
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
        sa.Column('assigner_identifier_system', sa.String(), nullable=True),
        sa.Column('assigner_identifier_value', sa.String(), nullable=True),
        sa.Column('assigner_identifier_type_text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_reference_pk'], ['document_reference.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_document_reference_identifier_document_reference_pk'), 'document_reference_identifier', ['document_reference_pk'], unique=False)
    op.create_index(op.f('ix_document_reference_identifier_assigner_id'), 'document_reference_identifier', ['assigner_id'], unique=False)

    # Identifier type coding grandchild table
    op.create_table(
        'document_reference_identifier_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_reference_identifier_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_reference_identifier_id'], ['document_reference_identifier.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_document_reference_identifier_type_coding_id'), 'document_reference_identifier_type_coding', ['document_reference_identifier_id'], unique=False)

    # Type codings
    op.create_table(
        'document_reference_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_reference_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_reference_pk'], ['document_reference.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_document_reference_type_coding_document_reference_pk'), 'document_reference_type_coding', ['document_reference_pk'], unique=False)

    # Category child table
    op.create_table(
        'document_reference_category',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_reference_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_reference_pk'], ['document_reference.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_document_reference_category_document_reference_pk'), 'document_reference_category', ['document_reference_pk'], unique=False)

    # Category coding grandchild table
    op.create_table(
        'document_reference_category_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_reference_category_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_reference_category_id'], ['document_reference_category.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_document_reference_category_coding_id'), 'document_reference_category_coding', ['document_reference_category_id'], unique=False)

    # Author child table
    op.create_table(
        'document_reference_author',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_reference_pk', sa.BigInteger(), nullable=False),
        sa.Column('author_reference', sa.String(), nullable=True),
        sa.Column('author_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Organization', 'Device', 'Patient', 'RelatedPerson', name='document_reference_author_reference_type', create_type=False), nullable=True),
        sa.Column('author_id', sa.BigInteger(), nullable=True),
        sa.Column('author_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_reference_pk'], ['document_reference.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_document_reference_author_document_reference_pk'), 'document_reference_author', ['document_reference_pk'], unique=False)
    op.create_index(op.f('ix_document_reference_author_author_id'), 'document_reference_author', ['author_id'], unique=False)

    # RelatesTo child table
    op.create_table(
        'document_reference_relates_to',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_reference_pk', sa.BigInteger(), nullable=False),
        sa.Column('code', postgresql.ENUM('replaces', 'transforms', 'signs', 'appends', name='document_relationship_type', create_type=False), nullable=False),
        sa.Column('target_reference', sa.String(), nullable=True),
        sa.Column('target_type', postgresql.ENUM('DocumentReference', name='document_reference_target_reference_type', create_type=False), nullable=True),
        sa.Column('target_id', sa.BigInteger(), nullable=True),
        sa.Column('target_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_reference_pk'], ['document_reference.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_document_reference_relates_to_document_reference_pk'), 'document_reference_relates_to', ['document_reference_pk'], unique=False)
    op.create_index(op.f('ix_document_reference_relates_to_target_id'), 'document_reference_relates_to', ['target_id'], unique=False)

    # SecurityLabel child table
    op.create_table(
        'document_reference_security_label',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_reference_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_reference_pk'], ['document_reference.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_document_reference_security_label_document_reference_pk'), 'document_reference_security_label', ['document_reference_pk'], unique=False)

    # SecurityLabel coding grandchild table
    op.create_table(
        'document_reference_security_label_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_reference_security_label_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_reference_security_label_id'], ['document_reference_security_label.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_document_reference_security_label_coding_id'), 'document_reference_security_label_coding', ['document_reference_security_label_id'], unique=False)

    # Content child table
    op.create_table(
        'document_reference_content',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_reference_pk', sa.BigInteger(), nullable=False),
        sa.Column('attachment_content_type', sa.String(), nullable=True),
        sa.Column('attachment_language', sa.String(), nullable=True),
        sa.Column('attachment_data', sa.Text(), nullable=True),
        sa.Column('attachment_url', sa.String(), nullable=True),
        sa.Column('attachment_size', sa.Integer(), nullable=True),
        sa.Column('attachment_hash', sa.String(), nullable=True),
        sa.Column('attachment_title', sa.String(), nullable=True),
        sa.Column('attachment_creation', sa.DateTime(timezone=True), nullable=True),
        sa.Column('format_system', sa.String(), nullable=True),
        sa.Column('format_version', sa.String(), nullable=True),
        sa.Column('format_code', sa.String(), nullable=True),
        sa.Column('format_display', sa.String(), nullable=True),
        sa.Column('format_user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_reference_pk'], ['document_reference.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_document_reference_content_document_reference_pk'), 'document_reference_content', ['document_reference_pk'], unique=False)

    # Context Encounter child table
    op.create_table(
        'document_reference_context_encounter',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_reference_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Encounter', 'EpisodeOfCare', name='document_reference_context_encounter_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_reference_pk'], ['document_reference.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_document_reference_context_encounter_document_reference_pk'), 'document_reference_context_encounter', ['document_reference_pk'], unique=False)
    op.create_index(op.f('ix_document_reference_context_encounter_reference_id'), 'document_reference_context_encounter', ['reference_id'], unique=False)

    # Context Event child table
    op.create_table(
        'document_reference_context_event',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_reference_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_reference_pk'], ['document_reference.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_document_reference_context_event_document_reference_pk'), 'document_reference_context_event', ['document_reference_pk'], unique=False)

    # Context Event coding grandchild table
    op.create_table(
        'document_reference_context_event_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_reference_context_event_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_reference_context_event_id'], ['document_reference_context_event.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_document_reference_context_event_coding_id'), 'document_reference_context_event_coding', ['document_reference_context_event_id'], unique=False)

    # Context FacilityType coding
    op.create_table(
        'document_reference_context_facility_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_reference_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_reference_pk'], ['document_reference.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_document_reference_context_facility_type_coding_pk'), 'document_reference_context_facility_type_coding', ['document_reference_pk'], unique=False)

    # Context PracticeSetting coding
    op.create_table(
        'document_reference_context_practice_setting_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_reference_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_reference_pk'], ['document_reference.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_document_reference_context_practice_setting_coding_pk'), 'document_reference_context_practice_setting_coding', ['document_reference_pk'], unique=False)

    # Context Related child table
    op.create_table(
        'document_reference_context_related',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('document_reference_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', sa.String(), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['document_reference_pk'], ['document_reference.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_document_reference_context_related_document_reference_pk'), 'document_reference_context_related', ['document_reference_pk'], unique=False)
    op.create_index(op.f('ix_document_reference_context_related_reference_id'), 'document_reference_context_related', ['reference_id'], unique=False)


def downgrade() -> None:
    op.drop_table('document_reference_context_related')
    op.drop_table('document_reference_context_practice_setting_coding')
    op.drop_table('document_reference_context_facility_type_coding')
    op.drop_table('document_reference_context_event_coding')
    op.drop_table('document_reference_context_event')
    op.drop_table('document_reference_context_encounter')
    op.drop_table('document_reference_content')
    op.drop_table('document_reference_security_label_coding')
    op.drop_table('document_reference_security_label')
    op.drop_table('document_reference_relates_to')
    op.drop_table('document_reference_author')
    op.drop_table('document_reference_category_coding')
    op.drop_table('document_reference_category')
    op.drop_table('document_reference_type_coding')
    op.drop_table('document_reference_identifier_type_coding')
    op.drop_table('document_reference_identifier')
    op.drop_table('document_reference_master_identifier_type_coding')
    op.drop_table('document_reference')

    op.execute("DROP SEQUENCE IF EXISTS document_reference_pub_seq")
    op.execute("DROP TYPE IF EXISTS document_reference_patient_reference_type")
    op.execute("DROP TYPE IF EXISTS document_reference_context_encounter_reference_type")
    op.execute("DROP TYPE IF EXISTS document_reference_target_reference_type")
    op.execute("DROP TYPE IF EXISTS document_reference_authenticator_reference_type")
    op.execute("DROP TYPE IF EXISTS document_reference_author_reference_type")
    op.execute("DROP TYPE IF EXISTS document_reference_subject_reference_type")
    op.execute("DROP TYPE IF EXISTS document_relationship_type")
    op.execute("DROP TYPE IF EXISTS document_reference_doc_status")
    op.execute("DROP TYPE IF EXISTS document_reference_status")
