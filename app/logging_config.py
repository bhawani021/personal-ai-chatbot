import logging
from pathlib import Path


def configure_logging(level=logging.INFO):
    log_directory = Path("logs")
    log_directory.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=level,
        format=("%(asctime)s | %(levelname)s | " "%(name)s | %(message)s"),
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                log_directory / "chatbot.log",
                encoding="utf-8",
            ),
        ],
        force=True,
    )
