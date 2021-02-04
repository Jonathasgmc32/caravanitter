"""followers

Revision ID: 5006b3a783a6
Revises: bb25177a7dc2
Create Date: 2021-01-28 13:43:20.349027

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5006b3a783a6'
down_revision = 'bb25177a7dc2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('followers',
    sa.Column('follower_id', sa.Integer(), nullable=True),
    sa.Column('followed_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['followed_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['follower_id'], ['users.id'], )
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('followers')
    # ### end Alembic commands ###
