import asyncio, importlib

ph = importlib.import_module("app.proxy_health_v2")

async def _run():
    # берём первые 10 прокси из файла
    with open("proxies.txt") as fh:
        sample = [p.strip() for p in fh.readlines()[:10]]
    # фейковый список вместо чтения файла внутри check()
    alive = [p for p, rtt in await asyncio.gather(*(ph._probe(p) for p in sample)) if rtt]
    # не все прокси помрут
    assert len(alive) >= 1, "all probes failed"

def test_probe_event_loop():
    asyncio.run(_run())
