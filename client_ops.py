"""Операции с Telethon"""
import datetime
import logging
from asyncio import new_event_loop, set_event_loop

from telethon.errors.rpcerrorlist import (PeerFloodError,
                                          UserPrivacyRestrictedError)
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty

import db
from models.model_client import (INVITE_SEND_RESULTS, INVITE_SESSION_RESULTS,
                                 ClientAccount, Member)

LOGGER = logging.getLogger('applog')


def check_account_availability(id_account: int) -> bool:
    client_account_item = db.db_client.get_client_account(id_account)
    try:
        set_event_loop(new_event_loop())
        client = TelegramClient(client_account_item.phone, client_account_item.api_id, client_account_item.api_hash)
        client.connect()
        if not client.is_user_authorized():
            db.db_client.update_client_account_auth(client_account_item.id, 0)
        client.disconnect()

        return True
    except Exception as ex:
        LOGGER.error(ex)
        db.db_client.update_client_account_active(client_account_item.id, 0)
        return False


def send_auth_code(id_account: int) -> bool:
    client_account_item = db.db_client.get_client_account(id_account)
    if client_account_item.authorized == 1:
        return False

    set_event_loop(new_event_loop())
    client = TelegramClient(client_account_item.phone, client_account_item.api_id, client_account_item.api_hash)
    client.connect()
    if not client.is_user_authorized():
        sent_code_item = client.send_code_request(client_account_item.phone)
        if sent_code_item:
            db.db_client.update_client_account_phone_code_hash(id_account, sent_code_item.phone_code_hash)
    client.disconnect()
    return True


def authorize(id_account: int, code: str) -> bool:
    client_account_item = db.db_client.get_client_account(id_account)
    if client_account_item.authorized == 1:
        return False

    set_event_loop(new_event_loop())
    client = TelegramClient(client_account_item.phone, client_account_item.api_id, client_account_item.api_hash)
    client.connect()
    if not client.is_user_authorized():
        client.sign_in(client_account_item.phone, code, phone_code_hash=client_account_item.phone_code_hash)
    client.disconnect()
    db.db_client.update_client_account_auth(id_account, 1)
    return True


def get_acc_groups(account_item: ClientAccount):
    # TODO это не моя функция, нужен рефакторинг
    common_groups_lst = []
    admin_groups_lst = []
    is_has_groups = False

    set_event_loop(new_event_loop())
    client = TelegramClient(account_item.phone, account_item.api_id, account_item.api_hash)
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
            LOGGER.error(ex)
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


def get_members_in_group(id_group: int, id_account: int):
    # TODO нужен рефакторинг + здесь в начале повтор кода
    members_lst = []
    client_account_item = db.db_client.get_client_account(id_account)
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
            LOGGER.error(ex)
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


def inviting():
    max_invites_per_day = 29

    active_session_item = db.db_client.get_active_invite_session()
    if not active_session_item:
        return

    norm_accounts_tuple = db.db_client.get_norm_client_accounts()
    cur_account = None
    for account_item in norm_accounts_tuple:
        if db.db_client.get_send_kol(account_item) >= max_invites_per_day:
            LOGGER.warning(f'max invites reached on acc #{account_item.id}')
            continue

        if is_account_warm(account_item) and db.db_client.get_send_kol(account_item) >= 4:
            LOGGER.warning(f'account warm and sends >= 4 on acc #{account_item.id}')
            continue

        last_invite_send_item = db.db_client.get_last_invite_send(account_item)
        if last_invite_send_item.datetime_send >= datetime.datetime.now() - datetime.timedelta(minutes=4):
            LOGGER.warning(f'skip inviting in this minute due to 4 mins pause on acc #{account_item.id}')
            continue

        continuous_send_6_days_tuple = db.db_client.get_continuous_send_6_days(account_item)
        if len(continuous_send_6_days_tuple) >= 6:
            LOGGER.warning(f'skip inviting in this minute due to 6 days use on acc #{account_item.id}')
            continue

        cur_account = account_item
        break  # если не сработало ни одно ограничение, то выходим из цикла for после первого же прогона

    if cur_account:
        send_invite(cur_account)
    else:
        LOGGER.warning('Not found account_item without restricts')


def send_invite(client_account_item: ClientAccount):
    active_session_item = db.db_client.get_active_invite_session()
    if not active_session_item:
        return

    set_event_loop(new_event_loop())
    client = TelegramClient(client_account_item.phone, client_account_item.api_id, client_account_item.api_hash)
    client.connect()
    if not client.is_user_authorized():
        db.db_client.update_client_account_auth(client_account_item.id, 0)
        client.disconnect()
        return

    id_member = db.db_client.get_random_member_to_invite(active_session_item.id_group_destination)
    if not id_member:
        db.db_client.stop_invite_session(INVITE_SESSION_RESULTS['closed_manually'])
        return

    member_entity = client.get_entity(id_member)
    target_group_entity = client.get_entity(active_session_item.id_group_destination)

    try:
        client(InviteToChannelRequest(target_group_entity, [member_entity]))
        db.db_client.create_invite_send(active_session_item.id, client_account_item.id,
                                        id_member, INVITE_SEND_RESULTS['sent_normally'])
    except PeerFloodError:
        LOGGER.warning(f"Getting Flood Error from TG on acc #{client_account_item.id}, set him inactive")
        db.db_client.update_client_account_active(client_account_item.id, 0)
        # db.db_client.stop_invite_session(INVITE_SESSION_RESULTS['closed_by_flood_warning'])
    except UserPrivacyRestrictedError:
        LOGGER.warning("The user's %s privacy settings is invite_restricted", id_member, exc_info=True)
        db.db_client.create_invite_send(active_session_item.id, client_account_item.id,
                                        id_member, INVITE_SEND_RESULTS['invite_restricted'])
        db.db_client.mark_member_invite_restricted(id_member)
    except Exception as ex:
        LOGGER.error(ex)

    client.disconnect()


def is_account_warm(client_account_item: ClientAccount) -> bool:
    warm_days = 5
    if client_account_item.date_reg >= datetime.datetime.now() - datetime.timedelta(days=warm_days):
        return True
    return False
