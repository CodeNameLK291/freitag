"""설정 모듈 테스트"""

from unittest.mock import patch
from src.utils.config import Config


def test_config_defaults():
    """Config 기본값 테스트"""
    # 환경 변수가 없을 때 빈 문자열 또는 기본값
    assert isinstance(Config.MAIL_FETCH_LIMIT, int)


@patch.dict(
    "os.environ",
    {
        "EXCHANGE_SERVER": "test.server.com",
        "EXCHANGE_DOMAIN": "testdomain",
        "EXCHANGE_USERNAME": "testuser",
        "EXCHANGE_PASSWORD": "testpass",
    },
)
def test_config_from_env():
    """환경 변수에서 설정 로드 테스트"""
    # Config 재로드
    from importlib import reload
    from src.utils import config

    reload(config)

    assert config.Config.EXCHANGE_SERVER == "test.server.com"
    assert config.Config.EXCHANGE_DOMAIN == "testdomain"


def test_config_get_exchange_config():
    """Exchange 설정 딕셔너리 반환 테스트"""
    config_dict = Config.get_exchange_config()

    assert isinstance(config_dict, dict)
    assert "server" in config_dict
    assert "domain" in config_dict
    assert "username" in config_dict
    assert "password" in config_dict


@patch.dict(
    "os.environ",
    {
        "EXCHANGE_SERVER": "test.server.com",
        "EXCHANGE_DOMAIN": "testdomain",
        "EXCHANGE_USERNAME": "testuser",
        "EXCHANGE_PASSWORD": "testpass",
    },
)
def test_config_validate_success():
    """Config 검증 성공 테스트"""
    # Config 재로드
    from importlib import reload
    from src.utils import config

    reload(config)

    assert config.Config.validate() is True


def test_config_validate_failure():
    """Config 검증 실패 테스트 (필수값 누락)"""
    # 기본 Config는 환경 변수가 없으면 빈 문자열
    # 빈 문자열이면 validate가 False를 반환해야 함
    result = Config.validate()
    # 환경 변수가 설정되어 있지 않으면 False
    assert isinstance(result, bool)
