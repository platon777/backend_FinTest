import logging
import sys
from pathlib import Path
from app.core.config import settings

# Create logs directory if it doesn't exist
log_dir = Path(settings.LOG_FILE).parent
log_dir.mkdir(parents=True, exist_ok=True)


def setup_logger(name: str = __name__) -> logging.Logger:
    """Setup and configure logger."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # Create formatters
    if settings.LOG_FORMAT == "json":
        formatter = logging.Formatter(
            '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(settings.LOG_FILE)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


# Create default logger
logger = setup_logger("fintest_api")
