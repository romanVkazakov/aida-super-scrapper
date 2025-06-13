import aiohttp
import logging

log = logging.getLogger("browser_core")
TIMEOUT = aiohttp.ClientTimeout(total=20)


async def fetch_html(url: str) -> str:
    """
    Лёгкая загрузка HTML через aiohttp (SSL off для Tor).
    Playwright можно вернуть потом, сейчас главное — чтобы не падало.
    """
    async with aiohttp.ClientSession(timeout=TIMEOUT) as s:
        async with s.get(url, ssl=False) as r:
            r.raise_for_status()
            html = await r.text()
            log.info("fetched %s (%d bytes)", url, len(html))
            return html
