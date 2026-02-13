"""
TaskTime - Application de gestion du temps et des activités
Fichier principal de l'application
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QStackedWidget, QMainWindow, QWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout
from PySide6.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QMouseEvent, QCursor

# Imports des modèles
from models.database import DatabaseManager

# Imports des vues
from vues.dashboard import DashboardView
from vues.accueil import AccueilView
from vues.analyses import AnalysesView
from vues.activites import ActivitesView
from vues.chrono import NewChronoView
from vues.settings import SettingsView

# Imports des présentateurs
from presenters.accueil import AccueilPresenter
from presenters.analyses import AnalysesPresenter
from presenters.activites import ActivitesPresenter
from presenters.chrono import ChronoPresenter
from presenters.settings import SettingsPresenter



class CustomTitleBar(QWidget):
    """
    Barre de titre personnalisée pour la fenêtre sans bordures.
    Permet le déplacement, la minimisation, l'agrandissement et la fermeture de la fenêtre.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setFixedHeight(40)
        self.setObjectName("TitleBar")
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(10)
        
        # Titre (Logo ou Texte)
        self.lbl_title = QLabel("TaskTime - Dashboard")
        self.lbl_title.setObjectName("TitleLabel")
        layout.addWidget(self.lbl_title)
        
        layout.addStretch()
        
        # Bouton Réduire
        self.btn_min = QPushButton("－")
        self.btn_min.setFixedSize(40, 40)
        self.btn_min.setObjectName("btn_min")
        self.btn_min.clicked.connect(self.minimize_window)
        layout.addWidget(self.btn_min)
        
        # Bouton Agrandir/Restaurer
        self.btn_max = QPushButton("☐")
        self.btn_max.setFixedSize(40, 40)
        self.btn_max.setObjectName("btn_max")
        self.btn_max.clicked.connect(self.maximize_restore_window)
        layout.addWidget(self.btn_max)
        
        # Bouton Fermer
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(40, 40)
        self.btn_close.setObjectName("btn_close")
        self.btn_close.clicked.connect(self.close_window)
        layout.addWidget(self.btn_close)
        
        # Pour le déplacement de la fenêtre
        self.start_pos = None

    def mousePressEvent(self, event: QMouseEvent):
        """Gère le clic sur la barre de titre pour déplacer la fenêtre."""
        if event.button() == Qt.LeftButton:
            # Utilisation du déplacement natif du système (Windows Snap, multi-écran)
            self.parent_window.windowHandle().startSystemMove()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        """Gestion du mouvement de la souris (géré par startSystemMove)."""
        pass

    def close_window(self):
        """Ferme la fenêtre principale."""
        self.parent_window.close()

    def minimize_window(self):
        """Minimise la fenêtre avec une animation de fondu."""
        # Animation de fondu (Fade Out) avant de minimiser
        self.anim_min = QPropertyAnimation(self.parent_window, b"windowOpacity")
        self.anim_min.setDuration(250)
        self.anim_min.setStartValue(1.0)
        self.anim_min.setEndValue(0.0)
        self.anim_min.setEasingCurve(QEasingCurve.OutQuad)
        
        def on_fade_finished():
            self.parent_window.showMinimized()
            # On rétablit l'opacité pour le retour
            self.parent_window.setWindowOpacity(1.0)
            
        self.anim_min.finished.connect(on_fade_finished)
        self.anim_min.start()

    def maximize_restore_window(self):
        """Bascule entre l'état maximisé et normal de la fenêtre."""
        if self.parent_window.isMaximized():
            self.parent_window.showNormal()
        else:
            self.parent_window.showMaximized()

