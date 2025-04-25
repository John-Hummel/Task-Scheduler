# core/logger.py
import logging
from datetime import datetime, timedelta
from pathlib import Path

basepath = Path(__file__).resolve().parent

LOG_DIR = "logs"
log_dir_path = basepath / LOG_DIR
log_dir_path.mkdir(exist_ok=True)

LOG_RETENTION_DAYS = 4

# Configure daily rotating log file
log_filename = log_dir_path / f"{datetime.now().strftime('%Y-%m-%d')}.log"
logger = logging.getLogger("task_logger")
logger.setLevel(logging.DEBUG)
log_formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")

file_handler = logging.FileHandler(log_filename)
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

# FIFO deletion of logs older than 4 days
def cleanup_old_logs():
    cutoff = datetime.now() - timedelta(days=LOG_RETENTION_DAYS)
    for log_file in log_dir_path.glob("*.log"):
        try:
            file_date = datetime.strptime(log_file.stem, "%Y-%m-%d")
            if file_date < cutoff:
                log_file.unlink()
        except ValueError:
            continue

cleanup_old_logs()

def log(level: str, message: str):
    if level.lower() == "debug":
        logger.debug(message)
    elif level.lower() == "info":
        logger.info(message)
    elif level.lower() == "warning":
        logger.warning(message)
    elif level.lower() == "error":
        logger.error(message)
    elif level.lower() == "critical":
        logger.critical(message)
    else:
        logger.info(message)
