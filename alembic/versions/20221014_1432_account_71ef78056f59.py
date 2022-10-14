"""account

Revision ID: 71ef78056f59
Revises: acefce6c09f3
Create Date: 2022-10-14 14:32:43.254442

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '71ef78056f59'
down_revision = 'acefce6c09f3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('n_account_funcs',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=50), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name'),
                    comment='Функция аккаунта'
                    )

    op.execute('INSERT INTO n_account_funcs VALUES (1, "Инвайтинг")')
    op.execute('INSERT INTO n_account_funcs VALUES (2, "Парсинг")')
    op.execute('INSERT INTO n_account_funcs VALUES (3, "Рассылка")')

    op.add_column('client_accounts', sa.Column('id_account_func', sa.Integer(), nullable=False))
    op.execute('UPDATE client_accounts SET id_account_func=1')
    op.create_foreign_key('client_accounts_ibfk_1', 'client_accounts', 'n_account_funcs', ['id_account_func'], ['id'])


def downgrade() -> None:
    op.drop_constraint('client_accounts_ibfk_1', 'client_accounts', type_='foreignkey')
    op.drop_column('client_accounts', 'id_account_func')
    op.drop_table('n_account_funcs')
