from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                                 QPushButton, QListWidget, QListWidgetItem, 
                                 QLineEdit, QColorDialog, QFrame, QDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QKeySequence

class SettingsView(QWidget):
    def __init__(self):
        super().__init__()
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(30, 30, 30, 30)
        self.layout.setSpacing(20)
        
        # Titre
        self.lbl_title = QLabel("Réglages")
        self.lbl_title.setObjectName("lbl_titre")
        self.layout.addWidget(self.lbl_title)
        
        
        # --- Section 2: Raccourcis ---
        # On maximise l'espace vu que c'est le seul contenu
        self.lbl_shortcuts = QLabel("Raccourcis Enregistrés")
        self.lbl_shortcuts.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        self.layout.addWidget(self.lbl_shortcuts)
        
        from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QHeaderView
        
        self.list_shortcuts = QTreeWidget()
        self.list_shortcuts.setColumnCount(2)
        self.list_shortcuts.setHeaderLabels(["Action", "Raccourci"])
        # Colonne Action prend de la place, Raccourci juste ce qu'il faut
        self.list_shortcuts.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.list_shortcuts.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.list_shortcuts.setAlternatingRowColors(True)
        self.list_shortcuts.setRootIsDecorated(False) 
        # Style spécifique pour la liste pour qu'elle remplisse bien
        self.list_shortcuts.setStyleSheet("""
            QTreeWidget {
                border: none;
                background-color: transparent;
                font-size: 16px;
                color: #F0EDEE;
            }
            QTreeWidget::item {
                border-bottom: 1px solid #372549;
                padding: 10px;
                height: 40px;
            }
            QTreeWidget::item:hover {
                background-color: rgba(255, 102, 153, 0.1);
                border-radius: 8px;
            }
            QTreeWidget::item:selected {
                background-color: #9F004C;
                border-radius: 8px;
                color: white;
            }
            QHeaderView::section {
                background-color: transparent;
                border: none;
                border-bottom: 2px solid #FF6699;
                padding: 10px;
                color: #FF6699;
                font-size: 14px;
                font-weight: bold;
                text-transform: uppercase;
            }
        """)
        self.layout.addWidget(self.list_shortcuts)
        
        # Boutons d'action
        self.layout_btns = QHBoxLayout()
        self.btn_edit_shortcut = QPushButton("Modifier Raccourci")
        self.btn_edit_shortcut.setFixedWidth(200)
        self.btn_edit_shortcut.setMinimumHeight(50)
        
        self.btn_del_shortcut = QPushButton("Supprimer Raccourci")
        self.btn_del_shortcut.setFixedWidth(200)
        self.btn_del_shortcut.setMinimumHeight(50)
        self.btn_del_shortcut.setObjectName("btn_cancel")
        
        self.layout_btns.addStretch()
        self.layout_btns.addWidget(self.btn_del_shortcut)
        self.layout_btns.addWidget(self.btn_edit_shortcut)
        
        self.layout.addLayout(self.layout_btns)
        


from vues.custom_dialog import StyledDialog

class KeyCaptureDialog(StyledDialog):
    def __init__(self, parent=None, action_name=""):
        super().__init__(parent, f"Modifier raccourci : {action_name}")
        self.resize(400, 200)
        
        # Message instruction
        lbl = QLabel("Appuyez sur la nouvelle combinaison de touches...")
        lbl.setObjectName("msg_text")
        lbl.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(lbl)
        
        # Affichage de la touche capturée
        self.lbl_key = QLabel("...")
        self.lbl_key.setObjectName("shortcut_display")
        self.lbl_key.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.lbl_key)
        
        self.content_layout.addStretch()
        
        # Bouton valider
        self.btn_ok = QPushButton("Valider")
        self.btn_ok.setObjectName("btn_add_activites")
        self.btn_ok.setEnabled(False)
        self.btn_ok.setMinimumWidth(100)
        self.btn_ok.clicked.connect(self.accept)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addStretch()
        self.content_layout.addLayout(btn_layout)
        
        self.captured_sequence = None
        
    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        
        # Ignorer les touches seules de modificateurs
        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            return
            
       
        m_val = modifiers.value if hasattr(modifiers, 'value') else int(modifiers)
        k_val = key.value if hasattr(key, 'value') else int(key)
        
        val = m_val | k_val
        sequence = QKeySequence(val)
        
        self.captured_sequence = sequence.toString(QKeySequence.NativeText)
        
        self.lbl_key.setText(self.captured_sequence)
        self.btn_ok.setEnabled(True)

    def get_sequence(self):
        return self.captured_sequence
