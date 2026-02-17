"""메인 윈도우 모듈"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QTextEdit,
    QStatusBar,
    QMessageBox,
    QSplitter,
    QToolBar,
    QAction,
    QProgressBar,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QCloseEvent, QFont
from src.exchange_client import ExchangeClient
from src.mail_db import MailRepository
from src.utils.logger import setup_logger
from src.ui.settings_dialog import SettingsDialog

logger = setup_logger(__name__)


class EmailFetchThread(QThread):
    """메일을 백그라운드에서 가져오는 스레드"""

    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int)  # 현재 수, 전체 수

    def __init__(
        self,
        client: ExchangeClient,
        limit: Optional[int] = 50,
        days_back: Optional[int] = 7,
        since_datetime: Optional[datetime] = None,
    ) -> None:
        super().__init__()
        self.client = client
        self.limit = limit
        self.days_back = days_back
        self.since_datetime = since_datetime

    def run(self) -> None:
        """메일 가져오기 실행"""
        try:
            # 진행률 콜백 함수
            def progress_callback(current: int, total: int) -> None:
                self.progress.emit(current, total)

            messages = self.client.get_inbox_messages(
                limit=self.limit,
                days_back=self.days_back,
                since_datetime=self.since_datetime,
                progress_callback=progress_callback,
            )
            self.finished.emit(messages)
        except Exception as e:
            logger.error(f"메일 가져오기 실패: {e}")
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    """메인 윈도우 클래스"""

    def __init__(self) -> None:
        super().__init__()
        self.client: Optional[ExchangeClient] = None
        self.messages: List[Dict[str, Any]] = []
        self.fetch_thread: Optional[EmailFetchThread] = None
        self.mail_repo = MailRepository()  # SQLite 저장소
        self.auto_connected = False  # 자동 연결 여부

        self.init_ui()

        # DB에서 기존 메일 로드
        self.load_emails_from_db()

    def init_ui(self) -> None:
        """UI 초기화"""
        self.setWindowTitle("Freitag - Exchange 메일 뷰어")
        self.setGeometry(100, 100, 1200, 800)

        # 툴바 생성
        self.create_toolbar()

        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 메인 레이아웃
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # 스플리터 (좌우 분할)
        splitter = QSplitter(Qt.Horizontal)

        # 왼쪽: 메일 테이블
        self.mail_table = QTableWidget()
        self.mail_table.setColumnCount(5)
        self.mail_table.setHorizontalHeaderLabels(["", "날짜", "제목", "보낸이", "📎"])

        # 정렬 활성화
        self.mail_table.setSortingEnabled(True)

        # 선택 모드 설정
        self.mail_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.mail_table.setSelectionMode(QTableWidget.SingleSelection)

        # 편집 불가
        self.mail_table.setEditTriggers(QTableWidget.NoEditTriggers)

        # 헤더 설정
        header = self.mail_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # 읽음 상태
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 날짜
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # 제목
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 보낸이
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # 첨부

        # 행 클릭 이벤트
        self.mail_table.cellClicked.connect(self.on_mail_row_clicked)

        splitter.addWidget(self.mail_table)

        # 오른쪽: 메일 내용
        self.mail_viewer = QTextEdit()
        self.mail_viewer.setReadOnly(True)
        splitter.addWidget(self.mail_viewer)

        # 스플리터 비율 설정 (1:2)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)

        # 프로그레스 바
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        main_layout.addWidget(self.progress_bar)

        # 상태바
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("준비")

    def create_toolbar(self) -> None:
        """툴바 생성"""
        toolbar = QToolBar("메인 툴바")
        self.addToolBar(toolbar)

        # 연결 버튼
        connect_action = QAction("연결", self)
        connect_action.triggered.connect(self.connect_to_server)
        toolbar.addAction(connect_action)

        # 새로고침 버튼
        refresh_action = QAction("새로고침", self)
        refresh_action.triggered.connect(self.refresh_emails)
        toolbar.addAction(refresh_action)

        toolbar.addSeparator()

        # 설정 버튼
        settings_action = QAction("설정", self)
        settings_action.triggered.connect(self.open_settings)
        toolbar.addAction(settings_action)

    def showEvent(self, event) -> None:  # type: ignore
        """윈도우가 표시될 때 자동 연결 시도"""
        super().showEvent(event)

        # 최초 1회만 자동 연결 시도
        if not self.auto_connected:
            self.auto_connected = True
            self.auto_connect_and_sync()

    def load_emails_from_db(self) -> None:
        """DB에서 기존 메일 로드"""
        try:
            emails = self.mail_repo.get_all_emails()
            if emails:
                logger.info(f"DB에서 {len(emails)}개 메일 로드")
                self.messages = emails
                self.display_emails(emails)
                self.statusBar.showMessage(f"DB에서 {len(emails)}개 메일 로드 완료")
            else:
                logger.info("DB에 저장된 메일 없음")
        except Exception as e:
            logger.error(f"DB 메일 로드 실패: {e}")

    def auto_connect_and_sync(self) -> None:
        """자동 연결 및 동기화"""
        try:
            self.statusBar.showMessage("서버 자동 연결 중...")

            # ExchangeClient 생성
            self.client = ExchangeClient()

            # 연결 시도
            if self.client.connect():
                self.statusBar.showMessage("연결 성공! 새 메일 확인 중...")
                logger.info("서버 자동 연결 성공")

                # 증분 동기화 (마지막 메일 이후)
                self.sync_new_emails()
            else:
                self.statusBar.showMessage("자동 연결 실패 - 수동 연결을 사용하세요")
                logger.warning("서버 자동 연결 실패")

        except Exception as e:
            logger.error(f"자동 연결 실패: {e}")
            self.statusBar.showMessage(f"자동 연결 실패: {str(e)}")

    def sync_new_emails(self) -> None:
        """증분 동기화 - 새 메일만 가져오기"""
        if not self.client or not self.client.is_connected():
            return

        # DB에서 가장 최근 메일 날짜 가져오기
        latest_datetime = self.mail_repo.get_latest_datetime()

        if latest_datetime:
            # 증분 동기화: 마지막 메일 이후만
            logger.info(f"증분 동기화: {latest_datetime} 이후 메일 가져오기")
            self.fetch_thread = EmailFetchThread(
                self.client, limit=None, days_back=None, since_datetime=latest_datetime
            )
        else:
            # 첫 실행: 전체 메일 가져오기
            logger.info("첫 실행: 서버의 모든 메일 가져오기")
            self.fetch_thread = EmailFetchThread(
                self.client, limit=None, days_back=None
            )

        # 프로그레스 바 표시
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.fetch_thread.finished.connect(self.on_emails_synced)
        self.fetch_thread.error.connect(self.on_fetch_error)
        self.fetch_thread.progress.connect(self.on_progress_update)
        self.fetch_thread.start()

    def connect_to_server(self) -> None:
        """Exchange 서버에 연결 (수동)"""
        try:
            self.statusBar.showMessage("서버 연결 중...")

            # ExchangeClient 생성
            self.client = ExchangeClient()

            # 연결 시도
            if self.client.connect():
                self.statusBar.showMessage("연결 성공!")
                QMessageBox.information(self, "성공", "Exchange 서버에 연결되었습니다.")
                # 수동 연결 후 증분 동기화
                self.sync_new_emails()
            else:
                self.statusBar.showMessage("연결 실패")
                QMessageBox.warning(self, "실패", "서버 연결에 실패했습니다.")

        except Exception as e:
            logger.error(f"연결 실패: {e}")
            self.statusBar.showMessage("연결 실패")
            QMessageBox.critical(self, "오류", f"연결 중 오류 발생:\n{str(e)}")

    def refresh_emails(self) -> None:
        """메일 목록 새로고침 (수동)"""
        if not self.client or not self.client.is_connected():
            QMessageBox.warning(self, "경고", "먼저 서버에 연결하세요.")
            return

        self.statusBar.showMessage("메일 가져오는 중...")

        # 프로그레스 바 표시
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        # 증분 동기화
        self.sync_new_emails()

    def on_progress_update(self, current: int, total: int) -> None:
        """프로그레스 바 업데이트"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress_bar.setValue(percentage)
            self.progress_bar.setFormat(f"{current}/{total} ({percentage}%)")
            self.statusBar.showMessage(f"메일 가져오는 중... {current}/{total}")

    def on_emails_synced(self, new_messages: List[Dict[str, Any]]) -> None:
        """새 메일 동기화 완료 시 호출"""
        # 프로그레스 바 숨김
        self.progress_bar.setVisible(False)

        if new_messages:
            # DB에 저장
            saved_count = self.mail_repo.save_emails(new_messages)
            logger.info(f"{saved_count}개의 새 메일 저장")

            # DB에서 전체 메일 다시 로드 (정렬 및 표시)
            all_emails = self.mail_repo.get_all_emails()
            self.messages = all_emails
            self.display_emails(all_emails)

            self.statusBar.showMessage(
                f"{saved_count}개의 새 메일 저장 완료 (총 {len(all_emails)}개)"
            )
        else:
            logger.info("새 메일 없음")
            self.statusBar.showMessage("새 메일이 없습니다")

    def display_emails(self, messages: List[Dict[str, Any]]) -> None:
        """메일 테이블에 표시"""
        # 정렬 비활성화 (데이터 입력 중)
        self.mail_table.setSortingEnabled(False)
        self.mail_table.setRowCount(len(messages))

        # 굵은 글씨 폰트 미리 생성
        bold_font = QFont()
        bold_font.setBold(True)

        for i, msg in enumerate(messages):
            # 0번 컬럼: 읽음 상태
            is_read = msg.get("is_read", False)
            read_item = QTableWidgetItem()
            read_item.setText("⚪" if is_read else "🔵")
            read_item.setTextAlignment(Qt.AlignCenter)
            self.mail_table.setItem(i, 0, read_item)

            # 1번 컬럼: 날짜
            received = msg.get("datetime_received", "")
            if received:
                date_str = received.strftime("%m/%d %H:%M")
            else:
                date_str = ""
            date_item = QTableWidgetItem(date_str)
            date_item.setData(Qt.UserRole, received)  # 정렬용 원본 데이터
            self.mail_table.setItem(i, 1, date_item)

            # 2번 컬럼: 제목
            subject = msg.get("subject", "(제목 없음)")
            subject_item = QTableWidgetItem(subject)
            subject_item.setData(Qt.UserRole, i)  # 메시지 인덱스 저장

            # 안읽은 메일 굵게
            if not is_read:
                subject_item.setFont(bold_font)

            self.mail_table.setItem(i, 2, subject_item)

            # 3번 컬럼: 보낸이
            sender = msg.get("sender", "알 수 없음")
            sender_item = QTableWidgetItem(sender)
            if not is_read:
                sender_item.setFont(bold_font)
            self.mail_table.setItem(i, 3, sender_item)

            # 4번 컬럼: 첨부파일
            has_attachments = msg.get("has_attachments", False)
            attach_item = QTableWidgetItem("📎" if has_attachments else "")
            attach_item.setTextAlignment(Qt.AlignCenter)
            self.mail_table.setItem(i, 4, attach_item)

        # 정렬 활성화
        self.mail_table.setSortingEnabled(True)

        # 기본 정렬: 날짜 내림차순 (최신순)
        self.mail_table.sortItems(1, Qt.DescendingOrder)

    def on_fetch_error(self, error: str) -> None:
        """메일 가져오기 실패"""
        # 프로그레스 바 숨김
        self.progress_bar.setVisible(False)
        self.statusBar.showMessage("메일 가져오기 실패")
        # 자동 연결 실패 시에는 상태바 메시지만 표시
        if not self.auto_connected:
            QMessageBox.critical(self, "오류", f"메일을 가져오는 중 오류 발생:\n{error}")

    def on_mail_row_clicked(self, row: int, column: int) -> None:
        """테이블 행 클릭 시 호출"""
        # 제목 컬럼에서 메시지 인덱스 가져오기
        subject_item = self.mail_table.item(row, 2)
        if not subject_item:
            return

        index = subject_item.data(Qt.UserRole)
        if index is None or not (0 <= index < len(self.messages)):
            return

        msg = self.messages[index]

        # 메일 내용 표시
        subject = msg.get("subject", "(제목 없음)")
        sender = msg.get("sender", "알 수 없음")
        received = msg.get("datetime_received", "")
        body = msg.get("body", "(내용 없음)")
        has_attachments = msg.get("has_attachments", False)

        if received:
            date_str = received.strftime("%Y-%m-%d %H:%M:%S")
        else:
            date_str = "알 수 없음"

        html = f"""
        <h2>{subject}</h2>
        <p><b>보낸이:</b> {sender}</p>
        <p><b>날짜:</b> {date_str}</p>
        <p><b>첨부파일:</b> {'있음' if has_attachments else '없음'}</p>
        <hr>
        <pre>{body}</pre>
        """

        self.mail_viewer.setHtml(html)

        # 읽음 상태로 변경
        read_item = self.mail_table.item(row, 0)
        if read_item:
            read_item.setText("⚪")

        # 굵은 글씨 해제
        subject_item.setFont(QFont())
        sender_item = self.mail_table.item(row, 3)
        if sender_item:
            sender_item.setFont(QFont())

    def open_settings(self) -> None:
        """설정 대화상자 열기"""
        dialog = SettingsDialog(self)
        if dialog.exec_():
            # 설정 저장됨
            self.statusBar.showMessage("설정이 저장되었습니다.")

    def closeEvent(self, event: QCloseEvent) -> None:
        """윈도우 닫기 전"""
        if self.client and self.client.is_connected():
            self.client.disconnect()
        event.accept()
