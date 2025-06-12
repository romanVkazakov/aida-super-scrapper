"""Celery tasks (один файл)."""
from celery_app import celery as app
import asyncio
from proxy_health import check

@app.task(name="proxy_health.check")
def proxy_health_check() -> list[str]:
    import asyncio, inspect
    if inspect.iscoroutinefunction(check):
        return asyncio.run(check())
    import redis, time ;
    r = redis.Redis(host="redis", port=6379, db=0);
    pipe = r.pipeline();
    ttl = 3600  # 1 час
    for p in check():
        pipe.setex(f"good_proxy:{p}", ttl, int(time.time()));
    pipe.execute();
    return check()

@app.on_after_configure.connect
def setup_periodic_tasks(sender, **_):
    sender.add_periodic_task(60.0, proxy_health_check.s(),
                             name="proxy health check")
