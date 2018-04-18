from peewee import SqliteDatabase


class SubstitutableDatabase:
    def __init__(self, filepath, tables):
        self._filepath = filepath
        self._tables = tables
        self._database = self._create_database()

    def _create_database(self):
        db = SqliteDatabase(self._filepath)
        for model in self._tables:
            model.bind(db, bind_refs=False, bind_backrefs=False)
        db.connect()
        db.create_tables(self._tables)
        return db
