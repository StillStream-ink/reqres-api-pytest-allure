import logging
import os

def get_logger():
    logger = logging.getLogger("reqres_api")
    logger.setLevel(logging.INFO)
    # 避免重复添加handler
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

logger = get_logger()
