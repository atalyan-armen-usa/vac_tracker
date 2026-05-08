"""Главный скрипт: проходит по источникам и сохраняет вакансии."""
import logging
import sys

from config import SEARCH_QUERIES, WEB_JSON_PATH
from db import init_db, get_conn, upsert_vacancy, log_run, now_iso, export_to_json
from sources import HHSource


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)
log = logging.getLogger("main")


def run_source(source, query: str) -> tuple[int, int]:
    """Возвращает (fetched, new)."""
    fetched = 0
    new = 0
    started = now_iso()
    error = None
    status = "ok"

    try:
        with get_conn() as conn:
            for v in source.fetch(query):
                fetched += 1
                if upsert_vacancy(conn, v):
                    new += 1
    except Exception as e:
        error = str(e)
        status = "error"
        log.exception("source %s failed on query %r", source.name, query)

    finished = now_iso()
    with get_conn() as conn:
        log_run(conn, source.name, query, started, finished, fetched, new, status, error)

    log.info("source=%s query=%r fetched=%d new=%d status=%s",
             source.name, query, fetched, new, status)
    return fetched, new


def main() -> int:
    init_db()

    total_fetched = 0
    total_new = 0

    sources = [HHSource()]
    try:
        for src in sources:
            for q in SEARCH_QUERIES:
                f, n = run_source(src, q)
                total_fetched += f
                total_new += n
    finally:
        for src in sources:
            if hasattr(src, "close"):
                src.close()

    count = export_to_json(WEB_JSON_PATH)
    log.info("DONE | total_fetched=%d total_new=%d exported=%d -> %s",
             total_fetched, total_new, count, WEB_JSON_PATH)
    return 0


if __name__ == "__main__":
    sys.exit(main())
