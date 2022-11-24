from aiogram.dispatcher.filters.state import State, StatesGroup


class GlobalState(StatesGroup):
    admin = State()
    set_api_id = State()
    set_api_hash = State()
    set_phone = State()
    set_acc_func = State()

    auth_acc = State()

    test = State()
