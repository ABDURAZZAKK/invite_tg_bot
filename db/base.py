"""Основа для моделей"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from databases import Database

from config import DATABASE_URL


Base = declarative_base()
database = Database(DATABASE_URL)
engine = create_engine(DATABASE_URL)


