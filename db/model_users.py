"""Модели юзеров, ролей, итд"""
import datetime
from sqlalchemy import (BigInteger, Boolean, Column, DateTime, ForeignKey,Integer, String, Table)
from db.base import Base



class User(Base):
    __tablename__ = 'users'
    __table_args__ = {"comment": "Юзеры"}

    id = Column(BigInteger, primary_key=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    username = Column(String(50))
    role_id = Column(Integer, ForeignKey('user_role.id'), nullable=False)
    # status_id = Column(Integer, ForeignKey('user_status.id'))
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now)



class UserRole(Base):
    __tablename__ = 'user_role'
    __table_args__ = {"comment": "Роль юзера"}

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


# class UserStatus(Base):
#     __tablename__ = 'user_status'
#     __table_args__ = {"comment": "Статус юзера"}

#     id = Column(Integer, primary_key=True)
#     name = Column(String(50), nullable=False, unique=True)


