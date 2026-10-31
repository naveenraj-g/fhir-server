"""add_related_person_tables

Revision ID: 888cf5f065fa
Revises: 33d766495d0f
Create Date: 2026-10-31 13:46:19.253002

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '888cf5f065fa'
down_revision: Union[str, None] = '33d766495d0f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Create Enum Types ───────────────────────────────────────────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE related_person_patient_reference_type AS ENUM ('Patient');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # ── 2. Create Public ID Sequence ───────────────────────────────────────────
    op.execute("CREATE SEQUENCE IF NOT EXISTS related_person_pub_seq START WITH 300000 INCREMENT BY 1")

    # ── 3. Create Tables and Indexes ───────────────────────────────────────────
    op.create_table('related_person',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('related_person_id', sa.BigInteger(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=True),
    sa.Column('patient_reference', sa.String(), nullable=False),
    sa.Column('patient_type', postgresql.ENUM('Patient', name='related_person_patient_reference_type', create_type=False), nullable=False),
    sa.Column('patient_id', sa.BigInteger(), nullable=True),
    sa.Column('patient_display', sa.String(), nullable=True),
    sa.Column('gender', postgresql.ENUM('male', 'female', 'other', 'unknown', name='administrative_gender', create_type=False), nullable=True),
    sa.Column('birth_date', sa.Date(), nullable=True),
    sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('extension', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'"), nullable=False),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )


    op.create_table('related_person_identifier',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('related_person_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['related_person_pk'], ['related_person.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


    op.create_table('related_person_identifier_type_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('related_person_identifier_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['related_person_identifier_id'], ['related_person_identifier.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


    op.create_table('related_person_relationship',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('related_person_pk', sa.BigInteger(), nullable=False),
    sa.Column('text', sa.String(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['related_person_pk'], ['related_person.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


    op.create_table('related_person_relationship_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('related_person_relationship_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['related_person_relationship_id'], ['related_person_relationship.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


    op.create_table('related_person_name',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('related_person_pk', sa.BigInteger(), nullable=False),
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
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['related_person_pk'], ['related_person.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


    op.create_table('related_person_telecom',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('related_person_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['related_person_pk'], ['related_person.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


    op.create_table('related_person_address',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('related_person_pk', sa.BigInteger(), nullable=False),
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
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['related_person_pk'], ['related_person.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


    op.create_table('related_person_photo',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('related_person_pk', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['related_person_pk'], ['related_person.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


    op.create_table('related_person_communication',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('related_person_pk', sa.BigInteger(), nullable=False),
    sa.Column('language_text', sa.String(), nullable=True),
    sa.Column('preferred', sa.Boolean(), nullable=True),
    sa.Column('tenant_id', sa.String(), nullable=False),
    sa.Column('created_by', sa.String(), nullable=False),
    sa.Column('updated_by', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['related_person_pk'], ['related_person.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


    op.create_table('related_person_communication_language_coding',
    sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column('related_person_communication_id', sa.BigInteger(), nullable=False),
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
    sa.ForeignKeyConstraint(['related_person_communication_id'], ['related_person_communication.id'], ),
    sa.PrimaryKeyConstraint('id')
    )



def downgrade() -> None:
    # ── Drop Tables in Reverse Dependency Order ────────────────────────────────
    op.drop_table('related_person_communication_language_coding')
    op.drop_table('related_person_communication')
    op.drop_table('related_person_photo')
    op.drop_table('related_person_address')
    op.drop_table('related_person_telecom')
    op.drop_table('related_person_name')
    op.drop_table('related_person_relationship_coding')
    op.drop_table('related_person_relationship')
    op.drop_table('related_person_identifier_type_coding')
    op.drop_table('related_person_identifier')
    op.drop_table('related_person')

    # ── Drop Sequence ──────────────────────────────────────────────────────────
    op.execute("DROP SEQUENCE IF EXISTS related_person_pub_seq")

    # ── Drop Enum Types ────────────────────────────────────────────────────────
    op.execute("DROP TYPE IF EXISTS related_person_patient_reference_type")
