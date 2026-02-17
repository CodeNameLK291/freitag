"""mail_db 모듈 테스트"""

import os
import tempfile
import pytest
from datetime import datetime, timezone, timedelta
from src.mail_db import MailRepository


@pytest.fixture
def temp_db():
    """임시 데이터베이스 픽스처"""
    # 임시 파일 생성
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    yield path

    # 테스트 후 삭제
    if os.path.exists(path):
        os.remove(path)


def test_mail_repository_init(temp_db):
    """MailRepository 초기화 테스트"""
    repo = MailRepository(temp_db)
    assert repo is not None
    assert repo.db_path == temp_db
    assert os.path.exists(temp_db)


def test_init_db_creates_tables(temp_db):
    """데이터베이스 테이블 생성 테스트"""
    repo = MailRepository(temp_db)

    # 테이블 존재 확인
    import sqlite3

    with sqlite3.connect(temp_db) as conn:
        cursor = conn.cursor()

        # emails 테이블 확인
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='emails'"
        )
        assert cursor.fetchone() is not None

        # 인덱스 확인
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_datetime_received'"
        )
        assert cursor.fetchone() is not None

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_message_id'"
        )
        assert cursor.fetchone() is not None


def test_save_emails_empty_list(temp_db):
    """빈 리스트 저장 테스트"""
    repo = MailRepository(temp_db)
    count = repo.save_emails([])
    assert count == 0


def test_save_emails_single_email(temp_db):
    """단일 메일 저장 테스트"""
    repo = MailRepository(temp_db)

    email = {
        "message_id": "msg123",
        "subject": "Test Email",
        "sender": "test@example.com",
        "datetime_received": datetime.now(timezone.utc),
        "body": "Test body",
        "is_read": False,
        "has_attachments": True,
    }

    count = repo.save_emails([email])
    assert count == 1


def test_save_emails_multiple_emails(temp_db):
    """여러 메일 저장 테스트"""
    repo = MailRepository(temp_db)

    emails = [
        {
            "message_id": f"msg{i}",
            "subject": f"Test Email {i}",
            "sender": f"test{i}@example.com",
            "datetime_received": datetime.now(timezone.utc) + timedelta(hours=i),
            "body": f"Test body {i}",
            "is_read": i % 2 == 0,
            "has_attachments": i % 3 == 0,
        }
        for i in range(5)
    ]

    count = repo.save_emails(emails)
    assert count == 5


def test_save_emails_duplicate_prevention(temp_db):
    """중복 메일 방지 테스트"""
    repo = MailRepository(temp_db)

    email = {
        "message_id": "msg_duplicate",
        "subject": "Test Email",
        "sender": "test@example.com",
        "datetime_received": datetime.now(timezone.utc),
        "body": "Test body",
        "is_read": False,
        "has_attachments": False,
    }

    # 첫 번째 저장
    count1 = repo.save_emails([email])
    assert count1 == 1

    # 같은 message_id로 다시 저장 시도
    count2 = repo.save_emails([email])
    assert count2 == 0  # 중복이므로 저장되지 않음


def test_get_all_emails_empty(temp_db):
    """빈 데이터베이스에서 메일 조회 테스트"""
    repo = MailRepository(temp_db)
    emails = repo.get_all_emails()
    assert emails == []


def test_get_all_emails_with_data(temp_db):
    """메일 조회 테스트"""
    repo = MailRepository(temp_db)

    # 메일 저장
    test_emails = [
        {
            "message_id": "msg1",
            "subject": "Email 1",
            "sender": "sender1@example.com",
            "datetime_received": datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            "body": "Body 1",
            "is_read": False,
            "has_attachments": True,
        },
        {
            "message_id": "msg2",
            "subject": "Email 2",
            "sender": "sender2@example.com",
            "datetime_received": datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc),
            "body": "Body 2",
            "is_read": True,
            "has_attachments": False,
        },
    ]

    repo.save_emails(test_emails)

    # 메일 조회
    retrieved = repo.get_all_emails()

    assert len(retrieved) == 2
    # 날짜 내림차순 정렬 확인 (최신순)
    assert retrieved[0]["message_id"] == "msg2"
    assert retrieved[1]["message_id"] == "msg1"
    assert retrieved[0]["subject"] == "Email 2"
    assert retrieved[1]["subject"] == "Email 1"


def test_get_latest_datetime_empty(temp_db):
    """빈 데이터베이스에서 최근 날짜 조회 테스트"""
    repo = MailRepository(temp_db)
    latest = repo.get_latest_datetime()
    assert latest is None


def test_get_latest_datetime_with_data(temp_db):
    """최근 메일 날짜 조회 테스트"""
    repo = MailRepository(temp_db)

    # 여러 메일 저장
    dt1 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    dt2 = datetime(2024, 1, 3, 12, 0, 0, tzinfo=timezone.utc)
    dt3 = datetime(2024, 1, 2, 12, 0, 0, tzinfo=timezone.utc)

    emails = [
        {
            "message_id": "msg1",
            "subject": "Email 1",
            "sender": "test@example.com",
            "datetime_received": dt1,
            "body": "Body 1",
            "is_read": False,
            "has_attachments": False,
        },
        {
            "message_id": "msg2",
            "subject": "Email 2",
            "sender": "test@example.com",
            "datetime_received": dt2,
            "body": "Body 2",
            "is_read": False,
            "has_attachments": False,
        },
        {
            "message_id": "msg3",
            "subject": "Email 3",
            "sender": "test@example.com",
            "datetime_received": dt3,
            "body": "Body 3",
            "is_read": False,
            "has_attachments": False,
        },
    ]

    repo.save_emails(emails)

    # 최근 날짜 조회
    latest = repo.get_latest_datetime()
    assert latest is not None
    assert latest == dt2  # 가장 최근 날짜


