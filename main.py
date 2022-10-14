#!venv/bin/python
"""Main module"""

import datetime
import logging
import logging.handlers as loghandlers
import os
import random
import sys
import threading
import time

import telebot
from telebot import types, util

import client_ops
import config
import db
import states
from models.model_client import (INVITE_SESSION_RESULTS, AccountFuncClassifier,
                                 ClientAccount)
from models.model_users import ROLES
from states import States as st

BOT = telebot.TeleBot(config.TOKEN_BOT)


if not os.path.exists('logs'):
    os.makedirs('logs')
LOGGER = logging.getLogger('applog')
LOGGER.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s  %(filename)s  %(funcName)s  %(lineno)d  %(name)s  %(levelname)s: %(message)s')
log_handler = loghandlers.RotatingFileHandler(
    './logs/botlog.log',
    maxBytes=1000000,
    encoding='utf-8',
    backupCount=50
)
log_handler.setLevel(logging.INFO)
log_handler.setFormatter(formatter)
LOGGER.addHandler(log_handler)
telebot.logger.setLevel(logging.INFO)
telebot.logger.addHandler(LOGGER)


@BOT.message_handler(func=lambda message: message.text == 'Отмена')
def cancel_to_mainmenu(message):
    """При команде Отмена из любого места возвращает в главное меню"""
    cmd_start(message)


@BOT.chat_member_handler()
def chat_member_greetings(chat_member_updated: types.ChatMemberUpdated):
    """Слежение за группами/каналами, где бот админом"""
    pass


@BOT.callback_query_handler(func=lambda call: True)
def inline_buttons_router(call):
    """Роутер для инлайновых кнопок"""
    if call.message:
        key = call.data.split(';')[0]
        is_del_inline_keyb = True

        if key == 'menu_reg_start':
            menu_reg_start(call.message)
        elif key == 'menu_admin_accounts_create':
            menu_admin_accounts_create(call.message)
        elif key == 'menu_admin_accounts_authorize':
            menu_admin_accounts_authorize(call.message, call.data)
        elif key == 'menu_admin_accounts_changefunc':
            menu_admin_accounts_changefunc(call.message, call.data)
        elif key == 'menu_admin_parsegroup_select':
            menu_admin_parsegroup_select(call.message, call.data)
        elif key == 'menu_admin_invite_group_select':
            menu_admin_invite_group_select(call.message, call.data)
        elif key == 'menu_admin_invite_stop':
            menu_admin_invite_stop(call.message)

        if is_del_inline_keyb:
            BOT.edit_message_reply_markup(chat_id=call.message.chat.id,
                                          message_id=call.message.id, reply_markup=types.InlineKeyboardMarkup())


@BOT.message_handler(commands=['start'])
def cmd_start(message):
    """Старт диалога с ботом"""
    if message.chat.id < 0:  # если вызвали из чата
        return
    mainmenu(message)


def menu_reg_about(message):
    """Инфа перед регистрацией"""
    if message.from_user.last_name and message.from_user.first_name:
        fio = f'{message.from_user.last_name} {message.from_user.first_name}'
    elif message.from_user.last_name or message.from_user.first_name:
        fio = message.from_user.first_name or message.from_user.last_name
    else:
        fio = 'unknown'
    db.db_tempvals.set_tmpval(message.chat.id, st.S_REG_FIO_GET.name, textval=fio)

    keyboard_inline = types.InlineKeyboardMarkup()
    keyboard_list = []
    keyboard_list.append(types.InlineKeyboardButton(text='Зарегистрироваться', callback_data="menu_reg_start;1"))
    keyboard_inline.add(*keyboard_list, row_width=1)

    mes = 'Нажмите кнопку для отправки запроса на регистрацию'
    BOT.send_message(message.chat.id, mes, reply_markup=keyboard_inline)


def menu_reg_start(message):
    """Начало регистрации"""
    user = db.db_users.get_user(message.chat.id)
    if user:
        BOT.send_message(message.chat.id, 'Вы уже зарегистрированы')
        mainmenu(message)
        return
    menu_reg_save(message)


