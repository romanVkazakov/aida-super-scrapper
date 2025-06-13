"""Celery tasks (один файл)."""

from celery_app import celery as app
import asyncio
from proxy_health import check


@app.task(name="proxy_health.check")
def proxy_health_check() -> list[str]:
    import inspect

    if inspect.iscoroutinefunction(check):
        return asyncio.run(check())
    import redis
    import time

    r = redis.Redis(host="redis", port=6379, db=0)
    pipe = r.pipeline()
    ttl = 3600  # 1 час
    for p in check():
        pipe.setex(f"good_proxy:{p}", ttl, int(time.time()))
    pipe.execute()
    return check()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **_):
    sender.add_periodic_task(60.0, proxy_health_check.s(), name="proxy health check")


import json
import logging
import redis
from celery.schedules import crontab

log = logging.getLogger(__name__)
r = redis.Redis(host="redis")  # если в compose другой host – поправь!


@app.task
def flush_bad_cache():
    """Удаляем html_cache:* у которых поле url начинается с '<html'."""
    deleted = 0
    for key in r.scan_iter("html_cache:*"):
        try:
            data = json.loads(r.get(key) or "{}")
            if str(data.get("url", "")).lstrip().startswith("<html"):
                r.delete(key)
                deleted += 1
        except Exception:
            r.delete(key)
            deleted += 1
    log.info("flush_bad_cache removed %s keys", deleted)
    return deleted


#  ───── Celery beat расписание ─────
from celery import current_app

current_app.conf.beat_schedule.update(
    {
        "flush-bad-cache-every-10min": {
            "task": "tasks.flush_bad_cache",
            "schedule": crontab(minute="*/10"),
        }
    }
)
