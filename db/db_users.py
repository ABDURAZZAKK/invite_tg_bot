"""Регистрация юзеров"""
from models.model_users import ROLES, User

from db.connection import Session


def get_user(id_user: int) -> User:
    """Объект юзера в БД"""
    session = Session()
    user = session.query(User).get(id_user)
    session.close()
    return user


def add_new_user(id_user: int, fio: str, nick: str) -> bool:
    """Добавление нового юзера"""
    session = Session()

    user = session.query(User).get(id_user)
    if user:
        user.id_role = ROLES['pending']
        user.fio = fio
        user.nick = nick
        user.reg = 0
        user.active = 1
    else:
        user = User(
            id=id_user,
            id_role=ROLES['pending'],
            fio=fio,
            nick=nick,
        )

    session.add(user)
    session.commit()
    session.close()
    return True
