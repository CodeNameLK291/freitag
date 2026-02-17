"""메일 데이터베이스 모듈 - SQLite를 이용한 영구 저장"""

import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class MailRepository:
    """SQLite를 이용한 메일 저장소"""

    def __init__(self, db_path: str = "freitag.db") -> None:
        """
        메일 저장소 초기화

        Args:
            db_path: 데이터베이스 파일 경로
        """
        self.db_path = db_path
        self.init_db()

    def init_db(self) -> None:
        """데이터베이스 테이블 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # emails 테이블 생성
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS emails (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        message_id TEXT UNIQUE NOT NULL,
                        subject TEXT DEFAULT '',
                        sender TEXT DEFAULT '',
                        datetime_received TEXT NOT NULL,
                        body TEXT DEFAULT '',
                        is_read BOOLEAN DEFAULT 0,
                        has_attachments BOOLEAN DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # 인덱스 생성
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_datetime_received
                    ON emails(datetime_received)
                """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS idx_message_id
                    ON emails(message_id)
                """
                )

                conn.commit()
                logger.info(f"데이터베이스 초기화 완료: {self.db_path}")

        except sqlite3.Error as e:
            logger.error(f"데이터베이스 초기화 실패: {e}")
            raise

    def save_emails(self, emails: List[Dict[str, Any]]) -> int:
        """
        메일 일괄 저장

        Args:
            emails: 저장할 메일 딕셔너리 리스트

        Returns:
            저장된 메일 개수
        """
        if not emails:
            return 0

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                saved_count = 0

                for email in emails:
                    # datetime을 ISO 8601 형식으로 변환
                    datetime_received = email.get("datetime_received")
                    if isinstance(datetime_received, datetime):
                        datetime_str = datetime_received.isoformat()
                    else:
                        datetime_str = str(datetime_received)

                    try:
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO emails
                            (message_id, subject, sender, datetime_received, body, is_read, has_attachments)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                email.get("message_id", ""),
                                email.get("subject", ""),
                                email.get("sender", ""),
                                datetime_str,
                                email.get("body", ""),
                                1 if email.get("is_read", False) else 0,
                                1 if email.get("has_attachments", False) else 0,
                            ),
                        )

                        if cursor.rowcount > 0:
                            saved_count += 1

                    except sqlite3.IntegrityError:
                        # 이미 존재하는 메일은 무시
                        continue

                conn.commit()
                logger.info(f"{saved_count}개의 새 메일 저장 완료")
                return saved_count

        except sqlite3.Error as e:
            logger.error(f"메일 저장 실패: {e}")
            raise

    def get_all_emails(self) -> List[Dict[str, Any]]:
        """
        모든 메일 조회

        Returns:
            메일 딕셔너리 리스트 (datetime_received 내림차순)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT message_id, subject, sender, datetime_received,
                           body, is_read, has_attachments
                    FROM emails
                    ORDER BY datetime_received DESC
                """
                )

                rows = cursor.fetchall()
                emails = []

                for row in rows:
                    # datetime 문자열을 datetime 객체로 변환
                    datetime_str = row["datetime_received"]
                    try:
                        datetime_obj = datetime.fromisoformat(datetime_str)
                    except (ValueError, TypeError):
                        datetime_obj = None

                    emails.append(
                        {
                            "message_id": row["message_id"],
                            "subject": row["subject"],
                            "sender": row["sender"],
                            "datetime_received": datetime_obj,
                            "body": row["body"],
                            "is_read": bool(row["is_read"]),
                            "has_attachments": bool(row["has_attachments"]),
                        }
                    )

                logger.info(f"{len(emails)}개의 메일 로드 완료")
                return emails

        except sqlite3.Error as e:
            logger.error(f"메일 조회 실패: {e}")
            raise

    def get_latest_datetime(self) -> Optional[datetime]:
        """
        가장 최근 메일의 수신일 반환 (증분 동기화용)

        Returns:
            가장 최근 메일의 datetime_received, 없으면 None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    SELECT datetime_received
                    FROM emails
                    ORDER BY datetime_received DESC
                    LIMIT 1
                """
                )

                row = cursor.fetchone()

                if row and row[0]:
                    try:
                        return datetime.fromisoformat(row[0])
                    except (ValueError, TypeError):
                        return None

                return None

        except sqlite3.Error as e:
            logger.error(f"최근 메일 날짜 조회 실패: {e}")
            raise

    def get_email_count(self) -> int:
        """
        저장된 메일 개수 반환

        Returns:
            메일 개수
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM emails")
                count = cursor.fetchone()[0]
                return count

        except sqlite3.Error as e:
            logger.error(f"메일 개수 조회 실패: {e}")
            raise

    def clear_all_emails(self) -> None:
        """
        모든 메일 삭제 (테스트용)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM emails")
                conn.commit()
                logger.info("모든 메일 삭제 완료")

        except sqlite3.Error as e:
            logger.error(f"메일 삭제 실패: {e}")
            raise