def menu_reg_save(message):
    """Сохранение регистрации"""
    id_user = message.chat.id
    fio = db.db_tempvals.get_tmpval(id_user, st.S_REG_FIO_GET.name).textval
    nick = message.chat.username

    if db.db_users.add_new_user(id_user, fio, nick):
        BOT.send_message(message.chat.id, 'Регистрация пройдена')
        states.set_state(message.chat.id, st.S_REG_PENDING.value)
        menu_reg_pending(message)
    else:
        BOT.send_message(message.chat.id, 'Ошибка регистрации')


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_REG_PENDING.value)
def menu_reg_pending(message):
    """Ожидание подтверждения"""
    user = db.db_users.get_user(message.chat.id)
    if user and user.id_role != ROLES['pending']:
        cmd_start(message)
    else:
        keyb_items = ['Обновить']
        keyboard = make_keyboard(items=keyb_items, is_with_cancel=False)
        BOT.send_message(message.chat.id, 'Ожидайте подтверждения', reply_markup=keyboard)


def mainmenu(message):
    """Главное меню"""
    user = db.db_users.get_user(message.chat.id)

    if not user or user.active == 0:
        menu_reg_about(message)
        return

    if user and user.reg == 0:
        menu_reg_pending(message)
        return

    db.db_tempvals.clear_user_tempvals(message.chat.id)
    states.set_state(message.chat.id, st.S_MAINMENU.value)

    keyb_items = []
    row_width = 2

    if user.id_role == ROLES['admin']:
        keyb_items.append('Группы')
        keyb_items.append('Парсинг участников')
        keyb_items.append('Рассылка инвайтов')
        keyb_items.append('Аккаунты')

    keyboard = make_keyboard(items=keyb_items, row_width=row_width, is_with_cancel=False)
    mes = 'Вы в главном меню'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_MAINMENU.value)
def mainmenu_choice(message):
    """Обработка нажатия в главном меню"""
    choice = message.text
    user = db.db_users.get_user(message.chat.id)

    if user.id_role == ROLES['admin']:
        if choice == 'Группы':
            menu_admin_accgroups_show(message)
        elif choice == 'Парсинг участников':
            menu_admin_parsegroup(message)
        elif choice == 'Рассылка инвайтов':
            menu_admin_invites(message)
        elif choice == 'Аккаунты':
            menu_admin_accounts_show(message)


def menu_admin_accgroups_show(message):
    if not db.db_client.get_first_client_account():
        BOT.send_message(message.chat.id, 'Нет рабочего аккаунта')
        return

    BOT.send_message(message.chat.id, 'Получение списка групп...')
    acc_groups_tuple = client_ops.get_acc_groups()
    if not acc_groups_tuple:
        BOT.send_message(message.chat.id, 'Ошибка загрузки групп')
        return

    common_groups_lst, admin_groups_lst, is_has_groups = acc_groups_tuple
    if not is_has_groups:
        mes = 'Аккаунт не состоит ни в одной группе\nНужно от имени аккаунта вручную вступить в группы, которые будем парсить\n'
        BOT.send_message(message.chat.id, mes)
        return

    mes = ''

    mes += '🔸<b>Группы, в которых состоит аккаунт:</b>\n'
    if common_groups_lst:
        for common_group_item in common_groups_lst:
            _, title_group = common_group_item
            mes += f'{title_group}\n'
    else:
        mes += '-'

    mes += '\n'

    mes += '🔸<b>Собственные группы (где аккаунт имеет роль админа):</b>\n'
    if admin_groups_lst:
        for admin_group_item in admin_groups_lst:
            _, title_group = admin_group_item
            mes += f'{title_group}\n'
    else:
        mes += '-'

    BOT.send_message(message.chat.id, mes, parse_mode='html')


