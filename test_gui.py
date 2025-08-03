#!/usr/bin/env python3
"""
GUI 테스트용 간단한 프로그램
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel, QPushButton
from PyQt5.QtCore import Qt

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Web Ceph Auto - GUI 테스트")
        self.setGeometry(100, 100, 400, 300)
        
        # 중앙 위젯
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 레이아웃
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # 라벨들
        title_label = QLabel("Web Ceph Auto")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        
        status_label = QLabel("프로그램이 정상적으로 실행되었습니다!")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet("font-size: 14px; margin: 10px;")
        
        info_label = QLabel("GUI 환경이 정상적으로 작동하고 있습니다.")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size: 12px; color: green; margin: 10px;")
        
        # 버튼
        test_button = QPushButton("테스트 버튼")
        test_button.clicked.connect(self.test_button_clicked)
        test_button.setStyleSheet("padding: 10px; font-size: 12px;")
        
        close_button = QPushButton("닫기")
        close_button.clicked.connect(self.close)
        close_button.setStyleSheet("padding: 10px; font-size: 12px;")
        
        # 레이아웃에 추가
        layout.addWidget(title_label)
        layout.addWidget(status_label)
        layout.addWidget(info_label)
        layout.addWidget(test_button)
        layout.addWidget(close_button)
        
    def test_button_clicked(self):
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.information(self, "테스트", "버튼이 정상적으로 작동합니다!")

def main():
    app = QApplication(sys.argv)
    
    # 폰트 설정
    app.setFont(app.font())
    
    window = TestWindow()
    window.show()
    window.raise_()
    window.activateWindow()
    
    print("GUI 테스트 창이 표시되었습니다.")
    print("창이 보이지 않으면 작업표시줄을 확인해주세요.")
    
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())