"""Работа с SQLite: схема, инициализация, вставка."""
import sqlite3
import json
from contextlib import contextmanager
from datetime import datetime, timezone

from config import DB_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS vacancies (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    source          TEXT    NOT NULL,
    external_id     TEXT    NOT NULL,
    url             TEXT,
    title           TEXT,
    company         TEXT,
    salary_from     INTEGER,
    salary_to       INTEGER,
    currency        TEXT,
    salary_gross    INTEGER,        -- 1 = до вычета, 0 = на руки
    area_id         INTEGER,
    area_name       TEXT,
    schedule        TEXT,           -- remote / fullDay / etc.
    employment      TEXT,
    experience      TEXT,
    requirement     TEXT,
    responsibility  TEXT,
    skills          TEXT,           -- JSON array
    role_query      TEXT,           -- какой запрос её нашёл
    priority        INTEGER,        -- 1 = Москва или удалёнка
    published_at    TEXT,
    raw_json        TEXT,
    fetched_at      TEXT,
    UNIQUE(source, external_id)
);

CREATE INDEX IF NOT EXISTS idx_vac_priority    ON vacancies(priority);
CREATE INDEX IF NOT EXISTS idx_vac_published   ON vacancies(published_at);
CREATE INDEX IF NOT EXISTS idx_vac_salary_from ON vacancies(salary_from);

CREATE TABLE IF NOT EXISTS sync_runs (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    source         TEXT,
    query          TEXT,
    started_at     TEXT,
    finished_at    TEXT,
    fetched_count  INTEGER,
    new_count      INTEGER,
    status         TEXT,
    error          TEXT
);
"""


@contextmanager
def get_conn(path: str = DB_PATH):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(path: str = DB_PATH) -> None:
    with get_conn(path) as c:
        c.executescript(SCHEMA)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def upsert_vacancy(conn: sqlite3.Connection, v: dict) -> bool:
    """Вставить вакансию, если её ещё нет. Возвращает True если новая."""
    cur = conn.execute(
        """
        INSERT OR IGNORE INTO vacancies (
            source, external_id, url, title, company,
            salary_from, salary_to, currency, salary_gross,
            area_id, area_name, schedule, employment, experience,
            requirement, responsibility, skills,
            role_query, priority, published_at, raw_json, fetched_at
        ) VALUES (
            :source, :external_id, :url, :title, :company,
            :salary_from, :salary_to, :currency, :salary_gross,
            :area_id, :area_name, :schedule, :employment, :experience,
            :requirement, :responsibility, :skills,
            :role_query, :priority, :published_at, :raw_json, :fetched_at
        )
        """,
        v,
    )
    return cur.rowcount > 0


def log_run(conn, source, query, started, finished, fetched, new, status, error=None):
    conn.execute(
        """INSERT INTO sync_runs
           (source, query, started_at, finished_at, fetched_count, new_count, status, error)
           VALUES (?,?,?,?,?,?,?,?)""",
        (source, query, started, finished, fetched, new, status, error),
    )


def export_to_json(path: str) -> int:
    """Экспортирует все вакансии в JSON для веб-странички. Возвращает count."""
    with get_conn() as c:
        rows = c.execute(
            """SELECT source, external_id, url, title, company,
                      salary_from, salary_to, currency, salary_gross,
                      area_name, schedule, employment, experience,
                      requirement, responsibility, skills,
                      role_query, priority, published_at, fetched_at
               FROM vacancies
               ORDER BY published_at DESC"""
        ).fetchall()
    data = []
    for r in rows:
        d = dict(r)
        if d.get("skills"):
            try:
                d["skills"] = json.loads(d["skills"])
            except Exception:
                d["skills"] = []
        else:
            d["skills"] = []
        data.append(d)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {"generated_at": now_iso(), "count": len(data), "vacancies": data},
            f, ensure_ascii=False, indent=2,
        )
    return len(data)
