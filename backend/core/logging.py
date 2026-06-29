import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from core.config import settings


def configure_logging() -> logging.Logger:
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("resume_analyzer")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        handler = TimedRotatingFileHandler(
            log_dir / "app.log",
            when="midnight",
            backupCount=30,
            encoding="utf-8",
        )
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s %(message)s"
            )
        )
        logger.addHandler(handler)

    return logger


logger = configure_logging()
