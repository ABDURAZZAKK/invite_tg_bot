"""Клиент (парсер, инвайтер)"""
import datetime

from models.model_client import (ClientAccount, InviteSend, InviteSession,
                                 Member)

from db.connection import Session

from . import connection_raw as db_conn


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


def get_first_client_account() -> ClientAccount:
    """Первый рабочий аккаунт"""
    session = Session()
    value = session.query(ClientAccount).filter(ClientAccount.authorized == 1, ClientAccount.active == 1).first()
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


def add_new_members(members_lst):
    """Сохранение новых участников из группы"""
    session = Session()
    kol_new = 0

    for member_item in members_lst:
        member = session.query(Member).get(member_item.id)
        if not member:
            session.add(member_item)
            kol_new += 1

    session.commit()
    session.close()
    return kol_new


def get_active_invite_session() -> InviteSession:
    session = Session()
    value = session.query(InviteSession).filter(InviteSession.result == None).first()
    session.close()
    return value


def start_invite_session(id_group_destination: int) -> bool:
    """Старт новой сессии отправки"""
    session = Session()

    invite_session_item = session.query(InviteSession).filter(InviteSession.result == None).first()
    if not invite_session_item:
        invite_session_item = InviteSession(
            id_group_destination=id_group_destination,
        )

    session.add(invite_session_item)
    session.commit()
    session.close()
    return True


def stop_invite_session(result: int) -> bool:
    session = Session()
    invite_session_item = session.query(InviteSession).filter(InviteSession.result == None).first()
    if invite_session_item:
        invite_session_item.datetime_end = datetime.datetime.now()
        invite_session_item.result = result
        session.add(invite_session_item)
        session.commit()
    session.close()
    return True


def get_send_kol() -> int:
    """Количество отправленных инвайтов за сутки"""
    session = Session()
    value = session.query(InviteSend).filter(InviteSend.datetime_send >=
                                             datetime.datetime.now() - datetime.timedelta(days=1)).all()
    session.close()
    return len(value)


def get_random_member_to_invite(id_group_destination: int):
    # id_group_destination - указываем группу, чтобы выбрать случайного юзера, которого мы туда ещё не приглашали
    connection = db_conn.open_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 
            members.id
            FROM members 
            LEFT JOIN invite_sends ON (invite_sends.id_member=members.id)
            LEFT JOIN invite_sessions ON (invite_sessions.id=invite_sends.id_invite_session)
            WHERE (invite_sessions.id_group_destination IS NULL OR invite_sessions.id_group_destination!=%s)
            ORDER BY RAND() LIMIT 1
        """, (id_group_destination,))
        value = cursor.fetchone()
    finally:
        db_conn.close_connection(connection)
    if value:
        return value[0]
    return None


def create_invite_send(id_invite_session: int, id_member: int, result: int) -> bool:
    session = Session()
    invite_send_item = InviteSend(
        id_invite_session=id_invite_session,
        id_member=id_member,
        result=result,
    )
    session.add(invite_send_item)
    session.commit()
    session.close()
    return True


def mark_member_invite_restricted(id_member: int) -> bool:
    session = Session()
    member_item = session.query(Member).get(id_member)
    if member_item:
        member_item.invite_restricted = 1
        session.add(member_item)
        session.commit()
    session.close()
    return True
