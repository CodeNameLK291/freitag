"""main_window 모듈 테스트"""

import os
import tempfile

# PyQt5 테스트를 위한 headless 설정
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from unittest.mock import Mock, patch, MagicMock  # noqa: E402
import pytest  # noqa: E402
from PyQt5.QtWidgets import QApplication  # noqa: E402
from src.ui.main_window import MainWindow, EmailFetchThread  # noqa: E402


@pytest.fixture(scope="module")
def qapp():
    """QApplication 픽스처"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def temp_db():
    """임시 데이터베이스 픽스처"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


@patch("src.ui.main_window.MailRepository")
def test_main_window_creation(mock_repo, qapp) -> None:
    """메인 윈도우 생성 테스트"""
    mock_repo_instance = MagicMock()
    mock_repo_instance.get_all_emails.return_value = []
    mock_repo.return_value = mock_repo_instance

    window = MainWindow()
    assert window is not None
    assert window.windowTitle() == "Freitag - Exchange 메일 뷰어"


@patch("src.ui.main_window.MailRepository")
def test_main_window_ui_elements(mock_repo, qapp) -> None:
    """UI 요소 존재 확인"""
    mock_repo_instance = MagicMock()
    mock_repo_instance.get_all_emails.return_value = []
    mock_repo.return_value = mock_repo_instance

    window = MainWindow()
    assert window.mail_table is not None
    assert window.mail_viewer is not None
    assert window.statusBar is not None
    assert window.progress_bar is not None  # 프로그레스 바 확인


@patch("src.ui.main_window.MailRepository")
@patch("src.ui.main_window.QMessageBox")
@patch("src.ui.main_window.ExchangeClient")
def test_connect_to_server(mock_client, mock_msgbox, mock_repo, qapp) -> None:
    """서버 연결 테스트"""
    mock_repo_instance = MagicMock()
    mock_repo_instance.get_all_emails.return_value = []
    mock_repo_instance.get_latest_datetime.return_value = None
    mock_repo.return_value = mock_repo_instance

    window = MainWindow()

    mock_instance = Mock()
    mock_instance.connect.return_value = True
    mock_instance.is_connected.return_value = True
    mock_instance.get_inbox_messages.return_value = []
    mock_client.return_value = mock_instance

    window.connect_to_server()

    # 스레드의 run() 메서드를 직접 호출하여 동기적으로 테스트
    if window.connect_thread:
        window.connect_thread.run()

    assert window.client is not None
    mock_msgbox.information.assert_called_once()


def test_email_fetch_thread() -> None:
    """이메일 가져오기 스레드 테스트"""
    mock_client = Mock()
    mock_client.get_inbox_messages.return_value = [
        {"subject": "Test", "sender": "test@test.com"}
    ]

    thread = EmailFetchThread(mock_client)
    assert thread is not None

    # 스레드 실행 테스트
    finished_signal_received = []
    thread.finished.connect(lambda msgs: finished_signal_received.append(msgs))

    # run 메소드 직접 호출 (QThread.start() 대신)
    thread.run()

    # 신호가 올바른 데이터로 발생했는지 확인
    assert len(finished_signal_received) == 1
    assert finished_signal_received[0] == [
        {"subject": "Test", "sender": "test@test.com"}
    ]


def test_email_fetch_thread_with_progress() -> None:
    """이메일 가져오기 스레드 진행률 테스트"""
    mock_client = Mock()

    # progress_callback을 받아서 호출하는 함수
    def get_messages_with_progress(**kwargs):  # type: ignore
        callback = kwargs.get("progress_callback")
        if callback:
            callback(1, 2)
            callback(2, 2)
        return [
            {"subject": "Test 1", "sender": "test1@test.com"},
            {"subject": "Test 2", "sender": "test2@test.com"},
        ]

    mock_client.get_inbox_messages.side_effect = get_messages_with_progress

    thread = EmailFetchThread(mock_client, limit=None, days_back=None)

    # 진행률 신호 테스트
    progress_calls = []
    thread.progress.connect(lambda c, t: progress_calls.append((c, t)))

    finished_signal_received = []
    thread.finished.connect(lambda msgs: finished_signal_received.append(msgs))

    # run 메소드 직접 호출
    thread.run()

    # 진행률 신호가 발생했는지 확인
    assert len(progress_calls) == 2
    assert progress_calls[0] == (1, 2)
    assert progress_calls[1] == (2, 2)

    # 메일도 정상적으로 받았는지 확인
    assert len(finished_signal_received) == 1
    assert len(finished_signal_received[0]) == 2


