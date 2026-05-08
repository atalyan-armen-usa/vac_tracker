"""Парсер hh.ru через официальный API.

Документация: https://api.hh.ru/openapi/redoc
- Без авторизации, лимит ~по UA, запрос требует осмысленный User-Agent.
- Поиск: GET /vacancies?text=...&salary=...&only_with_salary=true&area=...&per_page=100&page=N
- Деталь: GET /vacancies/{id} (для skills и полного описания)
"""
import time
import json
import logging
from typing import Iterator

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .base import BaseSource
from config import (
    HH_API_BASE, HH_PER_PAGE, HH_MAX_PAGES, HH_REQUEST_DELAY,
    USER_AGENT, MIN_SALARY, AREAS, PRIORITY_AREA_IDS, PRIORITY_REMOTE,
)
from db import now_iso

log = logging.getLogger(__name__)


class HHSource(BaseSource):
    name = "hh"

    def __init__(self):
        self.client = httpx.Client(
            base_url=HH_API_BASE,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=30.0,
        )

    def close(self):
        self.client.close()

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
        reraise=True,
    )
    def _get(self, path: str, params: dict | None = None) -> dict:
        r = self.client.get(path, params=params)
        if r.status_code == 429:
            log.warning("hh: rate limited, backing off")
            raise httpx.HTTPError("rate limited")
        r.raise_for_status()
        return r.json()

    def fetch(self, query: str) -> Iterator[dict]:
        for area in AREAS:
            yield from self._fetch_area(query, area)

    def _fetch_area(self, query: str, area: int) -> Iterator[dict]:
        for page in range(HH_MAX_PAGES):
            params = {
                "text": query,
                "search_field": "name",       # ищем в названии — точнее
                "salary": MIN_SALARY,
                "only_with_salary": "true",
                "currency": "RUR",
                "area": area,
                "per_page": HH_PER_PAGE,
                "page": page,
            }
            try:
                data = self._get("/vacancies", params)
            except Exception as e:
                log.error("hh: fetch failed query=%s area=%s page=%s: %s", query, area, page, e)
                return

            items = data.get("items", [])
            if not items:
                return

            for raw in items:
                normalized = self._normalize(raw, query)
                if normalized:
                    yield normalized

            time.sleep(HH_REQUEST_DELAY)

            if page + 1 >= data.get("pages", 0):
                return

    def _normalize(self, raw: dict, query: str) -> dict | None:
        salary = raw.get("salary") or {}
        s_from = salary.get("from")
        s_to = salary.get("to")

        # Доп. фильтр: верхняя граница (или нижняя если to нет) >= MIN_SALARY
        max_salary = s_to or s_from or 0
        if max_salary < MIN_SALARY:
            return None

        area = raw.get("area") or {}
        schedule = (raw.get("schedule") or {}).get("id")
        snippet = raw.get("snippet") or {}

        is_remote = schedule == "remote"
        is_priority_area = int(area.get("id", -1)) in PRIORITY_AREA_IDS
        priority = 1 if (is_remote and PRIORITY_REMOTE) or is_priority_area else 2

        return {
            "source": self.name,
            "external_id": str(raw["id"]),
            "url": raw.get("alternate_url"),
            "title": raw.get("name"),
            "company": (raw.get("employer") or {}).get("name"),
            "salary_from": s_from,
            "salary_to": s_to,
            "currency": salary.get("currency"),
            "salary_gross": 1 if salary.get("gross") else 0,
            "area_id": int(area["id"]) if area.get("id") else None,
            "area_name": area.get("name"),
            "schedule": schedule,
            "employment": (raw.get("employment") or {}).get("id"),
            "experience": (raw.get("experience") or {}).get("id"),
            "requirement": snippet.get("requirement"),
            "responsibility": snippet.get("responsibility"),
            "skills": json.dumps([], ensure_ascii=False),  # детальные навыки — позже, чтобы не делать N запросов
            "role_query": query,
            "priority": priority,
            "published_at": raw.get("published_at"),
            "raw_json": json.dumps(raw, ensure_ascii=False),
            "fetched_at": now_iso(),
        }
