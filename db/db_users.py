"""Регистрация юзеров"""
from models.model_users import ROLES, ClientAccount, User

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


def get_all_client_accounts():
    """Все клиентские аккаунты"""
    session = Session()
    values_tuple = session.query(ClientAccount).all()  # TODO ограничить в количестве
    session.close()
    return values_tuple


def get_client_account(id_account: int) -> ClientAccount:
    """Конкретный аккаунт"""
    session = Session()
    value = session.query(ClientAccount).get(id_account)
    session.close()
    return value


def add_new_client_account(api_id: str, api_hash: str, phone: str) -> bool:
    """Добавление нового клиентского аккаунта"""
    session = Session()

    client_account = ClientAccount(
        api_id=api_id,
        api_hash=api_hash,
        phone=phone,
    )

    session.add(client_account)
    session.commit()
    session.close()
    return True


def update_client_account_auth(id_account: int, authorized: int) -> bool:
    session = Session()
    account_item = session.query(ClientAccount).get(id_account)
    if account_item:
        account_item.authorized = authorized
        session.add(account_item)
        session.commit()
    session.close()
    return True


def update_client_account_phone_code_hash(id_account: int, phone_code_hash: str) -> bool:
    session = Session()
    account_item = session.query(ClientAccount).get(id_account)
    if account_item:
        account_item.phone_code_hash = phone_code_hash
        session.add(account_item)
        session.commit()
    session.close()
    return True