def test_email_fetch_thread_error() -> None:
    """이메일 가져오기 스레드 에러 테스트"""
    mock_client = Mock()
    mock_client.get_inbox_messages.side_effect = Exception("Connection error")

    thread = EmailFetchThread(mock_client)

    # 에러 신호 테스트
    error_signal_received = []
    thread.error.connect(lambda err: error_signal_received.append(err))

    # run 메소드 직접 호출
    thread.run()

    # 에러 신호가 발생했는지 확인
    assert len(error_signal_received) == 1
    assert "Connection error" in error_signal_received[0]


def test_connect_thread() -> None:
    """서버 연결 스레드 테스트"""
    mock_client = Mock()
    mock_client.connect.return_value = True

    from src.ui.main_window import ConnectThread

    thread = ConnectThread(mock_client)
    assert thread is not None

    # 스레드 실행 테스트
    finished_signal_received = []
    thread.finished.connect(lambda success: finished_signal_received.append(success))

    # run 메소드 직접 호출
    thread.run()

    # 신호가 올바른 데이터로 발생했는지 확인
    assert len(finished_signal_received) == 1
    assert finished_signal_received[0] is True


def test_connect_thread_failure() -> None:
    """서버 연결 스레드 실패 테스트"""
    mock_client = Mock()
    mock_client.connect.return_value = False

    from src.ui.main_window import ConnectThread

    thread = ConnectThread(mock_client)

    # 신호 테스트
    finished_signal_received = []
    thread.finished.connect(lambda success: finished_signal_received.append(success))

    # run 메소드 직접 호출
    thread.run()

    # 신호가 실패로 발생했는지 확인
    assert len(finished_signal_received) == 1
    assert finished_signal_received[0] is False


def test_connect_thread_error() -> None:
    """서버 연결 스레드 에러 테스트"""
    mock_client = Mock()
    mock_client.connect.side_effect = Exception("Network error")

    from src.ui.main_window import ConnectThread

    thread = ConnectThread(mock_client)

    # 에러 신호 테스트
    error_signal_received = []
    thread.error.connect(lambda err: error_signal_received.append(err))

    finished_signal_received = []
    thread.finished.connect(lambda success: finished_signal_received.append(success))

    # run 메소드 직접 호출
    thread.run()

    # 에러 신호가 발생했는지 확인
    assert len(error_signal_received) == 1
    assert "Network error" in error_signal_received[0]

    # finished 신호도 False로 발생했는지 확인
    assert len(finished_signal_received) == 1
    assert finished_signal_received[0] is False


@patch("src.ui.main_window.MailRepository")
def test_mail_table_exists(mock_repo, qapp):
    """메일 테이블이 존재하는지 테스트"""
    mock_repo_instance = MagicMock()
    mock_repo_instance.get_all_emails.return_value = []
    mock_repo.return_value = mock_repo_instance

    window = MainWindow()
    assert hasattr(window, "mail_table")
    assert window.mail_table.columnCount() == 5


@patch("src.ui.main_window.MailRepository")
def test_mail_table_headers(mock_repo, qapp):
    """테이블 헤더 테스트"""
    mock_repo_instance = MagicMock()
    mock_repo_instance.get_all_emails.return_value = []
    mock_repo.return_value = mock_repo_instance

    window = MainWindow()
    headers = [window.mail_table.horizontalHeaderItem(i).text() for i in range(5)]
    assert "" in headers  # 읽음 상태
    assert "날짜" in headers
    assert "제목" in headers
    assert "보낸이" in headers
    assert "📎" in headers


