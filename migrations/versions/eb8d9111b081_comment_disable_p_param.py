"""comment disable p param

Revision ID: eb8d9111b081
Revises: 61193ce01160
Create Date: 2016-09-22 16:25:10.083053

"""

# revision identifiers, used by Alembic.
revision = 'eb8d9111b081'
down_revision = '61193ce01160'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('comments', sa.Column('disabled', sa.Boolean(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('comments', 'disabled')
    ### end Alembic commands ###
