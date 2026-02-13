from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QFrame, QStackedWidget, QSizePolicy)
from PySide6.QtCore import Qt, Signal, QSize, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon
import os

# Chemin vers le dossier des icônes
ICON_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons")

class SidebarButton(QPushButton):
    """
    Bouton personnalisé pour la barre latérale.
    Hérite de QPushButton et ajoute la gestion de l'état réduit (collapsed).
    """
    def __init__(self, text, icon_name=None, parent=None):
        super().__init__(text, parent)
        self.original_text = text
        self.setCheckable(True) # Le bouton peut être coché (état actif)
        self.setAutoExclusive(True) # Un seul bouton coché à la fois dans le groupe
        self.setFixedHeight(50) # Hauteur fixe
        self.setCursor(Qt.PointingHandCursor) # Curseur main au survol
        self.setObjectName("sidebar_btn") # Pour le style CSS
        
        if icon_name:
            self.setIcon(QIcon(os.path.join(ICON_DIR, icon_name)))
            self.setIconSize(QSize(24, 24))

    def set_collapsed(self, collapsed):
        """
        Gère l'affichage du bouton selon si la barre latérale est réduite ou non.
        """
        self.setProperty("collapsed", collapsed)
        # Forcer la mise à jour du style
        self.style().unpolish(self)
        self.style().polish(self)
        
        if collapsed:
            self.setText("") # Masquer le texte
            self.setToolTip(self.original_text) # Afficher le texte en info-bulle
        else:
            self.setText(self.original_text) # Afficher le texte
            self.setToolTip("") # Masquer l'info-bulle