def menu_admin_parsegroup(message):
    if not db.db_client.get_first_client_account():
        BOT.send_message(message.chat.id, 'Нет рабочего аккаунта')
        return

    BOT.send_message(message.chat.id, 'Получение списка групп...')
    acc_groups_tuple = client_ops.get_acc_groups()
    if not acc_groups_tuple:
        BOT.send_message(message.chat.id, 'Ошибка загрузки групп')
        return

    common_groups_lst, _, is_has_groups = acc_groups_tuple
    if not is_has_groups:
        mes = 'Аккаунт не состоит ни в одной группе\nНужно от имени аккаунта вручную вступить в группы, которые будем парсить\n'
        BOT.send_message(message.chat.id, mes)
        return

    keyboard_inline = types.InlineKeyboardMarkup()
    keyboard_list = []
    for common_group_item in common_groups_lst:
        id_group, title_group = common_group_item
        keyboard_list.append(types.InlineKeyboardButton(
            text=title_group, callback_data=f"menu_admin_parsegroup_select;{id_group}"))
    keyboard_inline.add(*keyboard_list, row_width=1)

    mes = 'Выберите группу, из которой нужно сохранить список участников'
    BOT.send_message(message.chat.id, mes, reply_markup=keyboard_inline)


def menu_admin_parsegroup_select(message, data):
    BOT.send_message(message.chat.id, 'Сохранение участников...')
    params = data.split(';')
    id_group = int(params[1])
    menu_admin_parsegroup_savemembers(message, id_group)


def menu_admin_parsegroup_savemembers(message, id_group):
    members_lst = client_ops.get_members_in_group(id_group)
    if not members_lst:
        BOT.send_message(message.chat.id, 'Ошибка получения списка участников')
        return

    kol_new = db.db_client.add_new_members(members_lst)
    if kol_new is None:
        BOT.send_message(message.chat.id, 'Ошибка записи списка участников в базу')
        return

    mes = 'Успешно сохранено\n\n'
    mes += f'В группе участников: {len(members_lst)}\n'
    mes += f'Из них сохранено новых в базу: {kol_new}'
    BOT.send_message(message.chat.id, mes)
    mainmenu(message)


def menu_admin_invites(message):
    if not db.db_client.get_first_client_account():
        BOT.send_message(message.chat.id, 'Нет рабочего аккаунта')
        return

    keyboard_inline = types.InlineKeyboardMarkup()
    keyboard_list = []
    active_session_item = db.db_client.get_active_invite_session()
    if active_session_item:
        keyboard_list.append(types.InlineKeyboardButton(text='Остановить', callback_data="menu_admin_invite_stop;1"))
        keyboard_inline.add(*keyboard_list, row_width=1)
        mes = 'Идёт отправка инвайтов'
    else:
        BOT.send_message(message.chat.id, 'Получение списка групп...')
        acc_groups_tuple = client_ops.get_acc_groups()
        if not acc_groups_tuple:
            BOT.send_message(message.chat.id, 'Ошибка загрузки групп')
            return

        _, admin_groups_lst, is_has_groups = acc_groups_tuple
        if not is_has_groups:
            mes = 'Аккаунт не состоит ни в одной группе'
            BOT.send_message(message.chat.id, mes)
            return

        if not admin_groups_lst:
            mes = 'Аккаунт должен быть админом (с правами добавления участников) хотя бы в одной группе, в которую будем приглашать новых участников'
            BOT.send_message(message.chat.id, mes)
            return

        for admin_group_item in admin_groups_lst:
            id_group, title_group = admin_group_item
            keyboard_list.append(types.InlineKeyboardButton(
                text=title_group, callback_data=f"menu_admin_invite_group_select;{id_group}"))
        keyboard_inline.add(*keyboard_list, row_width=1)
        mes = 'Выберите группу, в которую будем приглашать участников'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard_inline)


def menu_admin_invite_group_select(message, data):
    params = data.split(';')
    id_group_destination = int(params[1])
    menu_admin_invite_start(message, id_group_destination)


def menu_admin_invite_start(message, id_group_destination):
    if db.db_client.start_invite_session(id_group_destination):
        BOT.send_message(message.chat.id, 'Рассылка инвайтов начата')
        mainmenu(message)
    else:
        BOT.send_message(message.chat.id, 'Ошибка старта рассылки')


def menu_admin_invite_stop(message):
    if db.db_client.stop_invite_session(INVITE_SESSION_RESULTS['closed_manually']):
        BOT.send_message(message.chat.id, 'Рассылка инвайтов остановлена')
        mainmenu(message)
    else:
        BOT.send_message(message.chat.id, 'Ошибка остановки рассылки')


