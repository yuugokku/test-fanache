"""text migration

Revision ID: 78e9a8c23967
Revises: 09b4faa5e938
Create Date: 2022-04-10 02:10:22.518073

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '78e9a8c23967'
down_revision = '09b4faa5e938'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('dictionary', sa.Column('scansion_url', sa.String(length=200), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('dictionary', 'scansion_url')
    # ### end Alembic commands ###
