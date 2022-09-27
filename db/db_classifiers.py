"""Классификаторы"""
from sqlalchemy import desc

from db.connection import Session


def get_classifier_items(model, is_reverse: bool = False):
    """Весь классификатор по названию модели"""
    session = Session()
    if hasattr(model, 'active'):
        values_tuple = session.query(model).filter(model.active == 1).order_by(
            desc(model.id) if is_reverse else model.id).all()
    else:
        values_tuple = session.query(model).order_by(desc(model.id) if is_reverse else model.id).all()
    session.close()
    return values_tuple


def find_classifier_object(model, id_object: int = None, name_object: str = None):
    """Поиск объекта в классификаторе по его id или имени"""
    session = Session()
    if hasattr(model, 'active'):
        if id_object:
            item = session.query(model).filter(model.id == id_object, model.active == 1).first()
        elif name_object:
            item = session.query(model).filter(model.name == name_object, model.active == 1).first()
        else:
            item = None
    else:
        if id_object:
            item = session.query(model).get(id_object)
        elif name_object:
            item = session.query(model).filter(model.name == name_object).first()
        else:
            item = None
    session.close()
    return item
