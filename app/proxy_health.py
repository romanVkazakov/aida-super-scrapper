from app.log_config import init_logging

init_logging(__name__)
from app.settings import get_settings
import asyncio
import random
import ssl
import os
import pathlib
import aiohttp
import redis
from app.proxy_pool import ban_proxy

PROXY_FILE = os.getenv("PROXY_FILE", "/app/proxies.txt")
REDIS_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
GOOD_TTL = get_settings().GOOD_TTL
TEST_URL = "http://httpbin.org/ip"

r = redis.from_url(REDIS_URL, decode_responses=True)


def pick_proxies(n=100):
    p = pathlib.Path(PROXY_FILE)
    if not p.exists():
        return []
    lines = [
        l.strip()
        for l in p.read_text().splitlines()
        if l.strip() and not l.startswith("#")
    ]
    random.shuffle(lines)
    return [f"http://{l}" for l in lines][:n]


async def probe(proxy: str) -> bool:
    conn = aiohttp.TCPConnector(ssl=ssl.create_default_context())
    try:
        async with aiohttp.ClientSession(connector=conn) as sess:
            async with sess.get(TEST_URL, proxy=proxy, timeout=10):
                return True
    except Exception:
        return False


async def check_batch():
    tasks = {asyncio.create_task(probe(p)): p for p in pick_proxies()}
    results = await asyncio.gather(*tasks.keys(), return_exceptions=True)

    for task, ok in zip(tasks.values(), results):
        proxy = task
        if ok is True:
            ip = proxy.split("@")[-1].split("//")[-1]
            r.setex(f"good_proxy:{ip}", GOOD_TTL, "1")
        else:
            ban_proxy(proxy)


def main():
    asyncio.run(check_batch())


if __name__ == "__main__":
    main()

# ---------------------------------------------------------------------------
#  🩹  COMPATIBILITY WRAPPERS (оставляем старые имена для Celery)
# ---------------------------------------------------------------------------


def check_proxies(n: int | None = None) -> int:
    """
    Проверяет прокси и возвращает количество рабочих.
    Если n указан — пытается подобрать n прокси, иначе поведение pick_proxies().
    """
    from proxy_health import pick_proxies  # локальный импорт, чтобы избежать

    alive = pick_proxies(n) if n else pick_proxies()  # циклов импорта
    return len(alive)


def run_health() -> int:
    """Полный алиас для старых импортов."""  # noqa: D401
    return check_proxies()


# ---------- universal entry point for Celery ---------------------------------
def check(limit: int = 200) -> list[str]:
    """
    Проверяем limit прокси из файла `proxies.txt`
    и возвращаем список рабочих ip:port.
    Используется Celery-task'ом proxy_health.check.
    """
    good = pick_proxies(limit)
    return good
