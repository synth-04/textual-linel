import pathlib
import sqlite3

DATABASE_PATH = pathlib.Path().home() / "test1.db"

class Database:
    def __init__(self, db_path=DATABASE_PATH):
        self.db = sqlite3.connect(db_path)
        self.cursor = self.db.cursor()
        self._create_table()

    def _create_table(self):
        query = """
            CREATE TABLE IF NOT EXISTS words(
                id INTEGER PRIMARY KEY,
                word TEXT,
                type TEXT,
                english TEXT,
                class_decl TEXT, 
                root TEXT,
                notes TEXT
            );
        """
        self._run_query(query)

    def get_all_words(self):
        result = self._run_query("SELECT * FROM words;")
        return result.fetchall()

    def get_last_word(self):
        result = self._run_query(
            "SELECT * FROM words ORDER BY id DESC LIMIT 1;"
        )
        return result.fetchone()

    def add_word(self, word):
        self._run_query(
            "INSERT INTO words VALUES (NULL, ?, ?, ?, ?, ?, ?);",
            *word,
        )

    def delete_word(self, id):
        self._run_query(
            "DELETE FROM words WHERE id=(?);",
            id,
        )
    
    def clear_all_words(self):
        self._run_query("DELETE FROM words;")

    def _run_query(self, query, *query_args):
        result = self.cursor.execute(query, [*query_args])
        self.db.commit()
        return result