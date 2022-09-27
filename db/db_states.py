"""Стадии в меню"""
from models.model_service import State

from db.connection import Session


def get_cur_state(id_user: int) -> str:
    """Прочитать стадию меню у юзера"""
    session = Session()
    state_item = session.query(State).get(id_user)
    session.close()
    if state_item:
        return state_item.state
    return None


def set_state(id_user: int, state: str) -> bool:
    """Установить стадию меню у юзера"""
    session = Session()
    state_item = session.query(State).get(id_user)
    if state_item:
        state_item.state = state
        session.add(state_item)
    else:
        session.add(State(id_user=id_user, state=state))
    session.commit()
    session.close()
    return True
