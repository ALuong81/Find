import logging
import os

os.makedirs("data", exist_ok=True)

logging.basicConfig(
    filename="data/system_log.txt",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def log_info(msg):
    logging.info(msg)

def log_error(msg):
    logging.error(msg)