def menu_admin_accounts_show(message):
    BOT.send_message(message.chat.id, 'Проверка аккаунтов...')
    client_accounts_tuple = db.db_client.get_all_client_accounts()

    if client_accounts_tuple:
        for client_account in client_accounts_tuple:
            client_ops.check_account_availability(client_account.id)

            keyboard_inline = types.InlineKeyboardMarkup()
            keyboard_list = []
            keyboard_list.append(types.InlineKeyboardButton(text='Сменить назначение',
                                 callback_data=f"menu_admin_accounts_changefunc;{client_account.id}"))

            mes = f'<b>Аккаунт #{client_account.id}</b>\n'
            mes += f'api_id: {client_account.api_id}\n'
            mes += f'api_hash: {client_account.api_hash}\n'
            mes += f'телефон: {client_account.phone}\n\n'

            account_func_item = db.db_classifiers.find_classifier_object(
                AccountFuncClassifier, id_object=client_account.id_account_func)
            mes += f'📌<b>Назначение аккаунта:</b> {account_func_item.name}\n'

            if client_account.banned == 1:
                mes += '🔴<b>Статус:</b> заблокирован Телеграмом'
            elif client_account.active == 0:
                mes += '⚫<b>Статус:</b> неактивен'
            elif client_account.authorized == 0:
                mes += '🟡<b>Статус:</b> требуется авторизация'
                keyboard_list.append(types.InlineKeyboardButton(text='Авторизовать',
                                     callback_data=f"menu_admin_accounts_authorize;{client_account.id}"))
            else:
                mes += '🟢<b>Статус:</b> активен'

            if is_account_warm(client_account):
                mes += '\n'
                mes += '🔥<b>Аккаунт на прогреве</b>'

            keyboard_inline.add(*keyboard_list, row_width=1)
            BOT.send_message(message.chat.id, mes, parse_mode='html', reply_markup=keyboard_inline)

        keyboard_inline = types.InlineKeyboardMarkup()
        keyboard_list = []
        keyboard_list.append(types.InlineKeyboardButton(text='Добавить новый',
                             callback_data=f"menu_admin_accounts_create;1"))
        keyboard_inline.add(*keyboard_list, row_width=1)
        mes = 'Новый аккаунт?'
        BOT.send_message(message.chat.id, mes, reply_markup=keyboard_inline)

    else:
        keyboard_inline = types.InlineKeyboardMarkup()
        keyboard_list.append(types.InlineKeyboardButton(text='Создать аккаунт',
                             callback_data="menu_admin_accounts_create;1"))
        keyboard_inline.add(*keyboard_list, row_width=1)
        mes = 'Нет клиентских аккаунтов'
        BOT.send_message(message.chat.id, mes, reply_markup=keyboard_inline)


def menu_admin_accounts_create(message):
    menu_admin_accounts_create_api_id_ask(message)


def menu_admin_accounts_create_api_id_ask(message):
    """Новый клиентский аккаунт - запрос api_id"""
    keyboard = make_keyboard(is_with_cancel=False)
    mes = 'Напишите api_id'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_ADMIN_CREATEACC_API_ID_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_ADMIN_CREATEACC_API_ID_ASK.value)
def menu_admin_accounts_create_api_id_save(message):
    """Новый клиентский аккаунт - сохранение api_id"""
    api_id = message.text
    if len(api_id) > 100:
        BOT.send_message(message.chat.id, 'Слишком длинный api_id')
        return
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_ADMIN_CREATEACC_API_ID_ASK.name, textval=api_id)
    menu_admin_accounts_create_api_hash_ask(message)


def menu_admin_accounts_create_api_hash_ask(message):
    """Новый клиентский аккаунт - запрос api_hash"""
    keyboard = make_keyboard(is_with_cancel=False)
    mes = 'Напишите api_hash'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_ADMIN_CREATEACC_API_HASH_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_ADMIN_CREATEACC_API_HASH_ASK.value)
