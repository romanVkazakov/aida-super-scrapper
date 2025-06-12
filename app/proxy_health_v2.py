import asyncio, httpx, time, ipaddress, redis

# ─────────── настройки ────────────────────────────────────────────────────────
CHECK_URL       = "http://example.com/ping"
CONCURRENCY     = 300          # сколько одновременных проверок
TIMEOUT         = 4            # секунд на один запрос
GOOD_LIMIT      = 300          # в Redis оставляем не больше N лучших
TTL_MIN, TTL_MAX = 300, 3600   # границы адаптивного TTL (сек)

r         = redis.Redis(host="redis", decode_responses=True)
PRIV_NETS = [ipaddress.ip_network(net) for net in
             ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
              "169.254.0.0/16", "127.0.0.0/8")]

# ─────────── вспомогалки ──────────────────────────────────────────────────────
def _is_private(proxy: str) -> bool:
    try:
        ip = ipaddress.ip_address(proxy.split(":")[0])
        return any(ip in net for net in PRIV_NETS)
    except ValueError:
        return True

async def _probe(proxy: str) -> tuple[str, float | None]:
    """возвращает (proxy, rtt_ms)  или (proxy, None) если умер"""
    start = time.perf_counter()
    try:
        async with httpx.AsyncClient(
                proxies=f"http://{proxy}", timeout=TIMEOUT) as c:
            await c.get(CHECK_URL)
        return proxy, (time.perf_counter() - start) * 1_000
    except Exception:
        return proxy, None

# ─────────── публичная точка входа ────────────────────────────────────────────
async def check(limit: int = GOOD_LIMIT) -> None:
    """Обновляет Redis ключами good_proxy:<ip:port> → RTT (мс)"""
    # 1. читаем список
    with open("proxies.txt") as fh:
        raw = [p.strip() for p in fh if p.strip()]
    raw = [p for p in raw if p != "0.0.0.0" and not _is_private(p)]

    # 2. пуляем проверки пачками
    sem = asyncio.Semaphore(CONCURRENCY)
    async def worker(p):
        async with sem:
            return await _probe(p)
    alive = [res async for res in asyncio.as_completed(map(worker, raw))]

    # 3. фильтруем, сортируем по RTT
    alive = [(p, rtt) for p, rtt in await asyncio.gather(*alive) if rtt]
    alive.sort(key=lambda t: t[1])          # fastest first

    # 4. пишем в Redis c адаптивным TTL
    for proxy, rtt in alive[:limit]:
        ttl = max(TTL_MIN, min(TTL_MAX, int(rtt * 0.6)))
        r.setex(f"good_proxy:{proxy}", ttl, int(rtt))

    # 5. чистим избыток, если ключей > limit
    keys = r.keys("good_proxy:*")
    if len(keys) > limit:
        # отсортируем по сохранённому rtt и дропнем хвост
        keys_sorted = sorted(keys, key=lambda k: int(r.get(k)))
        r.delete(*keys_sorted[limit:])
