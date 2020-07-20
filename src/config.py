import os


class Config:
    DEBUG = os.getenv('DEBUG', False)
    DB_CONNECTION = os.getenv('DB_CONNECTION', 'db.sqlite')
    SECRET_KEY = os.getenv('SECRET_KEY', 'secret').encode()
