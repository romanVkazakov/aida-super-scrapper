#!/usr/bin/env bash
set -e
echo "🔄  mass-fix импортов..."

# какие внешние пакеты надо «расшить»
for pkg in fastapi prometheus_client pythonjsonlogger; do
  find app -type f -name '*.py' -exec \
    sed -i -E "s/^from +app\.${pkg//\./\\.} +import /from ${pkg} import /" {} +
done

echo "📦 пересборка образа api (кэш ускорит)"
docker compose build api

echo "🧪 pytest…"
docker compose run --rm -v \"\$(pwd)\":/app -e PYTHONPATH=/app api \
  sh -c \"pip install -q pytest==8.2.0 httpx python-json-logger==2.0.7 && pytest -q tests\" \
|| { echo '⛔️  ещё один import отсутствует — смотри сообщение выше'; exit 1; }

echo -e '\n✅  Всё зелёное! Тесты прошли.'
