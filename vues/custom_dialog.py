from PySide6.QtWidgets import QDialog, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

class StyledDialog(QDialog):
    """
    Boîte de dialogue personnalisée avec barre de titre styled (identique à SelectionDialog).
    """
    def __init__(self, parent=None, title="Dialogue"):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        
        self.resize(350, 450)
        self.setObjectName("custom_dialog")
        
        # Global Layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # --- Title Bar ---
        self.title_bar = QWidget()
        self.title_bar.setObjectName("DialogTitleBar") 
        # Min height set in CSS
        
        self.title_layout = QHBoxLayout(self.title_bar)
        self.title_layout.setContentsMargins(10, 0, 5, 0)
        
        self.lbl_title = QLabel(title)
        self.lbl_title.setObjectName("TitleLabel")
        self.title_layout.addWidget(self.lbl_title)
        
        self.title_layout.addStretch()
        
        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("btn_close") 
        # Style defined in CSS for #TitleBar QPushButton
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.clicked.connect(self.reject)
        self.title_layout.addWidget(self.btn_close)
        
        self.main_layout.addWidget(self.title_bar)
        
        # --- Content Area ---
        self.content_widget = QWidget()
        self.content_widget.setObjectName("dialog_content")
        # Style managed in QSS via ID
        
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(10)
        
        self.main_layout.addWidget(self.content_widget)
        
    def exec(self):
        """Override exec to show overlay behind dialog"""
        # Create overlay if parent exists
        overlay = None
        if self.parent():
            from PySide6.QtWidgets import QWidget
            overlay = QWidget(self.parent())
            overlay.setObjectName("dialog_overlay")
            overlay.setGeometry(self.parent().rect())
            overlay.setStyleSheet("background-color: rgba(0, 0, 0, 150);")  # Semi-transparent black
            overlay.show()
            overlay.raise_()
            self.raise_()
        
        result = super().exec()
        
        # Clean up overlay
        if overlay:
            overlay.deleteLater()
            
        return result
        
    # Helpers to move window
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'old_pos') and event.buttons() == Qt.LeftButton:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()


class CustomMessageBox(StyledDialog):
    """
    MessageBox personnalisée avec design épuré.
    """
    def __init__(self, parent=None, title="Message", text="", msg_type="info"):
        super().__init__(parent, title)
        self.setObjectName("msg_dialog")
        self.resize(400, 180)
        
        # Message text
        self.lbl_text = QLabel(text)
        self.lbl_text.setObjectName("msg_text")
        self.lbl_text.setWordWrap(True)
        self.lbl_text.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.lbl_text)
        
        self.content_layout.addStretch()
        
        # Button
        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch()
        
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setObjectName("btn_add_activites")
        self.btn_ok.setCursor(Qt.PointingHandCursor)
        self.btn_ok.setMinimumWidth(100)
        self.btn_ok.clicked.connect(self.accept)
        self.button_layout.addWidget(self.btn_ok)
        
        self.button_layout.addStretch()
        self.content_layout.addLayout(self.button_layout)

    @staticmethod
    def information(parent, title, text):
        dlg = CustomMessageBox(parent, title, text, "info")
        dlg.exec()
        
    @staticmethod
    def warning(parent, title, text):
        dlg = CustomMessageBox(parent, title, text, "warning")
        dlg.exec()

    @staticmethod
    def critical(parent, title, text):
        dlg = CustomMessageBox(parent, title, text, "error")
        dlg.exec()

    @staticmethod
    def question(parent, title, text):
        dlg = CustomMessageBox(parent, title, text, "question")
        dlg.btn_ok.setText("Oui")
        
        btn_no = QPushButton("Non")
        btn_no.setObjectName("btn_stop")
        btn_no.setCursor(Qt.PointingHandCursor)
        btn_no.setMinimumWidth(100)
        btn_no.clicked.connect(dlg.reject)
        dlg.button_layout.insertWidget(0, btn_no)
        
        return dlg.exec()
