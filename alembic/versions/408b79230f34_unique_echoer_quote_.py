"""unique echoer-quote pairs

Revision ID: 408b79230f34
Revises: 3cdcd0017f1a
Create Date: 2013-03-21 19:21:26.636422

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '408b79230f34'
down_revision = '3cdcd0017f1a'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_unique_constraint('unique-echoer-quote-pair', 'echoes', ['quote_id', 'user_id'])
    pass


def downgrade():
    op.drop_constraint('unique-echoer-quote-pair', 'echoes')
    pass
