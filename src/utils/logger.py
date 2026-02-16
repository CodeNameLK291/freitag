"""로깅 설정 모듈"""

import logging
import sys


def setup_logger(name: str = "freitag", level: int = logging.INFO) -> logging.Logger:
    """로거를 설정하고 반환

    Args:
        name: 로거 이름
        level: 로깅 레벨

    Returns:
        설정된 로거 객체
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 이미 핸들러가 있으면 추가하지 않음
    if logger.handlers:
        return logger

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # 포맷터
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    return logger