def menu_admin_accounts_create_api_hash_save(message):
    """Новый клиентский аккаунт - сохранение api_hash"""
    api_hash = message.text
    if len(api_hash) > 100:
        BOT.send_message(message.chat.id, 'Слишком длинный api_hash')
        return
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_ADMIN_CREATEACC_API_HASH_ASK.name, textval=api_hash)
    menu_admin_accounts_create_phone_ask(message)


def menu_admin_accounts_create_phone_ask(message):
    """Новый клиентский аккаунт - запрос телефона"""
    keyboard = make_keyboard()
    mes = 'Напишите номер телефона'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_ADMIN_CREATEACC_API_PHONE_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_ADMIN_CREATEACC_API_PHONE_ASK.value)
def menu_admin_accounts_create_phone_save(message):
    """Новый клиентский аккаунт - сохранение телефона"""
    phone = message.text.replace(' ', '').replace('-', '').replace('(', '').replace(')', '').replace('+', '')
    if len(phone) > 20:
        BOT.send_message(message.chat.id, 'Слишком длинный номер')
        return
    if not str.isdigit(phone):
        BOT.send_message(message.chat.id, 'Неправильно указан номер телефона')
        return

    phone_str_lst = list(phone)
    if phone_str_lst[0] == '8':
        phone_str_lst[0] = '7'
    phone = "".join(phone_str_lst)
    phone = f'+{phone}'

    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_ADMIN_CREATEACC_API_PHONE_ASK.name, textval=phone)
    menu_admin_accounts_create_save(message)


def menu_admin_accounts_create_save(message):
    """Сохранение нового клиентского аккаунта"""
    id_user = message.chat.id
    api_id = db.db_tempvals.get_tmpval(id_user, st.S_MENU_ADMIN_CREATEACC_API_ID_ASK.name).textval
    api_hash = db.db_tempvals.get_tmpval(id_user, st.S_MENU_ADMIN_CREATEACC_API_HASH_ASK.name).textval
    phone = db.db_tempvals.get_tmpval(id_user, st.S_MENU_ADMIN_CREATEACC_API_PHONE_ASK.name).textval

    if db.db_client.add_new_client_account(api_id, api_hash, phone):
        BOT.send_message(message.chat.id, 'Клиентский аккаунт добавлен')
        menu_admin_accounts_show(message)
        mainmenu(message)
    else:
        BOT.send_message(message.chat.id, 'Ошибка добавления клиентского аккаунта')


def menu_admin_accounts_authorize(message, data):
    params = data.split(';')
    id_account = int(params[1])
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_ADMIN_AUTHACC_IDACCOUNT_GET.name, intval=id_account)

    if not client_ops.send_auth_code(id_account):
        BOT.send_message(message.chat.id, 'Ошибка запроса кода авторизации')
        return

    menu_admin_accounts_authorize_code_ask(message)


def menu_admin_accounts_authorize_code_ask(message):
    id_account = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_ADMIN_AUTHACC_IDACCOUNT_GET.name, is_delete_after_read=False).intval
    client_account_item = db.db_client.get_client_account(id_account)
    keyboard = make_keyboard(is_with_cancel=False)
    mes = f'Напишите код авторизации, который пришёл на номер {client_account_item.phone}'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_ADMIN_AUTHACC_CODE_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_ADMIN_AUTHACC_CODE_ASK.value)
def menu_admin_accounts_authorize_code_save(message):
    code = message.text
    if len(code) > 100:
        BOT.send_message(message.chat.id, 'Слишком длинный код')
        return

    id_account = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_ADMIN_AUTHACC_IDACCOUNT_GET.name, is_delete_after_read=False).intval
    if client_ops.authorize(id_account, code):
        BOT.send_message(message.chat.id, 'Авторизация пройдена успешно')
    else:
        BOT.send_message(message.chat.id, 'Ошибка авторизации')
    mainmenu(message)


def menu_admin_accounts_changefunc(message, data):
    params = data.split(';')
    id_account = int(params[1])
    db.db_tempvals.set_tmpval(message.chat.id, st.S_MENU_ADMIN_ACCFUNC_IDACCOUNT_GET.name, intval=id_account)
    menu_admin_accounts_changefunc_func_ask(message)


