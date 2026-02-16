"""Freitag Exchange Mail Viewer - 메인 실행 파일"""

import sys
from PyQt5.QtWidgets import QApplication
from src.ui.main_window import MainWindow


def main() -> int:
    """메인 함수"""
    app = QApplication(sys.argv)
    app.setApplicationName("Freitag")
    app.setOrganizationName("Freitag")
    
    # 메인 윈도우 생성 및 표시
    window = MainWindow()
    window.show()
    
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())
