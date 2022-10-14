"""Состояние пользователей в меню"""
import logging
from enum import Enum

import db

LOGGER = logging.getLogger('applog')


def get_cur_state(id_user: int) -> str:
    """Возвращает текущую стадию"""
    state = db.db_states.get_cur_state(id_user)
    if not state:
        state = States.S_START.value
    return state


def set_state(id_user: int, state: str) -> bool:
    """Сохраняет стадию, на которую переходит пользователь"""
    db.db_states.set_state(id_user, state)
    LOGGER.info("user %s come to %s (%s)", id_user, States(state).name, state)
    return True


class States(Enum):
    """
        Стадии меню юзеров.
        Стадии регистрации начинаются на "0"
        Стадия главного меню всегда "1"
        Стадии после главного меню обозначаются как:
            1 цифра - всегда "1"
            2 цифра - роль юзера
            3 цифра - тематический подраздел
            4 цифра - шаг в этом подразделе
            цифры далее - пункты добавленные позднее
    """
    S_START = '0'

    S_REG_FIO_GET = '0.1'
    S_REG_PENDING = '0.99'

    S_MAINMENU = '1'

    S_MENU_ADMIN_CREATEACC_API_ID_ASK = '1.10.1.1'
    S_MENU_ADMIN_CREATEACC_API_HASH_ASK = '1.10.1.2'
    S_MENU_ADMIN_CREATEACC_API_PHONE_ASK = '1.10.1.3'

    S_MENU_ADMIN_AUTHACC_IDACCOUNT_GET = '1.10.2.1'
    S_MENU_ADMIN_AUTHACC_CODE_ASK = '1.10.2.2'

    S_MENU_ADMIN_ACCFUNC_IDACCOUNT_GET = '1.10.3.1'
    S_MENU_ADMIN_ACCFUNC_FUNC_ASK = '1.10.3.2'
