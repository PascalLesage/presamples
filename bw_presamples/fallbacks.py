from peewee import SqliteDatabase
from playhouse.shortcuts import RetryOperationalError


class RetryDatabase(RetryOperationalError, SqliteDatabase):
    pass


def create_database(filepath, tables):
    db = RetryDatabase(filepath)
    for table in tables:
        table._meta.database = db
    db.create_tables(tables, safe=True)
    return db
