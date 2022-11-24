from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from typing import Tuple
from enums import CStatuses


def get_admin_markup(*rows: Tuple[str]) -> ReplyKeyboardMarkup:
    """ Принимает кортежи вида `('button1', 'b2', 'b3', ...), (b1,b2,b3)` где каждый котеж новая строка в клаве"""
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for row in rows:
        markup.row(*map(KeyboardButton,row))
    return markup


def get_inline_client_markup(client) -> InlineKeyboardMarkup:
    keyboard = []
    if client.status_id == CStatuses.WAITING_AUTHORIZATION.value['id']:
        keyboard.append([InlineKeyboardButton(text='Авторизоваться', callback_data=f'client:authorization:{client.id}')])
    keyboard.append([InlineKeyboardButton(text='Удалить', callback_data=f'client:delete:{client.id}')])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup


def get_inline_chats_markup(client,chat) -> InlineKeyboardMarkup:
    keyboard = []
    if chat.admin_rights or chat.creator:
        keyboard.append([InlineKeyboardButton(text='Инвайтить в эту группу', callback_data=f'inviting:{chat.id}')])
    keyboard.append([InlineKeyboardButton(text='Парсить участников', callback_data=f'parsing:{client.id}:{chat.id}')])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup


def get_inline_invite_stop_markup() -> InlineKeyboardMarkup:
    keyboard = []
    keyboard.append([InlineKeyboardButton(text='Остановить', callback_data=f'stop_inviting:')])
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    return markup