"""Соединение с БД для SQLAlchemy"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config as botconf

engine = create_engine(botconf.DB_URL, pool_size=200)
Session = sessionmaker(bind=engine)
