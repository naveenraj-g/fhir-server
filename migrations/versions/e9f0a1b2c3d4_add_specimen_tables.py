"""add_specimen_tables

Revision ID: e9f0a1b2c3d4
Revises: d8a2b3c4e5f6
Create Date: 2026-10-30 15:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e9f0a1b2c3d4'
down_revision: Union[str, None] = 'd8a2b3c4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE specimen_status AS ENUM ('available', 'unavailable', 'unsatisfactory', 'entered-in-error')")
    op.execute("CREATE TYPE specimen_quantity_comparator AS ENUM ('lt', 'le', 'ge', 'gt')")
    op.execute("CREATE TYPE specimen_subject_reference_type AS ENUM ('Patient', 'Group', 'Device', 'Substance', 'Location')")
    op.execute("CREATE TYPE specimen_collector_reference_type AS ENUM ('Practitioner', 'PractitionerRole')")
    op.execute("CREATE TYPE specimen_parent_reference_type AS ENUM ('Specimen')")
    op.execute("CREATE TYPE specimen_additive_reference_type AS ENUM ('Substance')")
    op.execute("CREATE TYPE specimen_note_author_reference_type AS ENUM ('Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson')")
    op.execute("CREATE SEQUENCE IF NOT EXISTS specimen_pub_seq START 310000 INCREMENT 1")

    # Main specimen table
    op.create_table(
        'specimen',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('specimen_id', sa.BigInteger(), server_default=sa.text("nextval('specimen_pub_seq')"), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        # accessionIdentifier (0..1 Identifier)
        sa.Column('accession_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('accession_identifier_type_text', sa.String(), nullable=True),
        sa.Column('accession_identifier_system', sa.String(), nullable=True),
        sa.Column('accession_identifier_value', sa.String(), nullable=True),
        sa.Column('accession_identifier_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('accession_identifier_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('accession_identifier_assigner_reference', sa.String(), nullable=True),
        sa.Column('accession_identifier_assigner_type', postgresql.ENUM('Organization', name='organization_reference_type', create_type=False), nullable=True),
        sa.Column('accession_identifier_assigner_id', sa.BigInteger(), nullable=True),
        sa.Column('accession_identifier_assigner_display', sa.String(), nullable=True),
        sa.Column('accession_identifier_assigner_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('accession_identifier_assigner_identifier_system', sa.String(), nullable=True),
        sa.Column('accession_identifier_assigner_identifier_value', sa.String(), nullable=True),
        sa.Column('accession_identifier_assigner_identifier_type_text', sa.String(), nullable=True),
        # status (0..1 code)
        sa.Column('status', postgresql.ENUM('available', 'unavailable', 'unsatisfactory', 'entered-in-error', name='specimen_status', create_type=False), nullable=True),
        # type (0..1 CodeableConcept)
        sa.Column('type_text', sa.String(), nullable=True),
        # subject (0..1 Reference(Patient | Group | Device | Substance | Location))
        sa.Column('subject_reference', sa.String(), nullable=True),
        sa.Column('subject_type', postgresql.ENUM('Patient', 'Group', 'Device', 'Substance', 'Location', name='specimen_subject_reference_type', create_type=False), nullable=True),
        sa.Column('subject_id', sa.BigInteger(), nullable=True),
        sa.Column('subject_display', sa.String(), nullable=True),
        sa.Column('subject_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('subject_identifier_system', sa.String(), nullable=True),
        sa.Column('subject_identifier_value', sa.String(), nullable=True),
        sa.Column('subject_identifier_type_text', sa.String(), nullable=True),
        # receivedTime (0..1 dateTime)
        sa.Column('received_time', sa.DateTime(timezone=True), nullable=True),
        # collection (0..1 BackboneElement)
        sa.Column('collection_collector_reference', sa.String(), nullable=True),
        sa.Column('collection_collector_type', postgresql.ENUM('Practitioner', 'PractitionerRole', name='specimen_collector_reference_type', create_type=False), nullable=True),
        sa.Column('collection_collector_id', sa.BigInteger(), nullable=True),
        sa.Column('collection_collector_display', sa.String(), nullable=True),
        sa.Column('collection_collector_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('collection_collector_identifier_system', sa.String(), nullable=True),
        sa.Column('collection_collector_identifier_value', sa.String(), nullable=True),
        sa.Column('collection_collector_identifier_type_text', sa.String(), nullable=True),
        sa.Column('collection_collected_date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('collection_collected_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('collection_collected_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('collection_duration_value', sa.Numeric(), nullable=True),
        sa.Column('collection_duration_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='specimen_quantity_comparator', create_type=False), nullable=True),
        sa.Column('collection_duration_unit', sa.String(), nullable=True),
        sa.Column('collection_duration_system', sa.String(), nullable=True),
        sa.Column('collection_duration_code', sa.String(), nullable=True),
        sa.Column('collection_quantity_value', sa.Numeric(), nullable=True),
        sa.Column('collection_quantity_unit', sa.String(), nullable=True),
        sa.Column('collection_quantity_system', sa.String(), nullable=True),
        sa.Column('collection_quantity_code', sa.String(), nullable=True),
        sa.Column('collection_method_text', sa.String(), nullable=True),
        sa.Column('collection_body_site_text', sa.String(), nullable=True),
        sa.Column('collection_fasting_status_text', sa.String(), nullable=True),
        sa.Column('collection_fasting_status_duration_value', sa.Numeric(), nullable=True),
        sa.Column('collection_fasting_status_duration_comparator', postgresql.ENUM('lt', 'le', 'ge', 'gt', name='specimen_quantity_comparator', create_type=False), nullable=True),
        sa.Column('collection_fasting_status_duration_unit', sa.String(), nullable=True),
        sa.Column('collection_fasting_status_duration_system', sa.String(), nullable=True),
        sa.Column('collection_fasting_status_duration_code', sa.String(), nullable=True),
        # extension
        sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default='[]', nullable=False),
        # tenant audit mixin
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('specimen_id')
    )
    op.create_index(op.f('ix_specimen_id'), 'specimen', ['id'], unique=False)
    op.create_index(op.f('ix_specimen_specimen_id'), 'specimen', ['specimen_id'], unique=True)
    op.create_index(op.f('ix_specimen_user_id'), 'specimen', ['user_id'], unique=False)
    op.create_index(op.f('ix_specimen_accession_identifier_assigner_id'), 'specimen', ['accession_identifier_assigner_id'], unique=False)
    op.create_index(op.f('ix_specimen_subject_id'), 'specimen', ['subject_id'], unique=False)
    op.create_index(op.f('ix_specimen_collection_collector_id'), 'specimen', ['collection_collector_id'], unique=False)

    # specimen_identifier
    op.create_table(
        'specimen_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('specimen_pk', sa.BigInteger(), nullable=False),
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
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['specimen_pk'], ['specimen.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_identifier_specimen_pk'), 'specimen_identifier', ['specimen_pk'], unique=False)
    op.create_index(op.f('ix_specimen_identifier_assigner_id'), 'specimen_identifier', ['assigner_id'], unique=False)

    # specimen_identifier_type_coding
    op.create_table(
        'specimen_identifier_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('specimen_identifier_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['specimen_identifier_id'], ['specimen_identifier.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_identifier_type_coding_specimen_identifier_id'), 'specimen_identifier_type_coding', ['specimen_identifier_id'], unique=False)

    # specimen_accession_identifier_type_coding
    op.create_table(
        'specimen_accession_identifier_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('specimen_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['specimen_pk'], ['specimen.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_accession_identifier_type_coding_specimen_pk'), 'specimen_accession_identifier_type_coding', ['specimen_pk'], unique=False)

    # specimen_type_coding
    op.create_table(
        'specimen_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('specimen_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['specimen_pk'], ['specimen.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_type_coding_specimen_pk'), 'specimen_type_coding', ['specimen_pk'], unique=False)

    # specimen_parent
    op.create_table(
        'specimen_parent',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('specimen_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Specimen', name='specimen_parent_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('reference_identifier_system', sa.String(), nullable=True),
        sa.Column('reference_identifier_value', sa.String(), nullable=True),
        sa.Column('reference_identifier_type_text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['specimen_pk'], ['specimen.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_parent_specimen_pk'), 'specimen_parent', ['specimen_pk'], unique=False)
    op.create_index(op.f('ix_specimen_parent_reference_id'), 'specimen_parent', ['reference_id'], unique=False)

    # specimen_request
    op.create_table(
        'specimen_request',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('specimen_pk', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('ServiceRequest', name='service_request_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('reference_identifier_system', sa.String(), nullable=True),
        sa.Column('reference_identifier_value', sa.String(), nullable=True),
        sa.Column('reference_identifier_type_text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['specimen_pk'], ['specimen.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_request_specimen_pk'), 'specimen_request', ['specimen_pk'], unique=False)
    op.create_index(op.f('ix_specimen_request_reference_id'), 'specimen_request', ['reference_id'], unique=False)

    # specimen_collection_method_coding
    op.create_table(
        'specimen_collection_method_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('specimen_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['specimen_pk'], ['specimen.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_collection_method_coding_specimen_pk'), 'specimen_collection_method_coding', ['specimen_pk'], unique=False)

    # specimen_collection_body_site_coding
    op.create_table(
        'specimen_collection_body_site_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('specimen_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['specimen_pk'], ['specimen.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_collection_body_site_coding_specimen_pk'), 'specimen_collection_body_site_coding', ['specimen_pk'], unique=False)

    # specimen_collection_fasting_status_coding
    op.create_table(
        'specimen_collection_fasting_status_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('specimen_pk', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['specimen_pk'], ['specimen.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_collection_fasting_status_coding_specimen_pk'), 'specimen_collection_fasting_status_coding', ['specimen_pk'], unique=False)

    # specimen_processing
    op.create_table(
        'specimen_processing',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('specimen_pk', sa.BigInteger(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('procedure_text', sa.String(), nullable=True),
        sa.Column('time_date_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('time_period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('time_period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['specimen_pk'], ['specimen.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_processing_specimen_pk'), 'specimen_processing', ['specimen_pk'], unique=False)

    # specimen_processing_procedure_coding
    op.create_table(
        'specimen_processing_procedure_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('specimen_processing_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['specimen_processing_id'], ['specimen_processing.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_processing_procedure_coding_specimen_processing_id'), 'specimen_processing_procedure_coding', ['specimen_processing_id'], unique=False)

    # specimen_processing_additive
    op.create_table(
        'specimen_processing_additive',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('specimen_processing_id', sa.BigInteger(), nullable=False),
        sa.Column('reference_reference', sa.String(), nullable=True),
        sa.Column('reference_type', postgresql.ENUM('Substance', name='specimen_additive_reference_type', create_type=False), nullable=True),
        sa.Column('reference_id', sa.BigInteger(), nullable=True),
        sa.Column('reference_display', sa.String(), nullable=True),
        sa.Column('reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('reference_identifier_system', sa.String(), nullable=True),
        sa.Column('reference_identifier_value', sa.String(), nullable=True),
        sa.Column('reference_identifier_type_text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['specimen_processing_id'], ['specimen_processing.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_processing_additive_specimen_processing_id'), 'specimen_processing_additive', ['specimen_processing_id'], unique=False)
    op.create_index(op.f('ix_specimen_processing_additive_reference_id'), 'specimen_processing_additive', ['reference_id'], unique=False)

    # specimen_container
    op.create_table(
        'specimen_container',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('specimen_pk', sa.BigInteger(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('type_text', sa.String(), nullable=True),
        sa.Column('capacity_value', sa.Numeric(), nullable=True),
        sa.Column('capacity_unit', sa.String(), nullable=True),
        sa.Column('capacity_system', sa.String(), nullable=True),
        sa.Column('capacity_code', sa.String(), nullable=True),
        sa.Column('specimen_quantity_value', sa.Numeric(), nullable=True),
        sa.Column('specimen_quantity_unit', sa.String(), nullable=True),
        sa.Column('specimen_quantity_system', sa.String(), nullable=True),
        sa.Column('specimen_quantity_code', sa.String(), nullable=True),
        sa.Column('additive_codeable_concept_text', sa.String(), nullable=True),
        sa.Column('additive_reference_reference', sa.String(), nullable=True),
        sa.Column('additive_reference_type', postgresql.ENUM('Substance', name='specimen_additive_reference_type', create_type=False), nullable=True),
        sa.Column('additive_reference_id', sa.BigInteger(), nullable=True),
        sa.Column('additive_reference_display', sa.String(), nullable=True),
        sa.Column('additive_reference_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('additive_reference_identifier_system', sa.String(), nullable=True),
        sa.Column('additive_reference_identifier_value', sa.String(), nullable=True),
        sa.Column('additive_reference_identifier_type_text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['specimen_pk'], ['specimen.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_container_specimen_pk'), 'specimen_container', ['specimen_pk'], unique=False)
    op.create_index(op.f('ix_specimen_container_additive_reference_id'), 'specimen_container', ['additive_reference_id'], unique=False)

    # specimen_container_identifier
    op.create_table(
        'specimen_container_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('specimen_container_id', sa.BigInteger(), nullable=False),
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
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['specimen_container_id'], ['specimen_container.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_container_identifier_specimen_container_id'), 'specimen_container_identifier', ['specimen_container_id'], unique=False)
    op.create_index(op.f('ix_specimen_container_identifier_assigner_id'), 'specimen_container_identifier', ['assigner_id'], unique=False)

    # specimen_container_identifier_type_coding
    op.create_table(
        'specimen_container_identifier_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('specimen_container_identifier_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['specimen_container_identifier_id'], ['specimen_container_identifier.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_container_identifier_type_coding_specimen_container_identifier_id'), 'specimen_container_identifier_type_coding', ['specimen_container_identifier_id'], unique=False)

    # specimen_container_type_coding
    op.create_table(
        'specimen_container_type_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('specimen_container_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['specimen_container_id'], ['specimen_container.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_container_type_coding_specimen_container_id'), 'specimen_container_type_coding', ['specimen_container_id'], unique=False)

    # specimen_container_additive_coding
    op.create_table(
        'specimen_container_additive_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('specimen_container_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['specimen_container_id'], ['specimen_container.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_container_additive_coding_specimen_container_id'), 'specimen_container_additive_coding', ['specimen_container_id'], unique=False)

    # specimen_condition
    op.create_table(
        'specimen_condition',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('specimen_pk', sa.BigInteger(), nullable=False),
        sa.Column('text', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['specimen_pk'], ['specimen.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_condition_specimen_pk'), 'specimen_condition', ['specimen_pk'], unique=False)

    # specimen_condition_coding
    op.create_table(
        'specimen_condition_coding',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('specimen_condition_id', sa.BigInteger(), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display', sa.String(), nullable=True),
        sa.Column('user_selected', sa.Boolean(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['specimen_condition_id'], ['specimen_condition.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_condition_coding_specimen_condition_id'), 'specimen_condition_coding', ['specimen_condition_id'], unique=False)

    # specimen_note
    op.create_table(
        'specimen_note',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('specimen_pk', sa.BigInteger(), nullable=False),
        sa.Column('author_string', sa.String(), nullable=True),
        sa.Column('author_reference', sa.String(), nullable=True),
        sa.Column('author_type', postgresql.ENUM('Practitioner', 'PractitionerRole', 'Patient', 'RelatedPerson', name='specimen_note_author_reference_type', create_type=False), nullable=True),
        sa.Column('author_id', sa.BigInteger(), nullable=True),
        sa.Column('author_display', sa.String(), nullable=True),
        sa.Column('author_identifier_use', postgresql.ENUM('usual', 'official', 'temp', 'secondary', 'old', name='identifier_use', create_type=False), nullable=True),
        sa.Column('author_identifier_system', sa.String(), nullable=True),
        sa.Column('author_identifier_value', sa.String(), nullable=True),
        sa.Column('author_identifier_type_text', sa.String(), nullable=True),
        sa.Column('time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['specimen_pk'], ['specimen.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_specimen_note_specimen_pk'), 'specimen_note', ['specimen_pk'], unique=False)
    op.create_index(op.f('ix_specimen_note_author_id'), 'specimen_note', ['author_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_specimen_note_author_id'), table_name='specimen_note')
    op.drop_index(op.f('ix_specimen_note_specimen_pk'), table_name='specimen_note')
    op.drop_table('specimen_note')

    op.drop_index(op.f('ix_specimen_condition_coding_specimen_condition_id'), table_name='specimen_condition_coding')
    op.drop_table('specimen_condition_coding')

    op.drop_index(op.f('ix_specimen_condition_specimen_pk'), table_name='specimen_condition')
    op.drop_table('specimen_condition')

    op.drop_index(op.f('ix_specimen_container_additive_coding_specimen_container_id'), table_name='specimen_container_additive_coding')
    op.drop_table('specimen_container_additive_coding')

    op.drop_index(op.f('ix_specimen_container_type_coding_specimen_container_id'), table_name='specimen_container_type_coding')
    op.drop_table('specimen_container_type_coding')

    op.drop_index(op.f('ix_specimen_container_identifier_type_coding_specimen_container_identifier_id'), table_name='specimen_container_identifier_type_coding')
    op.drop_table('specimen_container_identifier_type_coding')

    op.drop_index(op.f('ix_specimen_container_identifier_assigner_id'), table_name='specimen_container_identifier')
    op.drop_index(op.f('ix_specimen_container_identifier_specimen_container_id'), table_name='specimen_container_identifier')
    op.drop_table('specimen_container_identifier')

    op.drop_index(op.f('ix_specimen_container_additive_reference_id'), table_name='specimen_container')
    op.drop_index(op.f('ix_specimen_container_specimen_pk'), table_name='specimen_container')
    op.drop_table('specimen_container')

    op.drop_index(op.f('ix_specimen_processing_additive_reference_id'), table_name='specimen_processing_additive')
    op.drop_index(op.f('ix_specimen_processing_additive_specimen_processing_id'), table_name='specimen_processing_additive')
    op.drop_table('specimen_processing_additive')

    op.drop_index(op.f('ix_specimen_processing_procedure_coding_specimen_processing_id'), table_name='specimen_processing_procedure_coding')
    op.drop_table('specimen_processing_procedure_coding')

    op.drop_index(op.f('ix_specimen_processing_specimen_pk'), table_name='specimen_processing')
    op.drop_table('specimen_processing')

    op.drop_index(op.f('ix_specimen_collection_fasting_status_coding_specimen_pk'), table_name='specimen_collection_fasting_status_coding')
    op.drop_table('specimen_collection_fasting_status_coding')

    op.drop_index(op.f('ix_specimen_collection_body_site_coding_specimen_pk'), table_name='specimen_collection_body_site_coding')
    op.drop_table('specimen_collection_body_site_coding')

    op.drop_index(op.f('ix_specimen_collection_method_coding_specimen_pk'), table_name='specimen_collection_method_coding')
    op.drop_table('specimen_collection_method_coding')

    op.drop_index(op.f('ix_specimen_request_reference_id'), table_name='specimen_request')
    op.drop_index(op.f('ix_specimen_request_specimen_pk'), table_name='specimen_request')
    op.drop_table('specimen_request')

    op.drop_index(op.f('ix_specimen_parent_reference_id'), table_name='specimen_parent')
    op.drop_index(op.f('ix_specimen_parent_specimen_pk'), table_name='specimen_parent')
    op.drop_table('specimen_parent')

    op.drop_index(op.f('ix_specimen_type_coding_specimen_pk'), table_name='specimen_type_coding')
    op.drop_table('specimen_type_coding')

    op.drop_index(op.f('ix_specimen_accession_identifier_type_coding_specimen_pk'), table_name='specimen_accession_identifier_type_coding')
    op.drop_table('specimen_accession_identifier_type_coding')

    op.drop_index(op.f('ix_specimen_identifier_type_coding_specimen_identifier_id'), table_name='specimen_identifier_type_coding')
    op.drop_table('specimen_identifier_type_coding')

    op.drop_index(op.f('ix_specimen_identifier_assigner_id'), table_name='specimen_identifier')
    op.drop_index(op.f('ix_specimen_identifier_specimen_pk'), table_name='specimen_identifier')
    op.drop_table('specimen_identifier')

    op.drop_index(op.f('ix_specimen_collection_collector_id'), table_name='specimen')
    op.drop_index(op.f('ix_specimen_subject_id'), table_name='specimen')
    op.drop_index(op.f('ix_specimen_accession_identifier_assigner_id'), table_name='specimen')
    op.drop_index(op.f('ix_specimen_user_id'), table_name='specimen')
    op.drop_index(op.f('ix_specimen_specimen_id'), table_name='specimen')
    op.drop_index(op.f('ix_specimen_id'), table_name='specimen')
    op.drop_table('specimen')

    op.execute("DROP SEQUENCE IF EXISTS specimen_pub_seq")
    op.execute("DROP TYPE IF EXISTS specimen_note_author_reference_type")
    op.execute("DROP TYPE IF EXISTS specimen_additive_reference_type")
    op.execute("DROP TYPE IF EXISTS specimen_parent_reference_type")
    op.execute("DROP TYPE IF EXISTS specimen_collector_reference_type")
    op.execute("DROP TYPE IF EXISTS specimen_subject_reference_type")
    op.execute("DROP TYPE IF EXISTS specimen_quantity_comparator")
    op.execute("DROP TYPE IF EXISTS specimen_status")
