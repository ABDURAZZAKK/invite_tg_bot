"""Модели юзеров, ролей, итд"""
import datetime

from sqlalchemy import (BigInteger, Boolean, Column, DateTime, ForeignKey,
                        Integer, String)

from models.base import Base

# pylint: disable=missing-class-docstring,too-few-public-methods


ROLES = {
    'pending': 5,
    'admin': 10,
}


class RoleClassifier(Base):
    __tablename__ = 'n_role'
    __table_args__ = {"comment": "Роли юзеров"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class User(Base):
    __tablename__ = 'users'
    __table_args__ = {"comment": "Юзеры"}

    id = Column(BigInteger, primary_key=True)
    fio = Column(String(300), nullable=False)
    nick = Column(String(100))
    id_role = Column(Integer, ForeignKey('n_role.id'), nullable=False)
    date_reg = Column(DateTime, nullable=False, default=datetime.datetime.now)
    date_ban = Column(DateTime)
    reg = Column(Boolean, nullable=False, default=False)
    active = Column(Boolean, nullable=False, default=True)


class ClientAccount(Base):
    __tablename__ = 'client_accounts'
    __table_args__ = {"comment": "Аккаунты клиента-парсера"}

    id = Column(BigInteger, primary_key=True)
    api_id = Column(String(100), nullable=False)
    api_hash = Column(String(100), nullable=False)
    phone = Column(String(100), nullable=False)
    authorized = Column(Boolean, nullable=False, default=False, comment='пройдена авторизация')
    phone_code_hash = Column(String(100))
    banned = Column(Boolean, nullable=False, default=False, comment='аккаунт заблокирован телеграмом')
    date_reg = Column(DateTime, nullable=False, default=datetime.datetime.now)
    date_ban = Column(DateTime)
    active = Column(Boolean, nullable=False, default=True)
