"""설정 대화상자 모듈"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import QSettings


class SettingsDialog(QDialog):
    """설정 대화상자"""
    
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.settings = QSettings('Freitag', 'ExchangeMailViewer')
        self.init_ui()
        self.load_settings()
    
    def init_ui(self) -> None:
        """UI 초기화"""
        self.setWindowTitle("설정")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # 폼 레이아웃
        form = QFormLayout()
        
        # 입력 필드
        self.server_input = QLineEdit()
        self.domain_input = QLineEdit()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.email_input = QLineEdit()
        
        form.addRow("Exchange 서버:", self.server_input)
        form.addRow("도메인:", self.domain_input)
        form.addRow("사용자명:", self.username_input)
        form.addRow("비밀번호:", self.password_input)
        form.addRow("이메일 (선택):", self.email_input)
        
        layout.addLayout(form)
        
        # 도움말
        help_label = QLabel("* 비밀번호는 안전하게 저장되지 않습니다.")
        help_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(help_label)
        
        # 버튼
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("저장")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("취소")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
    
    def load_settings(self) -> None:
        """설정 불러오기"""
        self.server_input.setText(self.settings.value('server', 'outlook.hmc.co.kr'))
        self.domain_input.setText(self.settings.value('domain', 'autos'))
        self.username_input.setText(self.settings.value('username', ''))
        self.email_input.setText(self.settings.value('email', ''))
        # 보안상 비밀번호는 저장하지 않음
    
    def save_settings(self) -> None:
        """설정 저장"""
        # 필수 값 검증
        if not self.server_input.text() or not self.username_input.text():
            QMessageBox.warning(self, "경고", "서버 주소와 사용자명은 필수입니다.")
            return
        
        # .env 파일에 저장하도록 안내
        import os
        env_content = f"""# Exchange Server Configuration
EXCHANGE_SERVER={self.server_input.text()}
EXCHANGE_DOMAIN={self.domain_input.text()}
EXCHANGE_USERNAME={self.username_input.text()}
EXCHANGE_PASSWORD={self.password_input.text()}
EXCHANGE_EMAIL={self.email_input.text()}

# Email Settings
MAIL_FETCH_LIMIT=50
"""
        
        try:
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(env_content)
            
            # QSettings에도 저장 (비밀번호 제외)
            self.settings.setValue('server', self.server_input.text())
            self.settings.setValue('domain', self.domain_input.text())
            self.settings.setValue('username', self.username_input.text())
            self.settings.setValue('email', self.email_input.text())
            
            QMessageBox.information(self, "성공", ".env 파일에 설정이 저장되었습니다.")
            self.accept()
        
        except Exception as e:
            QMessageBox.critical(self, "오류", f"설정 저장 실패:\n{str(e)}")
