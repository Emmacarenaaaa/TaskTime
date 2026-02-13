from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel, 
                               QHBoxLayout, QDialog, QComboBox, QStackedWidget, 
                               QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt

class RoleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Attribuer un Rôle")
        
        self.layout = QVBoxLayout(self)
        
        self.layout.addWidget(QLabel("Sélectionner un utilisateur :"))
        self.combo_users = QComboBox()
        self.layout.addWidget(self.combo_users)
        
        self.layout.addWidget(QLabel("Sélectionner ou saisir un rôle :"))
        self.combo_roles = QComboBox()
        self.combo_roles.setEditable(True)
        self.layout.addWidget(self.combo_roles)
        
        btn_layout = QHBoxLayout()
        self.btn_valider = QPushButton("Valider")
        self.btn_annuler = QPushButton("Annuler")
        btn_layout.addWidget(self.btn_valider)
        btn_layout.addWidget(self.btn_annuler)
        self.layout.addLayout(btn_layout)
        
        self.btn_valider.clicked.connect(self.accept)
        self.btn_annuler.clicked.connect(self.reject)

class GestionView(QWidget):
    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout(self)
        self.stack = QStackedWidget()
        self.main_layout.addWidget(self.stack)

        # Tableau de bord
        self.page_dashboard = QWidget()
        self.setup_dashboard()
        self.stack.addWidget(self.page_dashboard)

        # Gestionnaire de liste (Générique)
        self.page_list = QWidget()
        self.setup_list_view()
        self.stack.addWidget(self.page_list)

    def setup_dashboard(self):
        layout = QVBoxLayout(self.page_dashboard)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        lbl = QLabel("ADMINISTRATION")
        lbl.setObjectName("lbl_titre")
        layout.addWidget(lbl)

        # Gros Boutons - Texte épuré
        self.btn_manage_users = QPushButton("UTILISATEURS")
        self.btn_manage_users.setFixedSize(220, 50)
        self.btn_manage_users.setObjectName("btn_big_menu")
        
        self.btn_manage_activities = QPushButton("ACTIVITÉS")
        self.btn_manage_activities.setFixedSize(220, 50)
        self.btn_manage_activities.setObjectName("btn_big_menu")

        self.btn_manage_roles = QPushButton("RÔLES")
        self.btn_manage_roles.setFixedSize(220, 50)
        self.btn_manage_roles.setObjectName("btn_big_menu")

        layout.addWidget(self.btn_manage_users)
        layout.addWidget(self.btn_manage_activities)
        layout.addWidget(self.btn_manage_roles)

        layout.addSpacing(20)
        
        self.btn_back_home = QPushButton("Retour Accueil")
        self.btn_back_home.setFixedSize(180, 40)
        self.btn_back_home.setObjectName("btn_retour")
        layout.addWidget(self.btn_back_home)

    def setup_list_view(self):
        layout = QVBoxLayout(self.page_list)
        layout.setContentsMargins(10, 10, 10, 10)
        
        #   En-tête
        header = QHBoxLayout()
        self.btn_back_dashboard = QPushButton("Retour")
        self.btn_back_dashboard.setFixedSize(100, 35) 
        self.btn_back_dashboard.setObjectName("btn_retour")
        
        self.lbl_list_title = QLabel("GESTION")
        self.lbl_list_title.setObjectName("lbl_titre_choice") 
        self.lbl_list_title.setAlignment(Qt.AlignCenter)
        
        self.btn_add_item = QPushButton("+ Ajouter")
        self.btn_add_item.setCursor(Qt.PointingHandCursor)
        self.btn_add_item.setFlat(True)
        self.btn_add_item.setMinimumWidth(120)
        self.btn_add_item.setFixedHeight(45)
        self.btn_add_item.setObjectName("btn_add_text")
        
        header.addWidget(self.btn_back_dashboard)
        header.addStretch()
        header.addWidget(self.lbl_list_title)
        header.addStretch()
        header.addWidget(self.btn_add_item)
        
        layout.addLayout(header)

        # List
        self.list_widget = QListWidget()
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setObjectName("list_admin")
        
        self.list_widget.setSelectionMode(QListWidget.NoSelection)
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        self.list_widget.setSpacing(8)
        
        layout.addWidget(self.list_widget)

    def set_title(self, title):
        self.lbl_list_title.setText(title)