import logging
from app.tor_control import renew
from app.browser_core import fetch_html as _core      # оригинальная реализация

log = logging.getLogger("browser")

async def fetch_html(url: str, max_retries: int = 3) -> str:
    """
    HTML с повторными попытками и сменой Tor-экзита.
    ▸ 3 попытки через текущий circuit;
    ▸ после 3-й ошибки — NEWNYM + финальный четвёртый запрос.
    """
    for attempt in range(1, max_retries + 1):
        try:
            return await _core(url)
        except Exception as err:
            log.warning("attempt %s/%s %s — %s", attempt, max_retries, url, err)

    # три неудачи — меняем цепочку Tor и делаем ещё один запрос
    renew()
    log.info("Tor circuit renewed, final retry for %s", url)
    return await _core(url)