def test_get_email_count_empty(temp_db):
    """빈 데이터베이스 메일 개수 테스트"""
    repo = MailRepository(temp_db)
    count = repo.get_email_count()
    assert count == 0


def test_get_email_count_with_data(temp_db):
    """메일 개수 조회 테스트"""
    repo = MailRepository(temp_db)

    emails = [
        {
            "message_id": f"msg{i}",
            "subject": f"Email {i}",
            "sender": "test@example.com",
            "datetime_received": datetime.now(timezone.utc),
            "body": f"Body {i}",
            "is_read": False,
            "has_attachments": False,
        }
        for i in range(10)
    ]

    repo.save_emails(emails)
    count = repo.get_email_count()
    assert count == 10


def test_clear_all_emails(temp_db):
    """모든 메일 삭제 테스트"""
    repo = MailRepository(temp_db)

    # 메일 저장
    emails = [
        {
            "message_id": f"msg{i}",
            "subject": f"Email {i}",
            "sender": "test@example.com",
            "datetime_received": datetime.now(timezone.utc),
            "body": f"Body {i}",
            "is_read": False,
            "has_attachments": False,
        }
        for i in range(5)
    ]

    repo.save_emails(emails)
    assert repo.get_email_count() == 5

    # 모든 메일 삭제
    repo.clear_all_emails()
    assert repo.get_email_count() == 0


def test_save_emails_with_missing_fields(temp_db):
    """필수 필드 없는 메일 저장 테스트"""
    repo = MailRepository(temp_db)

    # 일부 필드만 있는 메일
    email = {
        "message_id": "msg_partial",
        "datetime_received": datetime.now(timezone.utc),
    }

    count = repo.save_emails([email])
    assert count == 1

    # 조회하여 기본값 확인
    emails = repo.get_all_emails()
    assert len(emails) == 1
    assert emails[0]["subject"] == ""
    assert emails[0]["sender"] == ""
    assert emails[0]["body"] == ""
    assert emails[0]["is_read"] is False
    assert emails[0]["has_attachments"] is False


def test_datetime_conversion(temp_db):
    """datetime 변환 테스트"""
    repo = MailRepository(temp_db)

    # timezone-aware datetime
    dt_aware = datetime(2024, 5, 15, 10, 30, 45, tzinfo=timezone.utc)

    email = {
        "message_id": "msg_datetime",
        "subject": "Datetime Test",
        "sender": "test@example.com",
        "datetime_received": dt_aware,
        "body": "Test",
        "is_read": False,
        "has_attachments": False,
    }

    repo.save_emails([email])

    # 조회하여 datetime 확인
    emails = repo.get_all_emails()
    assert len(emails) == 1

    retrieved_dt = emails[0]["datetime_received"]
    assert isinstance(retrieved_dt, datetime)
    # timezone 정보는 손실될 수 있으므로 날짜/시간만 비교
    assert retrieved_dt.year == dt_aware.year
    assert retrieved_dt.month == dt_aware.month
    assert retrieved_dt.day == dt_aware.day
    assert retrieved_dt.hour == dt_aware.hour
    assert retrieved_dt.minute == dt_aware.minute


def test_save_emails_with_string_datetime(temp_db):
    """문자열 datetime 저장 테스트"""
    repo = MailRepository(temp_db)

    email = {
        "message_id": "msg_str_datetime",
        "subject": "String Datetime Test",
        "sender": "test@example.com",
        "datetime_received": "2024-05-15T10:30:45+00:00",
        "body": "Test",
        "is_read": False,
        "has_attachments": False,
    }

    count = repo.save_emails([email])
    assert count == 1

    # 조회하여 datetime 객체로 변환되었는지 확인
    emails = repo.get_all_emails()
    assert len(emails) == 1
    assert isinstance(emails[0]["datetime_received"], datetime)


def test_boolean_conversion(temp_db):
    """boolean 필드 변환 테스트"""
    repo = MailRepository(temp_db)

    emails = [
        {
            "message_id": "msg_bool1",
            "subject": "Test 1",
            "sender": "test@example.com",
            "datetime_received": datetime.now(timezone.utc),
            "body": "Test",
            "is_read": True,
            "has_attachments": True,
        },
        {
            "message_id": "msg_bool2",
            "subject": "Test 2",
            "sender": "test@example.com",
            "datetime_received": datetime.now(timezone.utc),
            "body": "Test",
            "is_read": False,
            "has_attachments": False,
        },
    ]

    repo.save_emails(emails)

    # 조회하여 boolean 확인
    retrieved = repo.get_all_emails()
    assert len(retrieved) == 2

    # 정렬 순서에 따라 확인
    email1 = next(e for e in retrieved if e["message_id"] == "msg_bool1")
    email2 = next(e for e in retrieved if e["message_id"] == "msg_bool2")

    assert email1["is_read"] is True
    assert email1["has_attachments"] is True
    assert email2["is_read"] is False
    assert email2["has_attachments"] is False
