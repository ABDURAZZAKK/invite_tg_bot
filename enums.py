import enum


class URoles(enum.Enum):
    """ `User` roles `value = {'id':id, 'name':name}`"""
    ADMIN = {'id': 10, 'name': 'admin'}
    PENDING = {'id': 5, 'name': 'pending'}

class InviteSessionResults(enum.Enum):
    CLOSED_MANUALLY = 1
    CLOSED_BY_FLOOD_WARNING = 2

class InviteSendResults(enum.Enum):
    SENT_NORMALLY = 1
    INVITE_RESTRICTED = 2

class CWorkes(enum.Enum):
    """ `Client` workes `value = {'id':id, 'name':name, 'answer':answer}` """
    UNWORKING = {'id': 1, 'name': 'unworking', 'answer': 'Свободен'}
    INVITING = {'id': 2, 'name': 'inviting', 'answer': 'Приглашает клиентов'}
    PARSING = {'id': 3, 'name': 'parsing', 'answer': 'Парсит клиентов'}
    MAILING = {'id': 4, 'name': 'mailing', 'answer': 'Занят рассылкой'}

    @classmethod
    def _missing_(cls, id):
        for work in cls:
            if work.value['id'] == id:
                return work
        return None


class CStatuses(enum.Enum):
    """ `Client` statuses `value = {'id':id, 'name':name, 'answer':answer, 'sticker': stiker}` """
    AUTHORIZED = {'id': 1, 'name': 'authorized', 'answer': 'Авторизован','sticker': '🟢'}
    WAITING_AUTHORIZATION = {'id': 2, 'name': 'waiting_for_authorization', 'answer': 'Требуется авторизация','sticker': '🟡'}
    BANNED = {'id': 3, 'name': 'banned', 'answer': 'Аккаунт забанен','sticker': '🔴'}

    @classmethod
    def _missing_(cls, id):
        for status in cls:
            if status.value['id'] == id:
                return status
        return None






"""Скрипты для миграций"""

    # c_statuses = op.create_table('client_statuses',
    # sa.Column('id', sa.Integer(), nullable=False),
    # sa.Column('name', sa.String(length=50), nullable=False),
    # sa.PrimaryKeyConstraint('id'),
    # sa.UniqueConstraint('name'),
    # comment='Статус аккаунта'
    # )

    # op.bulk_insert(c_statuses, [{'id':status.value['id'],'name':status.value['name']} for status in CStatuses])

    # c_workes = op.create_table('client_workes',
    # sa.Column('id', sa.Integer(), nullable=False),
    # sa.Column('name', sa.String(length=50), nullable=False),
    # sa.PrimaryKeyConstraint('id'),
    # sa.UniqueConstraint('name'),
    # comment='Чем занят аккаунт'
    # )

    # op.bulk_insert(c_workes, [{'id':work.value['id'],'name':work.value['name']} for work in CWorkes])

    # u_roles = op.create_table('user_role',
    # sa.Column('id', sa.Integer(), nullable=False),
    # sa.Column('name', sa.String(length=50), nullable=False),
    # sa.PrimaryKeyConstraint('id'),
    # sa.UniqueConstraint('name'),
    # comment='Роль юзера'
    # )

    # op.bulk_insert(u_roles, [{'id':role.value['id'],'name':role.value['name']} for role in URoles])