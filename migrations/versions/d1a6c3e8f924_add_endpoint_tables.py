"""add endpoint: whole FHIR resource in `content` JSONB plus a search index

Revision ID: d1a6c3e8f924
Revises: c9f5b2d7e813
Create Date: 2026-11-20 10:00:00.000000

Endpoint is a new resource, built Medplum-style from the start (see
EndpointModel's docstring): the whole FHIR resource lives in
`endpoint.content`, and every other column/table is a search index for one of
the FHIR R4 Endpoint search parameters (or `_id`/`_lastUpdated`), derived from
`content`:

  endpoint: status (Postgres enum endpoint_status), connection_type_system/
      _code/_display_norm, name/name_norm, managing_organization_reference/
      _type/_id/_identifier_system/_value
  endpoint_identifier: one row per identifier x type.coding
  endpoint_payload_type: one row per payloadType coding (+ a text-only row)

Public ids come from endpoint_pub_seq (start 620000). Nothing to backfill:
there is no old Endpoint data.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd1a6c3e8f924'
down_revision: Union[str, None] = 'c9f5b2d7e813'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_STATUS = ('active', 'suspended', 'error', 'off', 'entered-in-error', 'test')


def upgrade() -> None:
    endpoint_status = postgresql.ENUM(*_STATUS, name='endpoint_status')
    endpoint_status.create(op.get_bind(), checkfirst=True)
    op.execute("CREATE SEQUENCE IF NOT EXISTS endpoint_pub_seq START WITH 620000 INCREMENT BY 1")

    op.create_table(
        'endpoint',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('endpoint_id', sa.BigInteger(), server_default=sa.text("nextval('endpoint_pub_seq')"), nullable=False),
        sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', postgresql.ENUM(*_STATUS, name='endpoint_status', create_type=False), nullable=True),
        sa.Column('connection_type_system', sa.String(), nullable=True),
        sa.Column('connection_type_code', sa.String(), nullable=True),
        sa.Column('connection_type_display_norm', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('name_norm', sa.String(), nullable=True),
        sa.Column('managing_organization_reference', sa.String(), nullable=True),
        sa.Column(
            'managing_organization_type',
            postgresql.ENUM('Organization', name='organization_reference_type', create_type=False),
            nullable=True,
        ),
        sa.Column('managing_organization_id', sa.BigInteger(), nullable=True),
        sa.Column('managing_organization_identifier_system', sa.String(), nullable=True),
        sa.Column('managing_organization_identifier_value', sa.String(), nullable=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('created_by', sa.String(), nullable=False),
        sa.Column('updated_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_endpoint_id'), 'endpoint', ['id'], unique=False)
    op.create_index(op.f('ix_endpoint_endpoint_id'), 'endpoint', ['endpoint_id'], unique=True)
    op.create_index(op.f('ix_endpoint_connection_type_code'), 'endpoint', ['connection_type_code'], unique=False)
    op.create_index(op.f('ix_endpoint_managing_organization_id'), 'endpoint', ['managing_organization_id'], unique=False)
    op.create_index(op.f('ix_endpoint_tenant_id'), 'endpoint', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_endpoint_created_at'), 'endpoint', ['created_at'], unique=False)
    op.create_index(op.f('ix_endpoint_updated_at'), 'endpoint', ['updated_at'], unique=False)
    # text_pattern_ops: lets the default `name_norm LIKE 'value%'` use the index.
    op.create_index('ix_endpoint_name_norm', 'endpoint', ['name_norm'], unique=False,
                    postgresql_ops={'name_norm': 'text_pattern_ops'})

    op.create_table(
        'endpoint_identifier',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('endpoint_pk', sa.BigInteger(), sa.ForeignKey('endpoint.id'), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('value', sa.String(), nullable=True),
        sa.Column('type_system', sa.String(), nullable=True),
        sa.Column('type_code', sa.String(), nullable=True),
        sa.Column('type_text_norm', sa.String(), nullable=True),
        sa.Column('type_display_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_endpoint_identifier_endpoint_pk'), 'endpoint_identifier', ['endpoint_pk'], unique=False)
    op.create_index(op.f('ix_endpoint_identifier_value'), 'endpoint_identifier', ['value'], unique=False)

    op.create_table(
        'endpoint_payload_type',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('endpoint_pk', sa.BigInteger(), sa.ForeignKey('endpoint.id'), nullable=False),
        sa.Column('system', sa.String(), nullable=True),
        sa.Column('code', sa.String(), nullable=True),
        sa.Column('display_norm', sa.String(), nullable=True),
        sa.Column('text_norm', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_endpoint_payload_type_endpoint_pk'), 'endpoint_payload_type', ['endpoint_pk'], unique=False)
    op.create_index(op.f('ix_endpoint_payload_type_code'), 'endpoint_payload_type', ['code'], unique=False)


def downgrade() -> None:
    op.drop_table('endpoint_payload_type')
    op.drop_table('endpoint_identifier')
    op.drop_table('endpoint')
    op.execute("DROP SEQUENCE IF EXISTS endpoint_pub_seq")
    postgresql.ENUM(name='endpoint_status').drop(op.get_bind(), checkfirst=True)
