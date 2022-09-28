"""Операции с Telethon"""
from asyncio import new_event_loop, set_event_loop

from telethon.sync import TelegramClient

import db


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
