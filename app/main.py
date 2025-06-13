from app.log_config import init_logging

init_logging(__name__)
from fastapi import FastAPI, Response
from prometheus_client import (
    Counter,
    Gauge,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
import redis
from app.health import health_summary
from app.domain_limiter import throttle
import logging
import backoff
from fastapi import HTTPException
from pydantic import BaseModel, HttpUrl

from app.cache import cached_fetch_html
from app.extract import smart_extract

logging.basicConfig(level=logging.INFO)
registry = CollectorRegistry()
scrape_success = Counter(
    "scrape_success_total", "Successful /scrape requests", registry=registry
)
proxy_good = Gauge("proxy_good_total", "Good proxies in Redis", registry=registry)

api = FastAPI(title="AIDA Super Scraper")


@api.get("/metrics")
async def metrics():
    r = redis.Redis(host="redis", decode_responses=True)
    proxy_good.set(len(r.keys("good_proxy:*")))
    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)


class Req(BaseModel):
    url: HttpUrl


@api.post("/scrape")
@backoff.on_exception(backoff.expo, Exception, max_time=60)
async def scrape(req: Req):
    scrape_success.inc()
    await throttle(str(req.url))
    try:
        html = await cached_fetch_html(str(req.url))
        data = smart_extract(str(req.url), html)
        return {"status": "ok", "data": data}
    except Exception as e:
        logging.exception("scrape failed")
        raise HTTPException(status_code=500, detail=str(e))


@api.get("/health")
async def health():
    return await health_summary()
