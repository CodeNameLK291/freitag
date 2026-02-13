"""환경 변수 및 설정 관리 모듈"""

import os
from typing import Dict
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class Config:
    """애플리케이션 설정을 관리하는 클래스"""

    # Exchange 서버 설정
    EXCHANGE_SERVER: str = os.getenv("EXCHANGE_SERVER", "")
    EXCHANGE_DOMAIN: str = os.getenv("EXCHANGE_DOMAIN", "")
    EXCHANGE_USERNAME: str = os.getenv("EXCHANGE_USERNAME", "")
    EXCHANGE_PASSWORD: str = os.getenv("EXCHANGE_PASSWORD", "")
    EXCHANGE_EMAIL: str = os.getenv("EXCHANGE_EMAIL", "")  # 선택적 이메일 주소

    # 메일 설정
    MAIL_FETCH_LIMIT: int = int(os.getenv("MAIL_FETCH_LIMIT", "50"))

    @classmethod
    def validate(cls) -> bool:
        """필수 설정값이 모두 있는지 확인"""
        required = [
            cls.EXCHANGE_SERVER,
            cls.EXCHANGE_DOMAIN,
            cls.EXCHANGE_USERNAME,
            cls.EXCHANGE_PASSWORD,
        ]
        return all(required)

    @classmethod
    def get_exchange_config(cls) -> Dict[str, str]:
        """Exchange 설정을 딕셔너리로 반환"""
        return {
            "server": cls.EXCHANGE_SERVER,
            "domain": cls.EXCHANGE_DOMAIN,
            "username": cls.EXCHANGE_USERNAME,
            "password": cls.EXCHANGE_PASSWORD,
        }