class Application(QMainWindow):
    """
    Classe principale de l'application TaskTime.
    Gère la fenêtre principale, le tableau de bord et la navigation entre les vues.
    """

    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        
        # Configuration de la fenêtre
        self.setWindowFlags(Qt.FramelessWindowHint) # Fenêtre sans bordure système
        self.resize(1100, 750)
        
        # Disposition principale avec barre de titre personnalisée
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        
        self.layout_global = QVBoxLayout(self.main_widget)
        self.layout_global.setContentsMargins(0, 0, 0, 0)
        self.layout_global.setSpacing(0)
        
        # Barre de titre
        self.title_bar = CustomTitleBar(self)
        self.layout_global.addWidget(self.title_bar)
        
        # Pile de pages
        self.pile_pages = QStackedWidget()
        self.layout_global.addWidget(self.pile_pages)

        # Stockage de session
        self.selected_task_id = None
        self.selected_task_name = None

        # On lance le Dashboard directement
        self.afficher_dashboard()
        
        # Redimensionnement différé pour corriger l'affichage initial
        QTimer.singleShot(100, lambda: self.resize(self.width() + 1, self.height() + 1))
        QTimer.singleShot(150, lambda: self.resize(self.width() - 1, self.height() - 1))

    def afficher_dashboard(self):
        """Initialise et affiche le tableau de bord avec toutes les vues."""
        self.vue_dashboard = DashboardView()
        
        # Préparation de l'onglet Chrono (mode bulles)
        self.vue_chrono = NewChronoView()
        self.presenter_chrono = ChronoPresenter(self.vue_chrono, self.db)

        accueil_widget = self.create_accueil_widget() # Page 0
        
        # Connecter le chronomètre à l'accueil pour la synchro
        if self.presenter_chrono and self.presenter_accueil:
             self.presenter_chrono.set_accueil_presenter(self.presenter_accueil)
        
        activites_widget = self.create_activites_widget() # Page 2
        analyses_widget = self.create_analyses_widget() # Page 3
        
        # Page Réglages
        settings_widget = self.create_settings_widget() # Page 4

        self.vue_dashboard.set_content_pages(
            page_accueil=accueil_widget,
            page_chrono=self.vue_chrono, 
            page_activites=activites_widget,
            page_analyses=analyses_widget,
            page_settings=settings_widget
        )
        
        # Définir la page par défaut sur Accueil (0)
        self.vue_dashboard.switch_page(0)

        self.pile_pages.addWidget(self.vue_dashboard)
        self.pile_pages.setCurrentWidget(self.vue_dashboard)

        # Connecter le changement d'onglet à la logique de rafraîchissement
        self.vue_dashboard.stack.currentChanged.connect(self.on_dashboard_page_changed)

    def nativeEvent(self, eventType, message):
        """Gère les événements natifs Windows pour le redimensionnement de la fenêtre."""
        try:
            msg = message.asQSysInfo() if hasattr(message, 'asQSysInfo') else message
        except:
            return super().nativeEvent(eventType, message)
            
        if eventType == b"windows_generic_MSG":
            import ctypes
            from ctypes import wintypes
            
            msg = ctypes.wintypes.MSG.from_address(int(message))
            
            if msg.message == 0x0084: # WM_NCHITTEST
                p = self.mapFromGlobal(QCursor.pos())
                
                w = self.width()
                h = self.height()
                m = 5 # Marge de resize réduite pour éviter les conflits
                
                # Zones
                left = p.x() < m
                right = p.x() > w - m
                top = p.y() < m
                bottom = p.y() > h - m
                
                if top and left: return True, 13 # HTTOPLEFT
                if top and right: return True, 14 # HTTOPRIGHT
                if bottom and left: return True, 16 # HTBOTTOMLEFT
                if bottom and right: return True, 17 # HTBOTTOMRIGHT
                if left: return True, 10 # HTLEFT
                if right: return True, 11 # HTRIGHT
                if top: return True, 12 # HTTOP
                if bottom: return True, 15 # HTBOTTOM
                
        return super().nativeEvent(eventType, message)

    def on_dashboard_page_changed(self, index):
        """Appelé lorsque l'onglet du tableau de bord change"""
        current_widget = self.vue_dashboard.stack.widget(index)
        
        # Logique de rafraîchissement
        if current_widget == self.vue_analyses and self.presenter_analyses:
            self.presenter_analyses.refresh()
            
        if hasattr(self, 'vue_accueil') and current_widget == self.vue_accueil and self.presenter_accueil:
            self.presenter_accueil.refresh()
            
        if hasattr(self, 'vue_activites') and current_widget == self.vue_activites and self.presenter_activites:
            self.presenter_activites.refresh()
            
        if hasattr(self, 'vue_settings') and current_widget == self.vue_settings and self.presenter_settings:
            self.presenter_settings.load_data()

        # Rafraichir le chronomètre (Page Principale)
        if hasattr(self, 'vue_chrono') and current_widget == self.vue_chrono and self.presenter_chrono:
            self.presenter_chrono.refresh()
        


    def create_accueil_widget(self):
        """Crée et retourne le widget de la page d'accueil."""
        self.vue_accueil = AccueilView()
        self.presenter_accueil = AccueilPresenter(self.vue_accueil, self.db)
        return self.vue_accueil
    
    def create_activites_widget(self):
        """Crée et retourne le widget de gestion des activités."""
        self.vue_activites = ActivitesView()
        self.presenter_activites = ActivitesPresenter(self.vue_activites, self.db)
        return self.vue_activites

    def create_analyses_widget(self):
        """Crée et retourne le widget d'analyse et de statistiques."""
        self.vue_analyses = AnalysesView()
        self.presenter_analyses = AnalysesPresenter(self.vue_analyses, self.db)
        return self.vue_analyses

    def create_settings_widget(self):
        """Crée et retourne le widget des paramètres."""
        self.vue_settings = SettingsView()
        self.presenter_settings = SettingsPresenter(self.vue_settings, self.db)
        return self.vue_settings


def resource_path(relative_path):
    """
    Retourne le chemin absolu vers une ressource.
    Fonctionne en mode développement et en mode exécutable PyInstaller.
    
    Args:
        relative_path: Chemin relatif vers la ressource
        
    Returns:
        Chemin absolu vers la ressource
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.dirname(__file__))

    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Chargement dynamique du style
    style_path = resource_path(os.path.join("style", "style.qss"))
    
    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            style_content = f.read()
            
            app.setStyleSheet(style_content)
            print(f"Design chargé avec succès ! (Source: {style_path})")
    else:
        print(f"Fichier style introuvable : {style_path}")

    ex = Application()
    ex.show()
    sys.exit(app.exec())