@patch("src.ui.main_window.MailRepository")
def test_mail_table_population(mock_repo, qapp):
    """메일 데이터로 테이블 채우기 테스트"""
    from datetime import datetime, timezone

    mock_repo_instance = MagicMock()
    mock_repo_instance.get_all_emails.return_value = []
    mock_repo.return_value = mock_repo_instance

    window = MainWindow()

    mock_messages = [
        {
            "subject": "Test Email 1",
            "sender": "test1@example.com",
            "datetime_received": datetime.now(timezone.utc),
            "body": "Body 1",
            "has_attachments": True,
            "is_read": False,
        },
        {
            "subject": "Test Email 2",
            "sender": "test2@example.com",
            "datetime_received": datetime.now(timezone.utc),
            "body": "Body 2",
            "has_attachments": False,
            "is_read": True,
        },
    ]

    window.display_emails(mock_messages)

    assert window.mail_table.rowCount() == 2
    assert window.mail_table.item(0, 2).text() == "Test Email 1"
    assert window.mail_table.item(1, 2).text() == "Test Email 2"
    assert window.mail_table.item(0, 0).text() == "🔵"  # 안읽음
    assert window.mail_table.item(1, 0).text() == "⚪"  # 읽음


@patch("src.ui.main_window.MailRepository")
def test_load_emails_from_db(mock_repo, qapp):
    """DB에서 메일 로드 테스트"""
    from datetime import datetime, timezone

    mock_messages = [
        {
            "subject": "DB Email",
            "sender": "db@example.com",
            "datetime_received": datetime.now(timezone.utc),
            "body": "From DB",
            "has_attachments": False,
            "is_read": False,
        }
    ]

    mock_repo_instance = MagicMock()
    mock_repo_instance.get_all_emails.return_value = mock_messages
    mock_repo.return_value = mock_repo_instance

    window = MainWindow()

    # DB에서 로드된 메일이 있는지 확인
    assert len(window.messages) == 1
    assert window.messages[0]["subject"] == "DB Email"


@patch("src.ui.main_window.MailRepository")
def test_progress_bar_visibility(mock_repo, qapp):
    """프로그레스 바 표시 테스트"""
    mock_repo_instance = MagicMock()
    mock_repo_instance.get_all_emails.return_value = []
    mock_repo.return_value = mock_repo_instance

    window = MainWindow()

    # 초기에는 프로그레스 바가 숨겨져 있어야 함
    assert window.progress_bar.isVisible() is False


@patch("src.ui.main_window.MailRepository")
def test_progress_update(mock_repo, qapp):
    """프로그레스 바 업데이트 테스트"""
    mock_repo_instance = MagicMock()
    mock_repo_instance.get_all_emails.return_value = []
    mock_repo.return_value = mock_repo_instance

    window = MainWindow()

    # 프로그레스 업데이트 호출
    window.on_progress_update(5, 10)

    assert window.progress_bar.value() == 50
    assert "5/10" in window.progress_bar.format()


@patch("src.ui.main_window.MailRepository")
def test_on_emails_synced(mock_repo, qapp):
    """메일 동기화 완료 테스트"""
    from datetime import datetime, timezone

    new_messages = [
        {
            "message_id": "msg1",
            "subject": "New Email",
            "sender": "new@example.com",
            "datetime_received": datetime.now(timezone.utc),
            "body": "New",
            "has_attachments": False,
            "is_read": False,
        }
    ]

    all_messages = new_messages.copy()

    mock_repo_instance = MagicMock()
    mock_repo_instance.get_all_emails.return_value = []
    mock_repo_instance.save_emails.return_value = 1
    mock_repo.return_value = mock_repo_instance

    window = MainWindow()

    # DB에서 전체 메일을 반환하도록 설정
    mock_repo_instance.get_all_emails.return_value = all_messages

    window.on_emails_synced(new_messages)

    # save_emails가 호출되었는지 확인
    mock_repo_instance.save_emails.assert_called_once_with(new_messages)

    # 메일이 로드되었는지 확인
    assert len(window.messages) == 1
    assert window.messages[0]["subject"] == "New Email"
