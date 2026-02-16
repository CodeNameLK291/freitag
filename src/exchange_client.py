"""Exchange 메일 서버 연동 모듈"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from exchangelib import (
    Credentials,
    Account,
    Configuration,
    DELEGATE,
    Message,
)
from exchangelib.errors import UnauthorizedError, TransportError
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class ExchangeClient:
    """Exchange 메일 서버 클라이언트"""

    def __init__(
        self,
        server: Optional[str] = None,
        domain: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        email: Optional[str] = None,
    ):
        """Exchange 클라이언트 초기화

        Args:
            server: Exchange 서버 주소
            domain: 도메인
            username: 사용자명
            password: 비밀번호
            email: 이메일 주소 (선택적, 없으면 자동 생성)
        """
        self.server = server or Config.EXCHANGE_SERVER
        self.domain = domain or Config.EXCHANGE_DOMAIN
        self.username = username or Config.EXCHANGE_USERNAME
        self.password = password or Config.EXCHANGE_PASSWORD
        self.email = email or Config.EXCHANGE_EMAIL

        self.account: Optional[Account] = None
        self._connected = False

    def connect(self) -> bool:
        """Exchange 서버에 연결

        Returns:
            연결 성공 여부

        Raises:
            UnauthorizedError: 인증 실패
            TransportError: 네트워크 에러
        """
        try:
            logger.info(f"Exchange 서버 연결 시도: {self.server}")

            # 자격 증명 생성
            if self.domain:
                email = f"{self.domain}\\{self.username}"
            else:
                email = self.username

            credentials = Credentials(username=email, password=self.password)

            # 서버 설정
            config = Configuration(server=self.server, credentials=credentials)

            # 계정 연결 - 이메일 주소 결정
            if self.email:
                # 명시적으로 제공된 이메일 주소 사용
                smtp_address = self.email
            else:
                # 자동 생성: username@domain (서버에서 'outlook.' 제거)
                domain_part = self.server.replace("outlook.", "")
                smtp_address = f"{self.username}@{domain_part}"

            self.account = Account(
                primary_smtp_address=smtp_address,
                config=config,
                autodiscover=False,
                access_type=DELEGATE,
            )

            # 연결 테스트 (받은편지함 접근)
            _ = self.account.inbox.total_count

            self._connected = True
            logger.info("Exchange 서버 연결 성공")
            return True

        except UnauthorizedError as e:
            logger.error(f"인증 실패: {e}")
            self._connected = False
            raise
        except TransportError as e:
            logger.error(f"네트워크 에러: {e}")
            self._connected = False
            raise
        except Exception as e:
            logger.error(f"연결 실패: {e}")
            self._connected = False
            raise

    def is_connected(self) -> bool:
        """연결 상태 확인"""
        return self._connected and self.account is not None

    def get_inbox_messages(
        self,
        limit: int = 50,
        days_back: int = 7,
    ) -> List[Dict[str, Any]]:
        """받은편지함에서 메일 가져오기

        Args:
            limit: 가져올 메일 개수
            days_back: 며칠 전까지의 메일을 가져올지

        Returns:
            메일 정보 딕셔너리 리스트
        """
        if not self.is_connected():
            raise ConnectionError("Exchange 서버에 연결되지 않음")

        try:
            logger.info(f"받은편지함에서 메일 가져오기 (최대 {limit}개)")

            # 날짜 필터
            start_date = datetime.now(timezone.utc) - timedelta(days=days_back)

            # 메일 쿼리
            messages = self.account.inbox.filter(datetime_received__gte=start_date).order_by(
                "-datetime_received"
            )[:limit]

            # 메일 정보 추출
            mail_list = []
            for msg in messages:
                mail_info = self._extract_message_info(msg)
                mail_list.append(mail_info)
                logger.debug(f"메일 추출: {mail_info['subject']}")

            logger.info(f"총 {len(mail_list)}개 메일 가져오기 완료")
            return mail_list

        except Exception as e:
            logger.error(f"메일 가져오기 실패: {e}")
            raise

    def _extract_message_info(self, message: Message) -> Dict[str, Any]:
        """메시지에서 필요한 정보 추출

        Args:
            message: Exchange 메시지 객체

        Returns:
            메일 정보 딕셔너리
        """
        return {
            "id": message.id,
            "subject": message.subject or "(제목 없음)",
            "sender": self._extract_email_address(message.sender),
            "sender_name": (
                getattr(message.sender, "name", "Unknown") if message.sender else "Unknown"
            ),
            "to_recipients": [
                self._extract_email_address(r) for r in (message.to_recipients or [])
            ],
            "cc_recipients": [
                self._extract_email_address(r) for r in (message.cc_recipients or [])
            ],
            "body": message.body or "",
            "text_body": message.text_body or "",
            "datetime_received": message.datetime_received,
            "datetime_sent": message.datetime_sent,
            "is_read": message.is_read,
            "importance": message.importance,
            "has_attachments": message.has_attachments,
            "attachment_count": len(message.attachments or []),
        }

    def _extract_email_address(self, mailbox) -> str:
        """Mailbox 객체에서 이메일 주소 추출"""
        if mailbox is None:
            return ""
        return getattr(mailbox, "email_address", str(mailbox))

    def get_folder_list(self) -> List[str]:
        """메일함 목록 가져오기

        Returns:
            폴더 이름 리스트
        """
        if not self.is_connected():
            raise ConnectionError("Exchange 서버에 연결되지 않음")

        try:
            folders = []
            for folder in self.account.inbox.parent.walk():
                folders.append(folder.name)
            return folders
        except Exception as e:
            logger.error(f"폴더 목록 가져오기 실패: {e}")
            raise

    def disconnect(self) -> None:
        """연결 종료"""
        if self.account:
            self.account = None
            self._connected = False
            logger.info("Exchange 서버 연결 종료")
