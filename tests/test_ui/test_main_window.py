"""main_window 모듈 테스트"""

from unittest.mock import Mock, patch
import pytest
from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow, EmailFetchThread


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


@patch('src.ui.main_window.ExchangeClient')
def test_connect_to_server(mock_client, qapp) -> None:
    """서버 연결 테스트"""
    window = MainWindow()
    
    mock_instance = Mock()
    mock_instance.connect.return_value = True
    mock_client.return_value = mock_instance
    
    window.connect_to_server()
    
    assert window.client is not None


def test_email_fetch_thread() -> None:
    """이메일 가져오기 스레드 테스트"""
    mock_client = Mock()
    mock_client.get_inbox_messages.return_value = [
        {'subject': 'Test', 'sender': 'test@test.com'}
    ]
    
    thread = EmailFetchThread(mock_client)
    assert thread is not None
