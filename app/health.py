from app.log_config import init_logging
init_logging(__name__)
import time, asyncio, aiohttp
from aiohttp_socks import ProxyConnector
import redis.asyncio as aioredis
from app.settings import get_settings

S = get_settings()
REDIS = aioredis.from_url(str(S.REDIS_URL), decode_responses=True)
URL   = "https://check.torproject.org/api/ip"
TO    = aiohttp.ClientTimeout(total=8)

async def check_tor() -> bool:
    try:
        conn = ProxyConnector.from_url("socks5://tor:9050", rdns=True)
        async with aiohttp.ClientSession(connector=conn, timeout=TO) as s:
            async with s.get(URL, ssl=False) as r:
                return r.status == 200
    except Exception:
        return False

async def count_good_proxies() -> int:
    n = 0
    async for _ in REDIS.scan_iter("good_proxy:*"):
        n += 1
    return n

async def health_summary() -> dict:
    t0 = time.perf_counter()
    tor_ok, proxy_cnt = await asyncio.gather(check_tor(), count_good_proxies())
    return {
        "tor": "ok" if tor_ok else "fail",
        "good_proxies": proxy_cnt,
        "uptime": f"{time.perf_counter()-t0:.3f}s"
    }
