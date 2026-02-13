"""로거 모듈 테스트"""

import logging
from src.utils.logger import setup_logger


def test_setup_logger_default():
    """기본 로거 설정 테스트"""
    logger = setup_logger()

    assert logger.name == "freitag"
    assert logger.level == logging.INFO
    assert len(logger.handlers) > 0


def test_setup_logger_custom_name():
    """커스텀 이름으로 로거 설정 테스트"""
    logger = setup_logger(name="test_logger")

    assert logger.name == "test_logger"
    assert len(logger.handlers) > 0


def test_setup_logger_custom_level():
    """커스텀 레벨로 로거 설정 테스트"""
    logger = setup_logger(name="test_logger_debug", level=logging.DEBUG)

    assert logger.level == logging.DEBUG


def test_setup_logger_idempotent():
    """로거 설정이 멱등성을 가지는지 테스트"""
    logger1 = setup_logger(name="test_logger_idem")
    handler_count1 = len(logger1.handlers)

    logger2 = setup_logger(name="test_logger_idem")
    handler_count2 = len(logger2.handlers)

    # 같은 이름으로 다시 설정해도 핸들러가 추가되지 않음
    assert handler_count1 == handler_count2
    assert logger1 is logger2
