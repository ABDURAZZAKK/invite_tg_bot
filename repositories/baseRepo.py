from databases import Database


class BaseRepo:
    def __init__(self, database: Database) -> None:
        self.database = database