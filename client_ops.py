"""Операции с Telethon"""
from asyncio import new_event_loop, set_event_loop

from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty

import db
from models.model_users import Member


def check_account_availability() -> bool:
    client_accounts_tuple = db.db_users.get_all_client_accounts()
    if client_accounts_tuple:
        for client_account_item in client_accounts_tuple:
            # TODO обработка нескольких аккаунтов (с паузой)
            set_event_loop(new_event_loop())
            client = TelegramClient(client_account_item.phone, client_account_item.api_id, client_account_item.api_hash)
            client.connect()
            if not client.is_user_authorized():
                db.db_users.update_client_account_auth(client_account_item.id, 0)
            client.disconnect()

    return True


def send_auth_code(id_account: int) -> bool:
    client_account_item = db.db_users.get_client_account(id_account)
    if client_account_item.authorized == 1:
        return False

    set_event_loop(new_event_loop())
    client = TelegramClient(client_account_item.phone, client_account_item.api_id, client_account_item.api_hash)
    client.connect()
    if not client.is_user_authorized():
        sent_code_item = client.send_code_request(client_account_item.phone)
        if sent_code_item:
            db.db_users.update_client_account_phone_code_hash(id_account, sent_code_item.phone_code_hash)
    client.disconnect()
    return True


def authorize(id_account: int, code: str) -> bool:
    client_account_item = db.db_users.get_client_account(id_account)
    if client_account_item.authorized == 1:
        return False

    set_event_loop(new_event_loop())
    client = TelegramClient(client_account_item.phone, client_account_item.api_id, client_account_item.api_hash)
    client.connect()
    if not client.is_user_authorized():
        client.sign_in(client_account_item.phone, code, phone_code_hash=client_account_item.phone_code_hash)
    client.disconnect()
    db.db_users.update_client_account_auth(id_account, 1)
    return True


def get_acc_groups():
    # TODO это не моя функция, нужен рефакторинг
    common_groups_lst = []
    admin_groups_lst = []
    is_has_groups = False

    client_account_item = db.db_users.get_first_client_account()
    if not client_account_item:
        return False

    set_event_loop(new_event_loop())
    client = TelegramClient(client_account_item.phone, client_account_item.api_id, client_account_item.api_hash)
    client.connect()

    chats = []
    groups = []

    result = client(GetDialogsRequest(
        offset_date=None,
        offset_id=0,
        offset_peer=InputPeerEmpty(),
        limit=200,
        hash=0
    ))
    chats.extend(result.chats)

    for chat in chats:
        try:
            if (hasattr(chat, "participants_count") and chat.participants_count and chat.participants_count > 0) or (hasattr(chat, "megagroup") and chat.megagroup):
                groups.append(chat)
        except Exception as ex:
            print(ex)
            continue

    if groups:
        is_has_groups = True

    for grp in groups:
        if grp.admin_rights:
            admin_groups_lst.append((grp.id, grp.title))
        else:
            common_groups_lst.append((grp.id, grp.title))

    client.disconnect()
    return (common_groups_lst, admin_groups_lst, is_has_groups)


def get_members_in_group(id_group: int):
    # TODO нужен рефакторинг + здесь в начале повтор кода
    members_lst = []
    client_account_item = db.db_users.get_first_client_account()
    if not client_account_item:
        return False

    set_event_loop(new_event_loop())
    client = TelegramClient(client_account_item.phone, client_account_item.api_id, client_account_item.api_hash)
    client.connect()

    chats = []
    groups = []

    result = client(GetDialogsRequest(
        offset_date=None,
        offset_id=0,
        offset_peer=InputPeerEmpty(),
        limit=200,
        hash=0
    ))
    chats.extend(result.chats)

    for chat in chats:
        try:
            if (hasattr(chat, "participants_count") and chat.participants_count and chat.participants_count > 0) or (hasattr(chat, "megagroup") and chat.megagroup):
                groups.append(chat)
        except Exception as ex:
            print(ex)
            continue

    for grp in groups:
        if grp.id == id_group:
            all_participants = []
            all_participants = client.get_participants(grp, aggressive=True)
            for user_item in all_participants:
                if user_item.last_name and user_item.first_name:
                    fio = f'{user_item.last_name} {user_item.first_name}'
                elif user_item.last_name or user_item.first_name:
                    fio = user_item.first_name or user_item.last_name
                else:
                    fio = 'unknown'

                new_member = Member(
                    id=user_item.id,
                    fio=fio,
                    nick=user_item.username,
                )
                members_lst.append(new_member)

    client.disconnect()
    return members_lst
