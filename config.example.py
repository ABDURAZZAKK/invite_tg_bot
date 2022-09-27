"""Конфигурационный файл"""

IS_TEST = True

# bot token (from @BotFather)
TOKEN_BOT = ''

DB_USER = ''
DB_PASSWORD = ''
DB_NAME = ''
DB_HOST = 'localhost'
DB_URL = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}'
