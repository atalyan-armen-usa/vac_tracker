"""Конфигурация скрейпера вакансий."""

# Роли для поиска (отдельный запрос на каждую)
SEARCH_QUERIES = [
    "системный аналитик",
    "владелец продукта",
    "product owner",
    "продакт менеджер",
    "product manager",
]

# Минимальная зарплата (RUB) — только вакансии с указанной ЗП >= этой суммы
MIN_SALARY = 400_000

# Регионы hh.ru:
#   113 — Россия (вся)
#   1   — Москва
#   2   — Санкт-Петербург
AREAS = [113]  # Вся РФ; приоритет Москвы/удалёнки выставляется при сохранении

# Приоритетные локации (отмечаются priority=1)
PRIORITY_AREA_IDS = {1}  # Москва
PRIORITY_REMOTE = True   # Удалёнка тоже приоритет

# hh.ru API
HH_API_BASE = "https://api.hh.ru"
HH_PER_PAGE = 100         # максимум, разрешённый API
HH_MAX_PAGES = 20         # 20 * 100 = 2000 на запрос (лимит API = 2000)
HH_REQUEST_DELAY = 0.5    # сек между запросами (вежливость)

# User-Agent (hh API требует осмысленный UA)
USER_AGENT = "VacancyTracker/1.0 (contact: vacancy-tracker@example.com)"

# БД
DB_PATH = "vacancies.db"

# Экспорт для веб-странички
WEB_JSON_PATH = "web/vacancies.json"
