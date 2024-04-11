"""Add security_token column to device

Revision ID: 4e931f7417ed
Revises: 
Create Date: 2023-12-07 01:56:10.818922

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4e931f7417ed'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('device', schema=None) as batch_op:
        batch_op.add_column(sa.Column('security_token', sa.String(length=255), nullable=True))
        batch_op.create_unique_constraint('device_security_token_unique', ['security_token'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('device', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_column('security_token')

    # ### end Alembic commands ###