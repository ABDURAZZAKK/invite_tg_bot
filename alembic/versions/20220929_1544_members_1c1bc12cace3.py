"""members

Revision ID: 1c1bc12cace3
Revises: 86108f244203
Create Date: 2022-09-29 15:44:49.851738

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '1c1bc12cace3'
down_revision = '86108f244203'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('members',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('fio', sa.String(length=300), nullable=False),
                    sa.Column('nick', sa.String(length=100), nullable=True),
                    sa.Column('date_add', sa.DateTime(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    comment='Спарсенные участники групп'
                    )


def downgrade() -> None:
    op.drop_table('members')
