"""unique favorite constraint

Revision ID: 4ab613d39af3
Revises: 408b79230f34
Create Date: 2013-03-21 19:50:56.277165

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '4ab613d39af3'
down_revision = '408b79230f34'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_unique_constraint('unique-favorite', 'favorites', ['quote_id', 'user_id'])
    pass


def downgrade():
    op.drop_constraint('unique-favorite', 'favorites')
    pass
