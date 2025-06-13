from app.log_config import init_logging

init_logging(__name__)
import random
import redis
import os

# URL до Redis (в docker-compose у вас redis:6379)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
r = redis.from_url(REDIS_URL)

# Файл со списком прокси (по одному на строку, без комментариев)
PROXIES_FILE = "/app/proxies.txt"


def get_proxy():
    return None
    """
    Попытаться получить “хороший” прокси из Redis (ключи вида "good_proxy:<IP>:<port>");
    если в Redis ничего нет — выбрать случайный из proxies.txt;
    если и там нет — вернуть None (локальный IP).
    """
    try:
        # собрать все ключи good_proxy:*
        keys = list(r.scan_iter("good_proxy:*"))
        if keys:
            # формат ключей Redis: b"good_proxy:ip:port"
            good = [k.decode().split(":", 1)[1] for k in keys]
            return random.choice(good)
    except Exception:
        pass

    # fallback: случайный из файла proxies.txt
    try:
        with open(PROXIES_FILE, "r") as f:
            lines = [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
        if lines:
            return random.choice(lines)
    except Exception:
        pass

    return "socks5://tor:9050"


def ban_proxy(proxy):
    """
    Когда прокси оказался плохим, удаляем его из Redis.
    """
    try:
        # ключ в Redis: "good_proxy:<proxy>"
        r.delete(f"good_proxy:{proxy}")
    except Exception:
        pass
