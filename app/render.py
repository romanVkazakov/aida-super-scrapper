import asyncio
from fastapi import FastAPI, HTTPException, Query
from prometheus_client import Counter, Gauge, CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
import redis
from playwright.async_api import async_playwright

registry = CollectorRegistry()
scrape_success = Counter('scrape_success_total','Successful /scrape requests',registry=registry)
proxy_good = Gauge('proxy_good_total','Good proxies in Redis',registry=registry)

app = FastAPI()
@app.get('/metrics')
async def metrics():
    r = redis.Redis(host='redis', decode_responses=True)
    proxy_good.set(len(r.keys('good_proxy:*')))
    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)


async def _snapshot(url: str, timeout: int = 15000) -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page    = await browser.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=timeout)
            html = await page.content()
        finally:
            await browser.close()
    return html

@app.get("/render")
async def render(url: str = Query(..., min_length=5)):
    try:
        html = await _snapshot(url)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return {"url": url, "html": html}
