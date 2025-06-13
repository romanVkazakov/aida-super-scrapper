# -*- coding: utf-8 -*-
"""Celery tasks — всё в одном файле."""

from __future__ import annotations

import asyncio
import time
import redis

from celery import Celery
from celery.schedules import crontab
from app.proxy_health import check

# ─────────────────────  базовый Celery-app  ───────────────────────────
app = Celery(
    "tasks",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
)


# ─────────────────────  задачи  ───────────────────────────────────────
@app.task(name="proxy_health.check")
def proxy_health_check() -> list[str]:
    """Пингует прокси и складывает живые в Redis: good_proxy:*"""
    proxies = asyncio.run(check()) if asyncio.iscoroutinefunction(check) else check()

    r = redis.Redis(host="redis", db=0, decode_responses=True)
    now, ttl = int(time.time()), 3600
    pipe = r.pipeline()
    for p in proxies:
        pipe.setex(f"good_proxy:{p}", ttl, now)
    pipe.execute()
    return proxies


@app.task(name="proxy_health.refresh")
def proxy_refresh_good_proxies() -> int:
    """Синхронизирует good_proxy:* с актуальным списком живых прокси."""
    r = redis.Redis(host="redis", db=0, decode_responses=True)
    now, ttl = int(time.time()), 3600

    stored = {k.split(":", 1)[1] for k in r.scan_iter("good_proxy:*")}
    alive = set(check())

    pipe = r.pipeline()
    for p in alive:
        pipe.setex(f"good_proxy:{p}", ttl, now)
    for p in stored - alive:
        pipe.delete(f"good_proxy:{p}")
    pipe.execute()

    return len(stored - alive)


@app.task(name="tasks.flush_bad_cache")
def flush_bad_cache() -> int:
    """Убирает мусор bad_cache:*"""
    r = redis.Redis(host="redis", db=0, decode_responses=True)
    removed = 0
    for k in r.scan_iter("bad_cache:*"):
        r.delete(k)
        removed += 1
    return removed


# ────────────────────  расписание beat  ───────────────────────────────
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **_):
    # каждую минуту — детект живых прокси
    sender.add_periodic_task(60.0, proxy_health_check.s(), name="proxy health check")
    # каждые 5 минут — актуализируем good_proxy:*
    sender.add_periodic_task(
        crontab(minute="*/5"),
        proxy_refresh_good_proxies.s(),
        name="proxy refresh good proxies",
    )
    # каждые 10 минут — чистим мусорный кеш
    sender.add_periodic_task(
        crontab(minute="*/10"),
        flush_bad_cache.s(),
        name="flush bad cache",
    )
