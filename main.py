#!venv/bin/python
"""Main module"""

import datetime
import logging
import logging.handlers as loghandlers
import os
import sys
import threading
import time

import telebot
from telebot import types, util

import client_ops
import config
import db
import states
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
    row_width = 1

    if user.id_role == ROLES['admin']:
        keyb_items.append('Аккаунт')

    keyboard = make_keyboard(items=keyb_items, row_width=row_width, is_with_cancel=False)
    mes = 'Вы в главном меню'

    BOT.send_message(message.chat.id, mes, reply_markup=keyboard)


@BOT.message_handler(func=lambda message: states.get_cur_state(message.chat.id) == st.S_MAINMENU.value)
def mainmenu_choice(message):
    """Обработка нажатия в главном меню"""
    choice = message.text
    user = db.db_users.get_user(message.chat.id)

    if user.id_role == ROLES['admin']:
        if choice == 'Аккаунт':
            menu_admin_accounts_show(message)


def menu_admin_accounts_show(message):
    BOT.send_message(message.chat.id, 'Проверка аккаунтов...')
    if not client_ops.check_account_availability():
        BOT.send_message(message.chat.id, 'Ошибка проверки аккаунтов')
        return
    client_accounts_tuple = db.db_users.get_all_client_accounts()

    keyboard_inline = None
    keyboard_list = []
    mes = ''

    if client_accounts_tuple:
        for client_account in client_accounts_tuple:
            mes += f'<b>Аккаунт #{client_account.id}</b>\n'
            mes += f'api_id: {client_account.api_id}\n'
            mes += f'api_hash: {client_account.api_hash}\n'
            mes += f'телефон: {client_account.phone}\n\n'
            if client_account.banned == 1:
                mes += f'🔴<b>Статус:</b> заблокирован Телеграмом'
            elif client_account.active == 0:
                mes += f'⚫<b>Статус:</b> неактивен'
            elif client_account.authorized == 0:
                mes += f'🟡<b>Статус:</b> требуется авторизация'
                keyboard_inline = types.InlineKeyboardMarkup()
                keyboard_list.append(types.InlineKeyboardButton(text='Авторизовать',
                                     callback_data=f"menu_admin_accounts_authorize;{client_account.id}"))
                keyboard_inline.add(*keyboard_list, row_width=1)
            else:
                mes += f'🟢<b>Статус:</b> активен'
    else:
        keyboard_inline = types.InlineKeyboardMarkup()
        keyboard_list.append(types.InlineKeyboardButton(text='Создать аккаунт',
                             callback_data="menu_admin_accounts_create;1"))
        keyboard_inline.add(*keyboard_list, row_width=1)
        mes += 'Нет клиентских аккаунтов'

    BOT.send_message(message.chat.id, mes, parse_mode='html', reply_markup=keyboard_inline)


def menu_admin_accounts_create(message):
    client_accounts_tuple = db.db_users.get_all_client_accounts()
    if client_accounts_tuple:
        BOT.send_message(message.chat.id, 'Пока что доступен только 1 аккаунт')
        mainmenu(message)
        return
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

    if db.db_users.add_new_client_account(api_id, api_hash, phone):
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
    client_account_item = db.db_users.get_client_account(id_account)
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


@BOT.message_handler(content_types=['text'])
def dummy_message(message):
    """Любая другая текстовая команда"""
    cmd_start(message)


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


if __name__ == '__main__':
    startup_actions()

    TIMER_1MIN_THREAD = threading.Thread(target=timer_1min)
    TIMER_1MIN_THREAD.daemon = True
    TIMER_1MIN_THREAD.start()

    try:
        BOT.infinity_polling(allowed_updates=util.update_types)
    except Exception as ex:
        LOGGER.error(ex)
        sys.exit()
