"""client_accounts

Revision ID: 86108f244203
Revises: 6a7d996a50f8
Create Date: 2022-09-28 14:15:36.769779

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '86108f244203'
down_revision = '6a7d996a50f8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('client_accounts',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('api_id', sa.String(length=100), nullable=False),
                    sa.Column('api_hash', sa.String(length=100), nullable=False),
                    sa.Column('phone', sa.String(length=100), nullable=False),
                    sa.Column('authorized', sa.Boolean(), nullable=False, comment='пройдена авторизация'),
                    sa.Column('phone_code_hash', sa.String(length=100), nullable=True),
                    sa.Column('banned', sa.Boolean(), nullable=False, comment='аккаунт заблокирован телеграмом'),
                    sa.Column('date_reg', sa.DateTime(), nullable=False),
                    sa.Column('date_ban', sa.DateTime(), nullable=True),
                    sa.Column('active', sa.Boolean(), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    comment='Аккаунты клиента-парсера'
                    )


def downgrade() -> None:
    op.drop_table('client_accounts')
