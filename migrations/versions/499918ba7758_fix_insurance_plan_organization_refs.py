"""fix_insurance_plan_organization_refs

Revision ID: 499918ba7758
Revises: 4bd3cf74b229
Create Date: 2026-07-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '499918ba7758'
down_revision: Union[str, None] = '4bd3cf74b229'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### add missing _type discriminator columns (organization_reference_type
    # already exists as a Postgres type from the initial migration — reuse it,
    # never re-create) ###
    org_ref_type = sa.Enum('Organization', name='organization_reference_type', create_type=False)

    op.add_column('insurance_plan', sa.Column('owned_by_type', org_ref_type, nullable=True))
    op.add_column('insurance_plan', sa.Column('administered_by_type', org_ref_type, nullable=True))
    op.add_column('insurance_plan_network', sa.Column('reference_type', org_ref_type, nullable=True))
    op.add_column('insurance_plan_coverage_network', sa.Column('reference_type', org_ref_type, nullable=True))
    op.add_column('insurance_plan_plan_network', sa.Column('reference_type', org_ref_type, nullable=True))

    # ### backfill: existing rows store the raw public organization_id the
    # client sent in the reference string. Reinterpret each as an
    # organization_id lookup and rewrite to the matching internal
    # organization.id PK. Anything that doesn't resolve to a real
    # organization is nulled out rather than left pointing at the wrong row
    # once the FK constraint below starts being enforced. ###
    op.execute("""
        UPDATE insurance_plan ip
        SET owned_by_id = org.id, owned_by_type = 'Organization'
        FROM organization org
        WHERE ip.owned_by_id = org.organization_id
    """)
    op.execute("""
        UPDATE insurance_plan
        SET owned_by_id = NULL, owned_by_type = NULL
        WHERE owned_by_id IS NOT NULL
          AND owned_by_id NOT IN (SELECT id FROM organization)
    """)

    op.execute("""
        UPDATE insurance_plan ip
        SET administered_by_id = org.id, administered_by_type = 'Organization'
        FROM organization org
        WHERE ip.administered_by_id = org.organization_id
    """)
    op.execute("""
        UPDATE insurance_plan
        SET administered_by_id = NULL, administered_by_type = NULL
        WHERE administered_by_id IS NOT NULL
          AND administered_by_id NOT IN (SELECT id FROM organization)
    """)

    op.execute("""
        UPDATE insurance_plan_network t
        SET reference_id = org.id, reference_type = 'Organization'
        FROM organization org
        WHERE t.reference_id = org.organization_id
    """)
    op.execute("""
        UPDATE insurance_plan_network
        SET reference_id = NULL, reference_type = NULL
        WHERE reference_id IS NOT NULL
          AND reference_id NOT IN (SELECT id FROM organization)
    """)

    op.execute("""
        UPDATE insurance_plan_coverage_network t
        SET reference_id = org.id, reference_type = 'Organization'
        FROM organization org
        WHERE t.reference_id = org.organization_id
    """)
    op.execute("""
        UPDATE insurance_plan_coverage_network
        SET reference_id = NULL, reference_type = NULL
        WHERE reference_id IS NOT NULL
          AND reference_id NOT IN (SELECT id FROM organization)
    """)

    op.execute("""
        UPDATE insurance_plan_plan_network t
        SET reference_id = org.id, reference_type = 'Organization'
        FROM organization org
        WHERE t.reference_id = org.organization_id
    """)
    op.execute("""
        UPDATE insurance_plan_plan_network
        SET reference_id = NULL, reference_type = NULL
        WHERE reference_id IS NOT NULL
          AND reference_id NOT IN (SELECT id FROM organization)
    """)

    # ### now that data is clean, enforce FK + index like every other
    # Organization-reference column in the codebase ###
    op.create_index(op.f('ix_insurance_plan_owned_by_id'), 'insurance_plan', ['owned_by_id'], unique=False)
    op.create_foreign_key(
        'fk_insurance_plan_owned_by_id_organization',
        'insurance_plan', 'organization', ['owned_by_id'], ['id'],
    )
    op.create_index(op.f('ix_insurance_plan_administered_by_id'), 'insurance_plan', ['administered_by_id'], unique=False)
    op.create_foreign_key(
        'fk_insurance_plan_administered_by_id_organization',
        'insurance_plan', 'organization', ['administered_by_id'], ['id'],
    )
    op.create_index(op.f('ix_insurance_plan_network_reference_id'), 'insurance_plan_network', ['reference_id'], unique=False)
    op.create_foreign_key(
        'fk_insurance_plan_network_reference_id_organization',
        'insurance_plan_network', 'organization', ['reference_id'], ['id'],
    )
    op.create_index(op.f('ix_insurance_plan_coverage_network_reference_id'), 'insurance_plan_coverage_network', ['reference_id'], unique=False)
    op.create_foreign_key(
        'fk_insurance_plan_coverage_network_reference_id_organization',
        'insurance_plan_coverage_network', 'organization', ['reference_id'], ['id'],
    )
    op.create_index(op.f('ix_insurance_plan_plan_network_reference_id'), 'insurance_plan_plan_network', ['reference_id'], unique=False)
    op.create_foreign_key(
        'fk_insurance_plan_plan_network_reference_id_organization',
        'insurance_plan_plan_network', 'organization', ['reference_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_insurance_plan_plan_network_reference_id_organization', 'insurance_plan_plan_network', type_='foreignkey')
    op.drop_index(op.f('ix_insurance_plan_plan_network_reference_id'), table_name='insurance_plan_plan_network')
    op.drop_constraint('fk_insurance_plan_coverage_network_reference_id_organization', 'insurance_plan_coverage_network', type_='foreignkey')
    op.drop_index(op.f('ix_insurance_plan_coverage_network_reference_id'), table_name='insurance_plan_coverage_network')
    op.drop_constraint('fk_insurance_plan_network_reference_id_organization', 'insurance_plan_network', type_='foreignkey')
    op.drop_index(op.f('ix_insurance_plan_network_reference_id'), table_name='insurance_plan_network')
    op.drop_constraint('fk_insurance_plan_administered_by_id_organization', 'insurance_plan', type_='foreignkey')
    op.drop_index(op.f('ix_insurance_plan_administered_by_id'), table_name='insurance_plan')
    op.drop_constraint('fk_insurance_plan_owned_by_id_organization', 'insurance_plan', type_='foreignkey')
    op.drop_index(op.f('ix_insurance_plan_owned_by_id'), table_name='insurance_plan')

    op.drop_column('insurance_plan_plan_network', 'reference_type')
    op.drop_column('insurance_plan_coverage_network', 'reference_type')
    op.drop_column('insurance_plan_network', 'reference_type')
    op.drop_column('insurance_plan', 'administered_by_type')
    op.drop_column('insurance_plan', 'owned_by_type')
