"""main_window 모듈 테스트"""

import os

# PyQt5 테스트를 위한 headless 설정
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from unittest.mock import Mock, patch  # noqa: E402
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


def test_main_window_creation(qapp) -> None:
    """메인 윈도우 생성 테스트"""
    window = MainWindow()
    assert window is not None
    assert window.windowTitle() == "Freitag - Exchange 메일 뷰어"


def test_main_window_ui_elements(qapp) -> None:
    """UI 요소 존재 확인"""
    window = MainWindow()
    assert window.mail_list is not None
    assert window.mail_viewer is not None
    assert window.statusBar is not None


@patch("src.ui.main_window.QMessageBox")
@patch("src.ui.main_window.ExchangeClient")
def test_connect_to_server(mock_client, mock_msgbox, qapp) -> None:
    """서버 연결 테스트"""
    window = MainWindow()

    mock_instance = Mock()
    mock_instance.connect.return_value = True
    mock_instance.is_connected.return_value = True
    mock_client.return_value = mock_instance

    window.connect_to_server()

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
