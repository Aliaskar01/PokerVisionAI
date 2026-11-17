import sqlite3
from pathlib import Path

def connect(path: Path):
    path.parent.mkdir(parents=True,exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute('PRAGMA journal_mode=WAL')
    connection.execute('CREATE TABLE IF NOT EXISTS analyses (id INTEGER PRIMARY KEY, created TEXT NOT NULL, hand_id TEXT, mode TEXT NOT NULL, payload TEXT NOT NULL)')
    return connection
