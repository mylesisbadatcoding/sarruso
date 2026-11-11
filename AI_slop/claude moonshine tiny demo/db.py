"""SQLite storage for transcription entries."""
import os
import sqlite3
import threading
from pathlib import Path

from metrics import wer_cer

DB_PATH = Path(os.environ.get("STT_DB", Path(__file__).parent / "data" / "entries.db"))
_lock = threading.Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    source TEXT,
    model TEXT,
    text TEXT,
    reference TEXT,
    audio_seconds REAL,
    infer_ms REAL,
    rtf REAL,
    tokens INTEGER,
    tokens_per_sec REAL,
    wer REAL,
    cer REAL,
    live_passes INTEGER,
    avg_pass_ms REAL,
    first_text_ms REAL
)
"""


def _conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def init():
    with _lock, _conn() as c:
        c.execute(SCHEMA)


def insert(row: dict) -> dict:
    cols = list(row.keys())
    sql = f"INSERT INTO entries ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})"
    with _lock, _conn() as c:
        cur = c.execute(sql, [row[k] for k in cols])
        new_id = cur.lastrowid
    return get(new_id)


def get(entry_id: int):
    with _lock, _conn() as c:
        r = c.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    return dict(r) if r else None


def list_entries():
    with _lock, _conn() as c:
        rows = c.execute("SELECT * FROM entries ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]


def set_reference(entry_id: int, reference):
    entry = get(entry_id)
    if not entry:
        return None
    wer, cer = wer_cer(reference, entry["text"]) if reference else (None, None)
    with _lock, _conn() as c:
        c.execute(
            "UPDATE entries SET reference = ?, wer = ?, cer = ? WHERE id = ?",
            (reference or None, wer, cer, entry_id),
        )
    return get(entry_id)


def delete(entry_id: int) -> bool:
    with _lock, _conn() as c:
        cur = c.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        return cur.rowcount > 0


def clear():
    with _lock, _conn() as c:
        c.execute("DELETE FROM entries")


def summary(entries: list) -> dict:
    def mean(key):
        vals = [e[key] for e in entries if e.get(key) is not None]
        return sum(vals) / len(vals) if vals else None

    return {
        "count": len(entries),
        "total_audio_seconds": sum(e["audio_seconds"] or 0 for e in entries),
        "mean_rtf": mean("rtf"),
        "mean_tokens_per_sec": mean("tokens_per_sec"),
        "mean_infer_ms": mean("infer_ms"),
        "mean_first_text_ms": mean("first_text_ms"),
        "mean_wer": mean("wer"),
        "mean_cer": mean("cer"),
        "with_reference": sum(1 for e in entries if e.get("wer") is not None),
    }
