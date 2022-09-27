"""initial

Revision ID: 6a7d996a50f8
Revises: 
Create Date: 2022-09-27 20:01:49.832181

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '6a7d996a50f8'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('n_role',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('name', sa.String(length=50), nullable=False),
                    sa.PrimaryKeyConstraint('id'),
                    sa.UniqueConstraint('name'),
                    comment='Роли юзеров'
                    )

    op.execute('INSERT INTO n_role VALUES (5, "Ожидание регистрации")')
    op.execute('INSERT INTO n_role VALUES (10, "Администратор")')

    op.create_table('prefs',
                    sa.Column('name', sa.String(length=50), nullable=False),
                    sa.Column('intval', sa.BigInteger(), nullable=True),
                    sa.Column('textval', sa.Text(), nullable=True),
                    sa.Column('dateval', sa.Date(), nullable=True),
                    sa.Column('datetimeval', sa.DateTime(), nullable=True),
                    sa.PrimaryKeyConstraint('name'),
                    comment='Константы и постоянные переменные'
                    )

    op.create_table('resources',
                    sa.Column('name', sa.String(length=50), nullable=False),
                    sa.Column('path', sa.String(length=255), nullable=False, comment='Путь к файлу на сервере'),
                    sa.Column('file_id', sa.String(length=255), nullable=True, comment='TG ID'),
                    sa.Column('date_update', sa.DateTime(), nullable=False),
                    sa.PrimaryKeyConstraint('name'),
                    comment='Файлы ресурсов и их ID'
                    )

    op.create_table('service_chats',
                    sa.Column('name', sa.String(length=50), nullable=False),
                    sa.Column('chat_id', sa.String(length=255), nullable=True, comment='id чата в TG'),
                    sa.Column('hyperlink', sa.String(length=255), nullable=True, comment='ссылка на чат'),
                    sa.PrimaryKeyConstraint('name'),
                    comment='ID сервисных групп и каналов'
                    )

    op.create_table('states',
                    sa.Column('id_user', sa.BigInteger(), nullable=False),
                    sa.Column('state', sa.String(length=255), nullable=False, comment='Номер стадии'),
                    sa.PrimaryKeyConstraint('id_user'),
                    comment='Стадии меню у юзеров'
                    )

    op.create_table('tempvals',
                    sa.Column('id_user', sa.BigInteger(), nullable=False),
                    sa.Column('state', sa.String(length=100), nullable=False,
                              comment='К какому шагу меню относится данная переменная'),
                    sa.Column('intval', sa.BigInteger(), nullable=True),
                    sa.Column('textval', sa.Text(), nullable=True),
                    sa.Column('protect', sa.Boolean(), nullable=False,
                              comment='Не будет удалено методом clear_user_tempvals()'),
                    sa.Column('date_create', sa.DateTime(), nullable=False),
                    sa.PrimaryKeyConstraint('id_user', 'state'),
                    comment='Временные переменные'
                    )

    op.create_table('users',
                    sa.Column('id', sa.BigInteger(), nullable=False),
                    sa.Column('fio', sa.String(length=300), nullable=False),
                    sa.Column('nick', sa.String(length=100), nullable=True),
                    sa.Column('id_role', sa.Integer(), nullable=False),
                    sa.Column('date_reg', sa.DateTime(), nullable=False),
                    sa.Column('date_ban', sa.DateTime(), nullable=True),
                    sa.Column('reg', sa.Boolean(), nullable=False),
                    sa.Column('active', sa.Boolean(), nullable=False),
                    sa.ForeignKeyConstraint(['id_role'], ['n_role.id'], ),
                    sa.PrimaryKeyConstraint('id'),
                    comment='Юзеры'
                    )


def downgrade() -> None:
    op.drop_table('users')
    op.drop_table('tempvals')
    op.drop_table('states')
    op.drop_table('service_chats')
    op.drop_table('resources')
    op.drop_table('prefs')
    op.drop_table('n_role')