def menu_admin_accounts_changefunc_func_ask(message):
    id_account = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_ADMIN_ACCFUNC_IDACCOUNT_GET.name, is_delete_after_read=False).intval
    client_account_item = db.db_client.get_client_account(id_account)
    available_funcs_tuple = db.db_client.get_available_acc_funcs(client_account_item.id_account_func)

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard_list = []
    for func_item in available_funcs_tuple:
        keyboard_list.append(func_item.name)
    keyboard.add(*keyboard_list, row_width=2)

    mes = f'Какое назначение сделать аккаунту #{client_account_item.id}?'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)
    states.set_state(message.chat.id, st.S_MENU_ADMIN_ACCFUNC_FUNC_ASK.value)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_MENU_ADMIN_ACCFUNC_FUNC_ASK.value)
def menu_admin_accounts_changefunc_func_save(message):
    choice = message.text
    id_account = db.db_tempvals.get_tmpval(
        message.chat.id, st.S_MENU_ADMIN_ACCFUNC_IDACCOUNT_GET.name, is_delete_after_read=False).intval
    client_account_item = db.db_client.get_client_account(id_account)
    available_funcs_tuple = db.db_client.get_available_acc_funcs(client_account_item.id_account_func)
    if choice not in [classif.name for classif in available_funcs_tuple]:
        BOT.send_message(message.chat.id, 'Выберите из предложенного!')
        return

    new_func_item = db.db_classifiers.find_classifier_object(AccountFuncClassifier, name_object=choice)
    if db.db_client.set_acc_func(id_account, new_func_item.id):
        BOT.send_message(message.chat.id, 'Назначение изменено')
        mainmenu(message)
    else:
        BOT.send_message(message.chat.id, 'Ошибка изменения назначения')


def is_account_warm(client_account_item: ClientAccount) -> bool:  # TODO копия из client_ops.py
    warm_days = 5
    if client_account_item.date_reg >= datetime.datetime.now() - datetime.timedelta(days=warm_days):
        return True
    return False


def make_keyboard(items=None, row_width=1, fill_with_classifier=None, is_classifier_reverse=False, is_with_cancel=True):
    """Создание обычной клавиатуры с параметрами"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard_list = []

    if fill_with_classifier:
        classifier_items = db.db_classifiers.get_classifier_items(
            fill_with_classifier, is_reverse=is_classifier_reverse)
        for item in classifier_items:
            keyboard_list.append(item.name)

    if items:
        for item in items:
            keyboard_list.append(item)

    if is_with_cancel:
        keyboard_list.append('Отмена')

    if not items and not fill_with_classifier and not is_with_cancel:
        return types.ReplyKeyboardRemove()

    keyboard.add(*keyboard_list, row_width=row_width)
    return keyboard


@BOT.message_handler(content_types=['text'])
def dummy_message(message):
    """Любая другая текстовая команда"""
    cmd_start(message)


def startup_actions():
    """Стартовые действия"""
    pass


def timer_1min():
    """Таймер выполняющийся каждую 1 минуту"""
    LOGGER.info('Timer_1min thread started...')
    cycle_period = 60
    while True:
        try:
            pass

            time.sleep(cycle_period)
        except Exception as ex_tm:
            LOGGER.error(ex_tm)
            time.sleep(cycle_period)


def timer_inviter():
    """Таймер инвайтера"""
    LOGGER.info('Timer_inviter thread started...')
    while True:
        cycle_period = 60  # random.randrange(15, 30)
        try:
            client_ops.send_invites()
            time.sleep(cycle_period)
        except Exception as ex_tm:
            LOGGER.error(ex_tm)
            time.sleep(cycle_period)


if __name__ == '__main__':
    startup_actions()

    TIMER_1MIN_THREAD = threading.Thread(target=timer_1min)
    TIMER_1MIN_THREAD.daemon = True
    TIMER_1MIN_THREAD.start()

    TIMER_INVITER_THREAD = threading.Thread(target=timer_inviter)
    TIMER_INVITER_THREAD.daemon = True
    TIMER_INVITER_THREAD.start()

    try:
        BOT.infinity_polling(allowed_updates=util.update_types)
    except Exception as ex:
        LOGGER.error(ex)
        sys.exit()
