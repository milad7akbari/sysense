import logging
from pythonjsonlogger import jsonlogger
from app.core.config import settings

def configure_logging():
    root = logging.getLogger()
    # remove default handlers
    root.handlers = []

    if settings.DEBUG or settings.ENV == "development":
        handler = logging.StreamHandler()
        fmt = '%(asctime)s %(levelname)s %(name)s %(message)s'
        formatter = jsonlogger.JsonFormatter(fmt)
        handler.setFormatter(formatter)
        root.addHandler(handler)
        root.setLevel(logging.DEBUG)
    else:
        root.setLevel(logging.WARNING)
