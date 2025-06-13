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


@app.task(name="proxy_health.refresh")
def proxy_refresh_good_proxies() -> int:
    """Оставляет в Redis только рабочие прокси."""
    import time
    import redis
    from app.proxy_health import check

    r = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)
    ttl = 3600
    now = int(time.time())

    stored: set[str] = {k.split(":", 1)[1] for k in r.scan_iter("good_proxy:*")}
    alive: set[str] = set(check())

    pipe = r.pipeline()
    for p in alive:
        pipe.setex(f"good_proxy:{p}", ttl, now)
    for p in stored - alive:
        pipe.delete(f"good_proxy:{p}")
    pipe.execute()

    return len(stored - alive)
