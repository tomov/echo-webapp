"""add device_token column to user model

Revision ID: 35775c0122c0
Revises: 4ab613d39af3
Create Date: 2013-03-21 22:37:39.849651

"""

# revision identifiers, used by Alembic.
revision = '35775c0122c0'
down_revision = '4ab613d39af3'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('users', sa.Column('device_token', sa.String(length = 64)))


def downgrade():
    op.drop_column('users', 'device_token')
