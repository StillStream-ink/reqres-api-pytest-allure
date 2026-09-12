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

        os.makedirs("reports", exist_ok=True)
        fh = logging.FileHandler("reports/test_run.log", encoding="utf-8")
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger

logger = get_logger()
