import logging
import uuid
from pythonjsonlogger import jsonlogger


def init_logging(service: str):
    handler = logging.StreamHandler()
    fmt = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s trace_id"
    )
    handler.setFormatter(fmt)
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    # добавляем фильтр с trace_id (uuid4 на каждый emit)
    class TraceFilter(logging.Filter):
        def filter(self, record):
            record.trace_id = uuid.uuid4().hex
            return True

    root.addFilter(TraceFilter())
    logging.getLogger(service).info("logger_init", extra={"service": service})
