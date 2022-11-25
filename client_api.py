from telethon.errors.rpcerrorlist import (PeerFloodError,
                                          UserPrivacyRestrictedError,
                                          UserAlreadyParticipantError)

from typing import List, Any
from aiogram import types
from telethon.sync import TelegramClient
import asyncio
import logging
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.functions.messages import AddChatUserRequest
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty, InputPeerChat


# logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.DEBUG)

from contextvars import ContextVar



clients_context = ContextVar('clients', default=dict())
stop_invite = False


async def get_client(client_data) -> TelegramClient:
    clients = clients_context.get()
    phone = client_data.phone
    if phone in clients:
        if 'client' in clients[phone]:
            return clients[phone]['client']
    else:
        client = await connect(client_data)
        _add_client_to_context(phone, client)

        return client


async def client_is_authorized(client_data) -> bool:
    client = await get_client(client_data)
    b = await client.is_user_authorized()
    return b


def _get_client_context(phone, key) -> Any:
    clients = clients_context.get()
    if phone in clients:
        return clients[phone][key]
    

def _update_client_context(phone, key, value) -> None:
    clients = clients_context.get()
    if phone in clients:
        clients[phone].update({key:value})
    clients_context.set(clients)


def _add_client_to_context(phone, client) -> None:
    clients = clients_context.get()
    if phone in clients:
        clients[phone].update({'client':client})
    else:
        clients[phone] = {'client':client}
    clients_context.set(clients)

def _delete_client_from_context(phone) -> None:
    clients = clients_context.get()
    del clients[phone]
    clients_context.set(clients)



async def send_phone_hash_code(client_data) -> None:
    client = await get_client(client_data)
    sent  = await client.send_code_request(client_data.phone)
    _update_client_context(client_data.phone, 'phone_code_hash', sent.phone_code_hash)
    

async def authorize(client_data, code) -> None:
    phone = client_data.phone
    client = await get_client(client_data)
    phone_code_hash = _get_client_context(phone, 'phone_code_hash')
    await client.sign_in(phone=phone, code=code, phone_code_hash=phone_code_hash)
    
    
async def connect(client_data) -> TelegramClient:
    client = TelegramClient(f'sessions/{client_data.phone}', client_data.api_id, client_data.api_hash)
    await client.connect()
    return client
    

async def get_chats(client_data):
    client = await get_client(client_data)
    dialogs = await client(GetDialogsRequest(
        offset_date=None,
        offset_id=0,
        offset_peer=InputPeerEmpty(),
        limit=200,
        hash=0
    ))
    chats = []
    for chat in dialogs.chats:
        if hasattr(chat, "participants_count") and chat.participants_count and chat.participants_count > 0:
                chats.append(chat)

    return chats


async def get_members(client_data, chat_id) -> List[dict]:
    client = await get_client(client_data)
    chat  = await client.get_entity(chat_id)
    participants = await client.get_participants(chat, aggressive=True)
    members = []
    for prt in participants:
        members.append({
            'id': prt.id,
            'first_name': prt.first_name or None,
            'last_name': prt.last_name or None,
            'username': prt.username or None,
            'chat_id': chat_id,
        })

    return members


async def _send_invite(client: TelegramClient, target_chat, member):
    target_chat_entity = await client.get_entity(target_chat)
    member_entity = await client.get_entity(member.id)
    try:
        try:
            await client(InviteToChannelRequest(target_chat_entity, [member_entity]))
        except:
            await client(AddChatUserRequest(target_chat, member_entity,fwd_limit=100))
    except UserAlreadyParticipantError: 
        pass
    except UserPrivacyRestrictedError:
        pass

async def inviting(message: types.Message, active_accs, target_chat, members):
    clients = cicle([await get_client(acc) for acc in active_accs])
    mem_count = len(members)
    curr_count = 0
    if clients:
        for member in members:
            if stop_invite:
                break
            client = next(clients)
            await _send_invite(client, target_chat, member)
            curr_count+=1
            await message.edit_text(f'Отправленно {curr_count}/{mem_count} инвайтов')
            await asyncio.sleep(3000/len(active_accs))


async def disconnect_all() -> None:
    clients = clients_context.get()
    for cl in clients:
        await clients[cl]['client'].disconnect()


def cicle(l: List):
    while True:
        for i in l:
            yield i
    