"""inviter

Revision ID: acefce6c09f3
Revises: 1c1bc12cace3
Create Date: 2022-10-01 13:34:59.876668

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'acefce6c09f3'
down_revision = '1c1bc12cace3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('n_invite_send_results',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=50), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name'),
                    comment='Результат отправки инвайта юзеру'
                    )

    op.execute('INSERT INTO n_invite_send_results VALUES (1, "Отправлено нормально")')
    op.execute('INSERT INTO n_invite_send_results VALUES (2, "У юзера запрет на приглашения")')

    op.create_table('n_invite_session_results',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=50), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name'),
                    comment='Причины остановки рассылки'
                    )

    op.execute('INSERT INTO n_invite_session_results VALUES (1, "Завершено вручную")')
    op.execute('INSERT INTO n_invite_session_results VALUES (2, "Предупреждение от ТГ о флуде")')

    op.create_table('invite_sessions',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('id_group_destination', sa.BigInteger(), nullable=False),
                    sa.Column('datetime_start', sa.DateTime(), nullable=False),
                    sa.Column('datetime_end', sa.DateTime(), nullable=True),
                    sa.Column('result', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['result'], ['n_invite_session_results.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    comment='Текущая рассылка, от старта до остановки'
                    )

    op.create_table('invite_sends',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('id_invite_session', sa.BigInteger(), nullable=False),
                    sa.Column('id_member', sa.BigInteger(), nullable=False),
                    sa.Column('datetime_send', sa.DateTime(), nullable=False),
                    sa.Column('result', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['id_invite_session'], ['invite_sessions.id'], ),
                    sa.ForeignKeyConstraint(['id_member'], ['members.id'], ),
                    sa.ForeignKeyConstraint(['result'], ['n_invite_send_results.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    comment='Отправки конкретным юзерам'
                    )
    op.add_column('members', sa.Column('invite_restricted', sa.Boolean(), nullable=True,
                  comment='Заблокирован ли у юзера приём инвайтов (1 - да)'))


def downgrade() -> None:
    op.drop_column('members', 'invite_restricted')
    op.drop_table('invite_sends')
    op.drop_table('invite_sessions')
    op.drop_table('n_invite_session_results')
    op.drop_table('n_invite_send_results')
