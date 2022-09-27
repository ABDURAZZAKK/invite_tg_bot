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
        # call.message, call.data

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

    keyboard = make_keyboard(is_with_cancel=False)
    BOT.send_message(message.chat.id, 'Вы в главном меню', reply_markup=keyboard)


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
