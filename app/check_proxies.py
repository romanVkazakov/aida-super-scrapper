import asyncio
import aiohttp
import ssl
import pathlib

PROXIES_FILE = "/app/proxies.txt"
OUTPUT_FILE = "/app/good_proxies.txt"

# Загружаем список прокси
p = pathlib.Path(PROXIES_FILE)
if not p.exists():
    print("Файл proxies.txt не найден.")
    exit(1)
with open(PROXIES_FILE, "r") as f:
    proxies = [line.strip() for line in f if line.strip()]


async def test_proxy(proxy: str) -> bool:
    test_url = "http://httpbin.org/ip"
    conn = aiohttp.TCPConnector(ssl=ssl.create_default_context())
    try:
        # Если прокси в формате "http://IP:PORT" → используем его напрямую
        async with aiohttp.ClientSession(connector=conn) as session:
            async with session.get(test_url, proxy=proxy, timeout=15) as resp:
                return resp.status == 200
    except:
        return False


async def run_tests(all_proxies):
    tasks = [asyncio.create_task(test_proxy(p)) for p in all_proxies]
    results = await asyncio.gather(*tasks)
    # возвращаем только те прокси, которые прошли
    return [p for p, ok in zip(all_proxies, results) if ok]


def main():
    working = asyncio.run(run_tests(proxies))
    if working:
        with open(OUTPUT_FILE, "w") as out:
            for w in working:
                out.write(w + "\\n")
        print(f"Найдено {len(working)} рабочих прокси. Сохранено в {OUTPUT_FILE}.")
    else:
        print("Не удалось найти ни одного рабочего прокси.")


if __name__ == "__main__":
    main()
