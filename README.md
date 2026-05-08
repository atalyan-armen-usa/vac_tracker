# Vacancy Scraper · Системный аналитик / Product

Сканирует hh.ru API, складывает вакансии (системный аналитик, владелец продукта, продакт-менеджер) с указанной ЗП от 400 000 ₽ в SQLite. Обновляется по расписанию через GitHub Actions, статичная веб-страничка с фильтрами публикуется на GitHub Pages.

## Что внутри

```
config.py             — роли, мин. ЗП, регионы
db.py                 — SQLite + экспорт в JSON
sources/hh.py         — парсер hh.ru API
main.py               — точка входа
web/index.html        — UI с фильтрами/сортировкой
web/vacancies.json    — данные для UI (автогенерируется)
.github/workflows/scrape.yml — cron-расписание + деплой Pages
```

## Запуск локально

```bash
pip install -r requirements.txt
python main.py
# Откроется vacancies.db, web/vacancies.json обновится
# Открыть UI: запустить локальный http-сервер
python -m http.server -d web 8000
# → http://localhost:8000
```

## Деплой на GitHub Pages (бесплатно)

**Шаг 1.** Создай новый репозиторий на github.com (например `vacancy-tracker`), публичный.

**Шаг 2.** В этой папке:
```bash
git init -b main
git add .
git commit -m "init"
git remote add origin git@github.com:USERNAME/vacancy-tracker.git
git push -u origin main
```

**Шаг 3.** В репозитории на GitHub:
1. **Settings → Pages → Source → "GitHub Actions"** (НЕ "Deploy from branch")
2. **Settings → Actions → General → Workflow permissions → "Read and write permissions"** → Save
3. **Actions → Scrape vacancies → Run workflow** (первый запуск вручную)

После первого прогона (3–5 минут) страничка будет доступна по адресу:  
`https://USERNAME.github.io/vacancy-tracker/`

Дальше скрейпер сам бегает раз в день и пушит обновления.

## Настройка

Поменяй в `config.py`:
- `SEARCH_QUERIES` — поисковые запросы
- `MIN_SALARY` — нижний порог ЗП
- `AREAS` — регионы (`113` = вся РФ, `1` = Москва)
- `PRIORITY_AREA_IDS` — какие города отмечать как приоритетные

После правки запусти `python main.py` локально или дёрни workflow в Actions.

## Дальнейшие шаги (как захочешь)

- Добавить парсер Habr Career (`sources/habr.py`)
- Подтягивать `key_skills` из деталки `/vacancies/{id}` на hh
- Алерты на новые приоритетные вакансии (Telegram-бот)
