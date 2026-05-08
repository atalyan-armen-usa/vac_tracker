"""Базовый класс для парсеров источников."""
from abc import ABC, abstractmethod
from typing import Iterator


class BaseSource(ABC):
    name: str = "base"

    @abstractmethod
    def fetch(self, query: str) -> Iterator[dict]:
        """Yield-ит словари вакансий в нормализованном формате (см. db.upsert_vacancy)."""
        ...
