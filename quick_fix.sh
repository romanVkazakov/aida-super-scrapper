#!/usr/bin/env bash
set -e

echo "▶ 1. Перемещаю browser_core.py в пакет app/"
mv -f browser_core.py app/browser_core.py

echo "▶ 2. Правлю импорт в app/cache.py → app.browser_core"
sed -i 's/^from browser_core import/from app.browser_core import/' app/cache.py

echo "▶ 3. Пересобираю образ api (кэш, поэтому быстро)"
docker compose build api

echo "▶ 4. Гоняю pytest внутри временного контейнера …"
docker compose run --rm \
  -v "$(pwd)":/app \
  -e PYTHONPATH=/app \
  api sh -c "pip install -q pytest==8.2.0 httpx && pytest -q tests"
