"""Модели клиента (парсер, инвайтер)"""
import datetime

from sqlalchemy import (BigInteger, Boolean, Column, DateTime, ForeignKey,
                        Integer, String)

from models.base import Base

# pylint: disable=missing-class-docstring,too-few-public-methods


INVITE_SESSION_RESULTS = {
    'closed_manually': 1,
    'closed_by_flood_warning': 2,
}

INVITE_SEND_RESULTS = {
    'sent_normally': 1,
    'invite_restricted': 2,
}


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


class Member(Base):
    __tablename__ = 'members'
    __table_args__ = {"comment": "Спарсенные участники групп"}

    id = Column(BigInteger, primary_key=True)
    fio = Column(String(300), nullable=False)
    nick = Column(String(100))
    invite_restricted = Column(Boolean, comment='Заблокирован ли у юзера приём инвайтов (1 - да)')
    date_add = Column(DateTime, nullable=False, default=datetime.datetime.now)


class InviteSessionResultClassifier(Base):
    __tablename__ = 'n_invite_session_results'
    __table_args__ = {"comment": "Причины остановки рассылки"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class InviteSendResultClassifier(Base):
    __tablename__ = 'n_invite_send_results'
    __table_args__ = {"comment": "Результат отправки инвайта юзеру"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class InviteSession(Base):
    __tablename__ = 'invite_sessions'
    __table_args__ = {"comment": "Текущая рассылка, от старта до остановки"}

    id = Column(BigInteger, primary_key=True)
    id_group_destination = Column(BigInteger, nullable=False)
    datetime_start = Column(DateTime, nullable=False, default=datetime.datetime.now)
    datetime_end = Column(DateTime)
    result = Column(Integer, ForeignKey('n_invite_session_results.id'))


class InviteSend(Base):
    __tablename__ = 'invite_sends'
    __table_args__ = {"comment": "Отправки конкретным юзерам"}

    id = Column(BigInteger, primary_key=True)
    id_invite_session = Column(BigInteger, ForeignKey('invite_sessions.id'), nullable=False)
    id_member = Column(BigInteger, ForeignKey('members.id'), nullable=False)
    datetime_send = Column(DateTime, nullable=False, default=datetime.datetime.now)
    result = Column(Integer, ForeignKey('n_invite_send_results.id'))
