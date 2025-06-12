from app.log_config import init_logging
init_logging(__name__)
import random, pathlib, os

BASE = pathlib.Path("/app")   # контейнерный путь
UA_FILE   = os.getenv("UA_FILE",   BASE / "ua_list.txt")
LANG_FILE = os.getenv("LANG_FILE", BASE / "lang_list.txt")

VIEWPORTS = [
    (1366, 768),   # ноут
    (1440, 900),   # MacBook 13
    (1536, 864),
    (1680, 1050),
    (1920, 1080),  # Full HD
]

def _load(file):
    p = pathlib.Path(file)
    return [l.strip() for l in p.read_text().splitlines() if l.strip() and not l.startswith("#")]

UA_LIST   = _load(UA_FILE)
LANG_LIST = _load(LANG_FILE)

def random_profile():
    return {
        "user_agent": random.choice(UA_LIST),
        "locale":     random.choice(LANG_LIST).split(",")[0],
        "extra_headers": {"Accept-Language": random.choice(LANG_LIST)},
        "viewport":   dict(zip(("width","height"), random.choice(VIEWPORTS))),
    }
