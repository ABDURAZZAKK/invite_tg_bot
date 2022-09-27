"""Временные переменные в БД"""
from models.model_service import Tempval

from db.connection import Session


def set_tmpval(id_user: int, state: str, intval: int = None, textval: str = None, is_protect: bool = False) -> bool:
    """Запись временной переменной"""
    session = Session()
    tmpval_item = session.query(Tempval).get((id_user, state))
    if tmpval_item:
        tmpval_item.intval = intval
        tmpval_item.textval = textval
        tmpval_item.protect = is_protect
        session.add(tmpval_item)
    else:
        session.add(Tempval(
            id_user=id_user,
            state=state,
            intval=intval,
            textval=textval,
            protect=is_protect
        ))
    session.commit()
    session.close()
    return True


def get_tmpval(id_user: int, state: str, is_delete_after_read: bool = True) -> Tempval:
    """Чтение временной переменной"""
    session = Session()
    tmpval_item = session.query(Tempval).get((id_user, state))
    if tmpval_item and is_delete_after_read:
        session.delete(tmpval_item)
        session.commit()
    session.close()
    return tmpval_item


def clear_user_tempvals(id_user: int) -> bool:
    """Очистка временных переменных юзера"""
    session = Session()
    session.query(Tempval).filter(Tempval.id_user == id_user, Tempval.protect == 0).delete(synchronize_session='fetch')
    session.commit()
    session.close()
    return True
