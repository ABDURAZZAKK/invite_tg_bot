from aiogram import types
from typing import List
from sqlalchemy.engine import Row
from enums import CWorkes, CStatuses
from keyboards import get_inline_client_markup, get_inline_chats_markup
import client_api
from repositories.getRepo import get_client_repo




async def sendG_CAccounts(message: types.Message, CAccounts: List[Row], **kwargs) -> None:
    for acc in CAccounts:
        work = CWorkes(acc.work_id).value
        status = CStatuses(acc.status_id).value
        status_message = f"{status['sticker']}Статус:  <i>{status['answer']}</i>\n\n"
        if acc.status_id == CStatuses.AUTHORIZED.value['id']:
            if not await client_api.client_is_authorized(acc):
                status_message = f"{CStatuses.WAITING_AUTHORIZATION.value['sticker']}Статус:"\
                                f"  <i>{CStatuses.WAITING_AUTHORIZATION.value['answer']}</i>\n\n"
                
                client_repo = get_client_repo()
                await client_repo.update(acc.id, status_id=CStatuses.WAITING_AUTHORIZATION.value['id'])

        await message.answer(
            f"Аккаунт #{acc.id}\n\n"
            f"api_id:  <i>{acc.api_id}</i>\n\n"
            f"api_hash:  <i>{acc.api_hash}</i>\n\n"
            f"телефон:  <i>{acc.phone}</i>\n\n"
            f"<i><b>{work['answer']}</b></i>\n\n"
            f"{status_message}"
        ,reply_markup=get_inline_client_markup(acc),parse_mode="html")

    if kwargs:
        await message.answer("Выберите действие", **kwargs)



async def sendG_chats(message: types.Message, client, chats, **kwargs) -> None:
    for chat in chats:
        await message.answer(
            f"Группа: <b>{chat.title}</b>\n\n"
            f"Количество участников: <i>{chat.participants_count}</i>\n\n"
            f"Права администратора: <i>{('Есть' if chat.admin_rights or chat.creator else 'Нет')}</i>\n\n"
        ,reply_markup=get_inline_chats_markup(client, chat)
        ,parse_mode="html")

    if kwargs:
        await message.answer("Выберите действие", **kwargs)