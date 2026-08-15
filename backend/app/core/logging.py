import logging
from logging.config import dictConfig


def setup_logging(*, debug: bool) -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                }
            },
            "root": {
                "level": "DEBUG" if debug else "INFO",
                "handlers": ["console"],
            },
            "loggers": {
                "uvicorn": {"level": "INFO", "propagate": True},
                "sqlalchemy.engine": {
                    "level": "WARNING",
                    "propagate": True,
                },
            },
        }
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
