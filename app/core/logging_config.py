import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import json as jsonlogger
from app.core.config import settings


def configure_logging():
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)

    formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )

    if settings.ENV == "development":
        handler = logging.StreamHandler(sys.stdout)
        log_level = "DEBUG" if settings.DEBUG else settings.LOG_LEVEL.upper()
    else:
        if settings.LOG_FILE_PATH:
            log_dir = os.path.dirname(settings.LOG_FILE_PATH)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

            handler = RotatingFileHandler(
                settings.LOG_FILE_PATH, maxBytes=10 * 1024 * 1024, backupCount=5  # 10 MB per file, 5 backups
            )
        else:
            handler = logging.StreamHandler(sys.stdout)

        log_level = settings.LOG_LEVEL.upper()

    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(log_level)

    if settings.ENV != "development":
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