class DashboardView(QWidget):
    """
    Vue principale du tableau de bord.
    Contient la barre latérale de navigation et la zone de contenu principale.
    """
    def __init__(self):
        """Initialise la vue du tableau de bord"""
        super().__init__()
        
        self.setObjectName("page_dashboard")
        
        # Disposition principale horizontale (Sidebar + Contenu)
        self.layout_main = QHBoxLayout(self)
        self.layout_main.setContentsMargins(0, 0, 0, 0)
        self.layout_main.setSpacing(0)
        
        # --- 1. Barre Latérale (Sidebar) ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(250)
        self.layout_sidebar = QVBoxLayout(self.sidebar)
        self.layout_sidebar.setContentsMargins(10, 20, 10, 20)
        self.layout_sidebar.setSpacing(10)
        
        # Header (Marque + Toggle)
        self.layout_header = QHBoxLayout()
        self.layout_header.setContentsMargins(0, 0, 0, 0)
        
        # Marque (Brand)
        self.lbl_brand = QLabel("TaskTime")
        self.lbl_brand.setObjectName("lbl_brand")
        self.layout_header.addWidget(self.lbl_brand)
        
        # Espaceur central (Variable)
        self.header_spacer_middle = QWidget()
        self.header_spacer_middle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.layout_header.addWidget(self.header_spacer_middle)
        
        # Bouton Toggle Collapse
        self.btn_toggle = QPushButton()
        self.btn_toggle.setIcon(QIcon(os.path.join(ICON_DIR, "menu.svg")))
        self.btn_toggle.setFixedSize(40, 40) # Plus gros
        self.btn_toggle.setIconSize(QSize(24, 24))
        self.btn_toggle.setObjectName("btn_toggle_sidebar")
        self.btn_toggle.setCheckable(True)
        self.btn_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_toggle.clicked.connect(self.toggle_sidebar) 
        self.layout_header.addWidget(self.btn_toggle)
        
        self.layout_sidebar.addLayout(self.layout_header)
        
        self.layout_sidebar.addSpacing(20)
        
        # Boutons de Navigation
        self.btn_accueil = SidebarButton("Accueil", "home.svg") 
        self.btn_chrono = SidebarButton("Chrono", "clock.svg")
        self.btn_activites = SidebarButton("Activités", "activity.svg")
        self.btn_analyses = SidebarButton("Analyses", "chart.svg")
        self.btn_settings = SidebarButton("Réglages", "settings.svg")
        
        self.layout_sidebar.addWidget(self.btn_accueil)
        self.layout_sidebar.addWidget(self.btn_chrono)
        self.layout_sidebar.addWidget(self.btn_activites)
        self.layout_sidebar.addWidget(self.btn_analyses)
        self.layout_sidebar.addWidget(self.btn_settings)
        
        # Espace flexible
        self.layout_sidebar.addStretch()
        
        self.layout_main.addWidget(self.sidebar)
        
        # --- 2. Zone de Contenu Principale ---
        self.content_area = QWidget()
        self.content_area.setObjectName("content_area")
        self.layout_content = QVBoxLayout(self.content_area)
        self.layout_content.setContentsMargins(20, 20, 20, 20) 
        
        # Pile de pages (Stacked Widget)
        self.stack = QStackedWidget()
        self.layout_content.addWidget(self.stack)
        
        self.layout_main.addWidget(self.content_area)
        
        # --- Connexions ---
        self.btn_accueil.clicked.connect(lambda: self.switch_page(0))
        self.btn_chrono.clicked.connect(lambda: self.switch_page(1))
        self.btn_activites.clicked.connect(lambda: self.switch_page(2))
        self.btn_analyses.clicked.connect(lambda: self.switch_page(3))
        self.btn_settings.clicked.connect(lambda: self.switch_page(4))
        
        self.btn_accueil.setChecked(True) # Accueil par défaut
        
        self.is_collapsed = False

    def toggle_sidebar(self):
        if not self.is_collapsed:
            self.animate_sidebar(70) # Taille réduite
        else:
            self.animate_sidebar(250) # Taille normale
        self.is_collapsed = not self.is_collapsed

    def animate_sidebar(self, target_width):
        """
        Anime le changement de largeur de la barre latérale.
        Met également à jour la visibilité des textes et l'état des boutons.
        """
        current_width = self.sidebar.width()
        
        is_target_collapsed = (target_width < 150)
        
        # Animation de la largeur minimale (pour forcer le changement)
        self.anim_min = QPropertyAnimation(self.sidebar, b"minimumWidth")
        self.anim_min.setDuration(300)
        self.anim_min.setStartValue(current_width)
        self.anim_min.setEndValue(target_width)
        self.anim_min.setEasingCurve(QEasingCurve.InOutQuart)
        
        # Animation de la largeur maximale
        self.anim_max = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self.anim_max.setDuration(300)
        self.anim_max.setStartValue(current_width)
        self.anim_max.setEndValue(target_width)
        self.anim_max.setEasingCurve(QEasingCurve.InOutQuart)
        
        self.anim_min.start()
        self.anim_max.start()
        
        # Afficher/Masquer le titre "TaskTime" et ajuster le layout
        if is_target_collapsed:
            self.lbl_brand.hide()
            self.header_spacer_middle.hide() # Cache l'espaceur central
            self.layout_header.setAlignment(Qt.AlignCenter) # Centre le contenu restant (bouton)
        else:
            self.lbl_brand.show()
            self.header_spacer_middle.show() # Montre l'espaceur central
            self.layout_header.setAlignment(Qt.AlignJustify) # Rétablit l'alignement
        
        # Mettre à jour l'apparence des boutons (texte vs icône seule)
        buttons = [self.btn_accueil, self.btn_chrono, self.btn_activites, 
                   self.btn_analyses, self.btn_settings]
            
        for btn in buttons:
            btn.set_collapsed(is_target_collapsed)

    def set_content_pages(self, page_accueil, page_chrono, page_activites, page_analyses, page_settings):
        """
        Remplit le QStackedWidget avec les différentes vues.
        """
        self.stack.addWidget(page_accueil)      # Index 0
        self.stack.addWidget(page_chrono)       # Index 1
        self.stack.addWidget(page_activites)    # Index 2
        self.stack.addWidget(page_analyses)     # Index 3
        self.stack.addWidget(page_settings)     # Index 4

    def switch_page(self, index):
        """
        Change la page affichée dans la zone de contenu et met à jour l'état des boutons.
        """
        # Met à jour l'état 'checked' des boutons
        self.btn_accueil.setChecked(index == 0)
        self.btn_chrono.setChecked(index == 1)
        self.btn_activites.setChecked(index == 2)
        self.btn_analyses.setChecked(index == 3)
        self.btn_settings.setChecked(index == 4)
             
        # Change la page dans le QStackedWidget si l'index est valide
        if index < self.stack.count():
             self.stack.setCurrentIndex(index)
             # Donner le focus à la page actuelle pour que les raccourcis clavier fonctionnent immédiatement
             current_widget = self.stack.currentWidget()
             if current_widget:
                 current_widget.setFocus()


