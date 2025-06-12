# ─────────────────────────────────────────────────────────────────────────────
# База уже содержит Chromium + все системные библиотеки
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# -------------------------------------------------- python deps
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------------------------- проект
COPY app/ /app
COPY tasks.py /app/tasks.py
COPY app/__init__.py /app/__init__.py
COPY ua_list.txt lang_list.txt proxies.txt /app/

# -------------------------------------------------- default CMD для api-контейнера
CMD ["uvicorn", "main:api", "--host", "0.0.0.0", "--port", "8000"]
