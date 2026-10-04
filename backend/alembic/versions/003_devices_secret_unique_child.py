"""devices secret hash and unique child device constraint

Revision ID: 003_devices_secret_unique_child
Revises: 002_unique_child_consent
Create Date: 2026-10-04 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003_devices_secret_unique_child'
down_revision: Union[str, None] = '002_unique_child_consent'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('devices', sa.Column('device_secret_hash', sa.String(length=255), nullable=False, server_default=''))
    op.create_unique_constraint('uq_devices_child_id', 'devices', ['child_id'])


def downgrade() -> None:
    op.drop_constraint('uq_devices_child_id', 'devices', type_='unique')
    op.drop_column('devices', 'device_secret_hash')
