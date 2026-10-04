"""unique child consent constraint

Revision ID: 002_unique_child_consent
Revises: 001_initial_schema
Create Date: 2026-10-04 18:05:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '002_unique_child_consent'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint('uq_consents_child_id', 'consents', ['child_id'])


def downgrade() -> None:
    op.drop_constraint('uq_consents_child_id', 'consents', type_='unique')
