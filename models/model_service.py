"""Всякие сервисные модели для самого бота"""
import datetime

from sqlalchemy import (BigInteger, Boolean, Column, Date, DateTime, String,
                        Text)

from models.base import Base

# pylint: disable=missing-class-docstring,too-few-public-methods


class State(Base):
    __tablename__ = 'states'
    __table_args__ = {"comment": "Стадии меню у юзеров"}

    id_user = Column(BigInteger, primary_key=True)
    state = Column(String(255), nullable=False, comment="Номер стадии")


class Tempval(Base):
    __tablename__ = 'tempvals'
    __table_args__ = {"comment": "Временные переменные"}

    id_user = Column(BigInteger, primary_key=True)
    state = Column(String(100), primary_key=True, nullable=False,
                   comment="К какому шагу меню относится данная переменная")
    intval = Column(BigInteger)
    textval = Column(Text)
    protect = Column(Boolean, nullable=False, default=False, comment="Не будет удалено методом clear_user_tempvals()")
    date_create = Column(DateTime, nullable=False, default=datetime.datetime.now)


class Pref(Base):
    __tablename__ = 'prefs'
    __table_args__ = {"comment": "Константы и постоянные переменные"}

    name = Column(String(50), primary_key=True)
    intval = Column(BigInteger)
    textval = Column(Text)
    dateval = Column(Date)
    datetimeval = Column(DateTime)


class Resource(Base):
    __tablename__ = 'resources'
    __table_args__ = {"comment": "Файлы ресурсов и их ID"}

    name = Column(String(50), primary_key=True)
    path = Column(String(255), nullable=False, comment="Путь к файлу на сервере")
    file_id = Column(String(255), comment="TG ID")
    date_update = Column(DateTime, nullable=False, default=datetime.datetime.now)


class ServiceChat(Base):
    __tablename__ = 'service_chats'
    __table_args__ = {"comment": "ID сервисных групп и каналов"}

    name = Column(String(50), primary_key=True)
    chat_id = Column(String(255), comment="id чата в TG")
    hyperlink = Column(String(255), comment="ссылка на чат")
