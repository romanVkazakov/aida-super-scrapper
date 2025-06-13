from app.log_config import init_logging

init_logging(__name__)
from app.settings import get_settings
import asyncio
import time
from urllib.parse import urlparse

# Словарь {домен: время последнего запроса}
_last_access = {}
# Минимальная задержка (секунд) между запросами к одному и тому же домену
MIN_DELAY = get_settings().MIN_DELAY


async def throttle(url: str):
    domain = urlparse(url).netloc
    now = time.time()
    last = _last_access.get(domain, 0)
    wait = MIN_DELAY - (now - last)
    if wait > 0:
        await asyncio.sleep(wait)
    _last_access[domain] = time.time()
