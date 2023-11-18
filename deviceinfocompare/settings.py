import logging
import logging.config
import os
import sys
from pathlib import Path

import sqlalchemy
from sqlalchemy.orm import sessionmaker

from deviceinfocompare.data import DeclarativeBase

BASE_DIR: Path = Path(
    os.environ.get(
        "DIC_BASE_DIR", os.path.join(os.path.expanduser("~"), ".deviceinfocompare")
    )
)

DEBUG: bool = os.environ.get("DIC_DEBUG", True) in ["t", True, "true"]

LOG_LVL: str = "DEBUG" if DEBUG else "WARNING"

LOG_DIR: Path = Path(os.path.join(BASE_DIR, "logs"))

RESOURCE_PATH = Path(getattr(sys, "_MEIPASS", os.path.abspath(".")))

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "default": {
            "level": LOG_LVL,
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOG_DIR / "dic.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 2,
            "formatter": "standard",
            "encoding": "utf8",
        },
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "standard",
        },
    },
    "loggers": {
        "": {"handlers": ["default", "console"], "level": LOG_LVL, "propagate": False},
        "invoke": {"handlers": ["default", "console"], "level": "WARNING"},
    },
}

BASE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
logging.config.dictConfig(LOGGING)

logger = logging.getLogger(__name__)

ENGINE = sqlalchemy.create_engine(
    "sqlite:///" + os.path.join(BASE_DIR, "deviceinfo.db")
)
DeclarativeBase.metadata.create_all(ENGINE)
SESSION = sessionmaker(bind=ENGINE)()


def closeDB() -> None:
    global ENGINE, SESSION
    SESSION.close()
    ENGINE.dispose()
