"""add location_lot and location_lat to Quote

Revision ID: 3cdcd0017f1a
Revises: 2ebc6756bafa
Create Date: 2013-02-02 20:41:31.600833

"""

# revision identifiers, used by Alembic.
revision = '3cdcd0017f1a'
down_revision = '2ebc6756bafa'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('quotes', sa.Column('location_lat', sa.Float(precision = 32)))
    op.add_column('quotes', sa.Column('location_long', sa.Float(precision = 32)))

def downgrade():
    op.drop_column('quotes', 'location_lat')
    op.drop_column('quotes', 'location_long')
