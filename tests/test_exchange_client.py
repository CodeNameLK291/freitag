"""Exchange 클라이언트 테스트"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from src.exchange_client import ExchangeClient
from exchangelib.errors import UnauthorizedError, TransportError


@pytest.fixture
def mock_config():
    """Mock 설정"""
    with patch("src.exchange_client.Config") as mock:
        mock.EXCHANGE_SERVER = "test.example.com"
        mock.EXCHANGE_DOMAIN = "testdomain"
        mock.EXCHANGE_USERNAME = "testuser"
        mock.EXCHANGE_PASSWORD = "testpass"
        yield mock


@pytest.fixture
def mock_account():
    """Mock Exchange Account"""
    with patch("src.exchange_client.Account") as mock:
        account_instance = MagicMock()
        account_instance.inbox.total_count = 10
        mock.return_value = account_instance
        yield account_instance


def test_exchange_client_init(mock_config):
    """ExchangeClient 초기화 테스트"""
    client = ExchangeClient()
    assert client.server == "test.example.com"
    assert client.username == "testuser"
    assert not client.is_connected()


def test_exchange_client_custom_init():
    """커스텀 설정으로 초기화 테스트"""
    client = ExchangeClient(
        server="custom.server.com", domain="custom", username="user", password="pass"
    )
    assert client.server == "custom.server.com"
    assert client.domain == "custom"


def test_exchange_client_with_email():
    """이메일 주소를 직접 제공한 초기화 테스트"""
    client = ExchangeClient(
        server="custom.server.com",
        domain="custom",
        username="user",
        password="pass",
        email="user@custom.com",
    )
    assert client.email == "user@custom.com"


@patch("src.exchange_client.Configuration")
@patch("src.exchange_client.Credentials")
@patch("src.exchange_client.Account")
def test_connect_with_email(mock_account_class, mock_credentials, mock_config_class, mock_config):
    """이메일 주소를 직접 제공한 경우 연결 테스트"""
    # Mock 설정
    mock_account_instance = MagicMock()
    mock_account_instance.inbox.total_count = 5
    mock_account_class.return_value = mock_account_instance

    client = ExchangeClient(email="test@example.com")
    result = client.connect()

    assert result is True
    assert client.is_connected()
    # Account가 제공된 이메일 주소로 호출되었는지 확인
    call_kwargs = mock_account_class.call_args.kwargs
    assert call_kwargs["primary_smtp_address"] == "test@example.com"


@patch("src.exchange_client.Configuration")
@patch("src.exchange_client.Credentials")
@patch("src.exchange_client.Account")
def test_connect_success(mock_account_class, mock_credentials, mock_config_class, mock_config):
    """연결 성공 테스트"""
    # Mock 설정
    mock_account_instance = MagicMock()
    mock_account_instance.inbox.total_count = 5
    mock_account_class.return_value = mock_account_instance

    client = ExchangeClient()
    result = client.connect()

    assert result is True
    assert client.is_connected()
    mock_credentials.assert_called_once()


@patch("src.exchange_client.Account")
def test_connect_unauthorized_error(mock_account, mock_config):
    """인증 실패 테스트"""
    mock_account.side_effect = UnauthorizedError("Invalid credentials")

    client = ExchangeClient()

    with pytest.raises(UnauthorizedError):
        client.connect()

    assert not client.is_connected()


def test_get_inbox_messages_not_connected(mock_config):
    """연결 안 된 상태에서 메일 가져오기 시도"""
    client = ExchangeClient()

    with pytest.raises(ConnectionError):
        client.get_inbox_messages()


@patch("src.exchange_client.Account")
def test_get_inbox_messages_success(mock_account_class, mock_config):
    """메일 가져오기 성공 테스트"""
    # Mock 메시지 생성
    mock_message = MagicMock()
    mock_message.id = "msg123"
    mock_message.subject = "Test Email"
    mock_message.sender.email_address = "sender@test.com"
    mock_message.sender.name = "Sender Name"
    mock_message.to_recipients = []
    mock_message.cc_recipients = []
    mock_message.body = "Test body"
    mock_message.text_body = "Test text body"
    mock_message.datetime_received = datetime.now(timezone.utc)
    mock_message.datetime_sent = datetime.now(timezone.utc)
    mock_message.is_read = False
    mock_message.importance = "Normal"
    mock_message.has_attachments = False
    mock_message.attachments = []

    # Mock 계정 설정
    mock_account_instance = MagicMock()
    mock_account_instance.inbox.total_count = 1
    all_obj = mock_account_instance.inbox.all.return_value
    filter_obj = all_obj.filter.return_value
    order_obj = filter_obj.order_by.return_value
    order_obj.__getitem__.return_value = [mock_message]
    mock_account_class.return_value = mock_account_instance

    client = ExchangeClient()
    client.connect()

    messages = client.get_inbox_messages(limit=10)

    assert len(messages) == 1
    assert messages[0]["subject"] == "Test Email"
    assert messages[0]["sender"] == "sender@test.com"
    assert messages[0]["message_id"] == "msg123"


def test_extract_email_address():
    """이메일 주소 추출 테스트"""
    client = ExchangeClient()

    # None 테스트
    assert client._extract_email_address(None) == ""

    # Mailbox 객체 테스트
    mock_mailbox = MagicMock()
    mock_mailbox.email_address = "test@example.com"
    assert client._extract_email_address(mock_mailbox) == "test@example.com"


@patch("src.exchange_client.Account")
def test_connect_transport_error(mock_account, mock_config):
    """네트워크 에러 테스트"""
    mock_account.side_effect = TransportError("Network error")

    client = ExchangeClient()

    with pytest.raises(TransportError):
        client.connect()

    assert not client.is_connected()


@patch("src.exchange_client.Account")
def test_connect_generic_error(mock_account, mock_config):
    """일반 에러 테스트"""
    mock_account.side_effect = RuntimeError("Unexpected error")

    client = ExchangeClient()

    with pytest.raises(RuntimeError):
        client.connect()

    assert not client.is_connected()


@patch("src.exchange_client.Configuration")
@patch("src.exchange_client.Credentials")
@patch("src.exchange_client.Account")
def test_connect_no_domain(mock_account_class, mock_credentials, mock_config_class):
    """도메인 없이 연결 테스트"""
    # Mock 설정
    mock_account_instance = MagicMock()
    mock_account_instance.inbox.total_count = 5
    mock_account_class.return_value = mock_account_instance

    client = ExchangeClient(
        server="test.server.com",
        domain="",
        username="user@test.com",
        password="pass",
    )
    result = client.connect()

    assert result is True
    assert client.is_connected()


@patch("src.exchange_client.Account")
def test_get_inbox_messages_error(mock_account_class, mock_config):
    """메일 가져오기 실패 테스트"""
    # Mock 계정 설정
    mock_account_instance = MagicMock()
    mock_account_instance.inbox.total_count = 1
    mock_account_instance.inbox.all.return_value.filter.side_effect = Exception("Database error")
    mock_account_class.return_value = mock_account_instance

    client = ExchangeClient()
    client.connect()

    with pytest.raises(Exception):
        client.get_inbox_messages(limit=10)


@patch("src.exchange_client.Account")
def test_get_folder_list_success(mock_account_class, mock_config):
    """폴더 목록 가져오기 성공 테스트"""
    # Mock 폴더 생성
    mock_folder1 = MagicMock()
    mock_folder1.name = "Inbox"
    mock_folder2 = MagicMock()
    mock_folder2.name = "Sent Items"

    # Mock 계정 설정
    mock_account_instance = MagicMock()
    mock_account_instance.inbox.total_count = 1
    mock_account_instance.inbox.parent.walk.return_value = [mock_folder1, mock_folder2]
    mock_account_class.return_value = mock_account_instance

    client = ExchangeClient()
    client.connect()

    folders = client.get_folder_list()

    assert len(folders) == 2
    assert "Inbox" in folders
    assert "Sent Items" in folders


def test_get_folder_list_not_connected(mock_config):
    """연결 안 된 상태에서 폴더 목록 가져오기 시도"""
    client = ExchangeClient()

    with pytest.raises(ConnectionError):
        client.get_folder_list()


@patch("src.exchange_client.Account")
def test_get_folder_list_error(mock_account_class, mock_config):
    """폴더 목록 가져오기 실패 테스트"""
    # Mock 계정 설정
    mock_account_instance = MagicMock()
    mock_account_instance.inbox.total_count = 1
    mock_account_instance.inbox.parent.walk.side_effect = Exception("Access denied")
    mock_account_class.return_value = mock_account_instance

    client = ExchangeClient()
    client.connect()

    with pytest.raises(Exception):
        client.get_folder_list()


@patch("src.exchange_client.Configuration")
@patch("src.exchange_client.Credentials")
@patch("src.exchange_client.Account")
def test_disconnect(mock_account_class, mock_credentials, mock_config_class, mock_config):
    """연결 종료 테스트"""
    # Mock 설정
    mock_account_instance = MagicMock()
    mock_account_instance.inbox.total_count = 5
    mock_account_class.return_value = mock_account_instance

    client = ExchangeClient()
    client.connect()
    assert client.is_connected()

    client.disconnect()
    assert not client.is_connected()


@patch("src.exchange_client.Account")
def test_extract_message_info_with_none_subject(mock_account_class, mock_config):
    """제목이 None인 메시지 정보 추출 테스트"""
    # Mock 메시지 생성 (제목 없음)
    mock_message = MagicMock()
    mock_message.id = "msg123"
    mock_message.subject = None
    mock_message.sender = None
    mock_message.to_recipients = None
    mock_message.cc_recipients = None
    mock_message.body = None
    mock_message.text_body = None
    mock_message.datetime_received = datetime.now(timezone.utc)
    mock_message.datetime_sent = datetime.now(timezone.utc)
    mock_message.is_read = False
    mock_message.importance = "Normal"
    mock_message.has_attachments = False
    mock_message.attachments = None

    # Mock 계정 설정
    mock_account_instance = MagicMock()
    mock_account_instance.inbox.total_count = 1
    all_obj = mock_account_instance.inbox.all.return_value
    filter_obj = all_obj.filter.return_value
    order_obj = filter_obj.order_by.return_value
    order_obj.__getitem__.return_value = [mock_message]
    mock_account_class.return_value = mock_account_instance

    client = ExchangeClient()
    client.connect()

    messages = client.get_inbox_messages(limit=1)

    assert len(messages) == 1
    assert messages[0]["subject"] == "(제목 없음)"
    assert messages[0]["sender"] == ""
    assert messages[0]["sender_name"] == "Unknown"
    assert messages[0]["body"] == ""
    assert messages[0]["text_body"] == ""
    assert messages[0]["to_recipients"] == []
    assert messages[0]["cc_recipients"] == []
    assert messages[0]["attachment_count"] == 0
    assert messages[0]["message_id"] == "msg123"


@patch("src.exchange_client.Account")
def test_get_inbox_messages_full_fetch_mode(mock_account_class, mock_config):
    """전체 메일 가져오기 모드 테스트 (limit=None, days_back=None)"""
    # Mock 메시지 생성
    mock_messages = []
    for i in range(3):
        msg = MagicMock()
        msg.id = f"msg{i}"
        msg.subject = f"Email {i}"
        msg.sender.email_address = f"sender{i}@test.com"
        msg.sender.name = f"Sender {i}"
        msg.to_recipients = []
        msg.cc_recipients = []
        msg.body = f"Body {i}"
        msg.text_body = f"Text {i}"
        msg.datetime_received = datetime.now(timezone.utc)
        msg.datetime_sent = datetime.now(timezone.utc)
        msg.is_read = False
        msg.importance = "Normal"
        msg.has_attachments = False
        msg.attachments = []
        mock_messages.append(msg)

    # Mock 계정 설정
    mock_account_instance = MagicMock()
    mock_account_instance.inbox.total_count = 3
    all_obj = mock_account_instance.inbox.all.return_value
    order_obj = all_obj.order_by.return_value
    order_obj.__iter__.return_value = iter(mock_messages)
    mock_account_class.return_value = mock_account_instance

    client = ExchangeClient()
    client.connect()

    # limit=None, days_back=None로 전체 가져오기
    messages = client.get_inbox_messages(limit=None, days_back=None)

    assert len(messages) == 3
    assert messages[0]["message_id"] == "msg0"
    assert messages[1]["message_id"] == "msg1"
    assert messages[2]["message_id"] == "msg2"


@patch("src.exchange_client.Account")
def test_get_inbox_messages_with_since_datetime(mock_account_class, mock_config):
    """증분 동기화 테스트 (since_datetime 파라미터)"""
    # Mock 메시지 생성
    mock_message = MagicMock()
    mock_message.id = "msg_new"
    mock_message.subject = "New Email"
    mock_message.sender.email_address = "sender@test.com"
    mock_message.sender.name = "Sender"
    mock_message.to_recipients = []
    mock_message.cc_recipients = []
    mock_message.body = "New body"
    mock_message.text_body = "New text"
    mock_message.datetime_received = datetime.now(timezone.utc)
    mock_message.datetime_sent = datetime.now(timezone.utc)
    mock_message.is_read = False
    mock_message.importance = "Normal"
    mock_message.has_attachments = False
    mock_message.attachments = []

    # Mock 계정 설정
    mock_account_instance = MagicMock()
    mock_account_instance.inbox.total_count = 1
    all_obj = mock_account_instance.inbox.all.return_value
    filter_obj = all_obj.filter.return_value
    order_obj = filter_obj.order_by.return_value
    order_obj.__getitem__.return_value = [mock_message]
    mock_account_class.return_value = mock_account_instance

    client = ExchangeClient()
    client.connect()

    # since_datetime 사용하여 증분 동기화
    since = datetime(2024, 1, 1, tzinfo=timezone.utc)
    messages = client.get_inbox_messages(since_datetime=since)

    assert len(messages) == 1
    assert messages[0]["message_id"] == "msg_new"

    # filter가 올바른 파라미터로 호출되었는지 확인
    all_obj.filter.assert_called_once()


@patch("src.exchange_client.Account")
def test_get_inbox_messages_with_progress_callback(mock_account_class, mock_config):
    """진행률 콜백 테스트"""
    # Mock 메시지 생성
    mock_messages = []
    for i in range(5):
        msg = MagicMock()
        msg.id = f"msg{i}"
        msg.subject = f"Email {i}"
        msg.sender.email_address = f"sender{i}@test.com"
        msg.sender.name = f"Sender {i}"
        msg.to_recipients = []
        msg.cc_recipients = []
        msg.body = f"Body {i}"
        msg.text_body = f"Text {i}"
        msg.datetime_received = datetime.now(timezone.utc)
        msg.datetime_sent = datetime.now(timezone.utc)
        msg.is_read = False
        msg.importance = "Normal"
        msg.has_attachments = False
        msg.attachments = []
        mock_messages.append(msg)

    # Mock 계정 설정
    mock_account_instance = MagicMock()
    mock_account_instance.inbox.total_count = 5
    all_obj = mock_account_instance.inbox.all.return_value
    filter_obj = all_obj.filter.return_value
    order_obj = filter_obj.order_by.return_value
    order_obj.count.return_value = 5
    order_obj.__getitem__.return_value = mock_messages
    order_obj.__iter__.return_value = iter(mock_messages)
    mock_account_class.return_value = mock_account_instance

    client = ExchangeClient()
    client.connect()

    # 진행률 추적
    progress_calls = []

    def progress_callback(current: int, total: int) -> None:
        progress_calls.append((current, total))

    messages = client.get_inbox_messages(limit=10, progress_callback=progress_callback)

    assert len(messages) == 5
    # 진행률 콜백이 호출되었는지 확인
    assert len(progress_calls) == 5
    assert progress_calls[0] == (1, 5)
    assert progress_calls[4] == (5, 5)
