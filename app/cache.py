import redis.asyncio as aioredis, hashlib, logging
from app.browser_core import fetch_html as _fetch_html_core
TTL_SEC = 15 * 60
log = logging.getLogger("cache")

_redis = None
async def _r():
    global _redis
    if _redis is None:
        _redis = await aioredis.from_url("redis://redis:6379/0")
    return _redis

async def cached_fetch_html(url: str) -> str:
    key = "html_cache:" + hashlib.sha1(url.encode()).hexdigest()
    r   = await _r()
    html = await r.get(key)
    if html:
        log.info("cache HIT %s", url)
        return html.decode()
    log.info("cache MISS %s", url)
    html = await _fetch_html_core(url)
    await r.setex(key, TTL_SEC, html.encode())
    return html
