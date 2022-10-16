"""id account to sends

Revision ID: 1c42a0dcd34e
Revises: 71ef78056f59
Create Date: 2022-10-16 11:47:38.671164

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '1c42a0dcd34e'
down_revision = '71ef78056f59'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('invite_sends', sa.Column('id_account', sa.BigInteger(), nullable=False))
    op.execute('UPDATE invite_sends SET id_account = (SELECT id FROM client_accounts WHERE active=1 LIMIT 1)')
    op.create_foreign_key('invite_sends_ibfk_4', 'invite_sends', 'client_accounts', ['id_account'], ['id'])


def downgrade() -> None:
    op.drop_constraint('invite_sends_ibfk_4', 'invite_sends', type_='foreignkey')
    op.drop_column('invite_sends', 'id_account')
