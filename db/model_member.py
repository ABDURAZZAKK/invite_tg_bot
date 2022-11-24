"""Всякие сервисные модели для самого бота"""
import datetime
from sqlalchemy import (BigInteger, Boolean, Column, Date, DateTime, String,Text, ForeignKey)
from db.base import Base




class Member(Base):
    __tablename__ = 'members'
    __table_args__ = {"comment": "Спарсенные участники групп"}

    id = Column(BigInteger, primary_key=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    username = Column(String(50))
    invite_restricted = Column(Boolean, comment='Заблокирован ли у юзера приём инвайтов (1 - да)')
    chat_id = Column(BigInteger)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)


# class Chat(Base):
#     __tablename__ = 'chats'
#     __table_args__ = {"comment": "ID сервисных групп и каналов"}

#     id = Column(BigInteger, comment="id чата в TG")
#     name = Column(String(50), primary_key=True)
#     hyperlink = Column(String(255), comment="ссылка на чат")
