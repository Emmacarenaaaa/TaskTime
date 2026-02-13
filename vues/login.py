"""
Vue de connexion (actuellement non utilisée).
Conservée pour une éventuelle implémentation future de l'authentification.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PySide6.QtCore import Qt, Signal

class LoginView(QWidget):
    """Vue de connexion utilisateur."""
    signup_requested = Signal()
    
    def __init__(self):
        super().__init__()

        # Création des éléments de l'interface
        self.lbl_titre = QLabel("Connexion TaskTime")
        self.lbl_titre.setObjectName("lbl_titre")
        self.lbl_titre.setAlignment(Qt.AlignCenter)
        self.input_nom = QLineEdit()
        self.input_nom.setObjectName("input_nom")
        self.input_nom.setPlaceholderText("Nom d'utilisateur")

        self.input_mdp = QLineEdit()
        self.input_mdp.setObjectName("input_mdp")
        self.input_mdp.setPlaceholderText("Mot de passe")
        self.input_mdp.setEchoMode(QLineEdit.Password)

        self.btn_login = QPushButton("Se connecter")
        self.btn_login.setObjectName("btn_login") 

        self.btn_signup = QPushButton("Pas de compte ? S'inscrire")
        self.btn_signup.setObjectName("btn_signup")
        self.btn_signup.setCursor(Qt.PointingHandCursor)
        self.btn_signup.clicked.connect(lambda: self.signup_requested.emit())

        # Organisation du layout
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        
        # Conteneur carte de connexion
        self.login_card = QWidget()
        self.login_card.setMaximumWidth(450) 
        self.login_card.setMinimumWidth(300)
        self.login_card.setObjectName("login_card")
        
        card_layout = QVBoxLayout(self.login_card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(15)

        card_layout.addWidget(self.lbl_titre)
        card_layout.addSpacing(10)
        
        self.lbl_nom = QLabel("Nom :")
        self.lbl_nom.setObjectName("lbl_field_title")
        card_layout.addWidget(self.lbl_nom)
        card_layout.addWidget(self.input_nom)
        
        self.lbl_mdp = QLabel("Mot de passe :")
        self.lbl_mdp.setObjectName("lbl_field_title")
        card_layout.addWidget(self.lbl_mdp)
        card_layout.addWidget(self.input_mdp)
        
        card_layout.addSpacing(20)
        
        # Style du bouton géré dans le QSS via l'objectName "btn_login"
        card_layout.addWidget(self.btn_login)
        card_layout.addWidget(self.btn_signup)

        main_layout.addWidget(self.login_card)

    def afficher_erreur(self, message):
        """Affiche un message d'erreur de connexion."""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.warning(self, "Erreur de connexion", message)