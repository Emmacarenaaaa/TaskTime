"""
Vue de la page d'accueil de TaskTime.
Affiche un aperçu du chronomètre en cours et les activités récentes.
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QListWidget, QListWidgetItem, QPushButton, QFrame)
from PySide6.QtCore import Qt


class MiniChronoCard(QFrame):
    """Widget affichant un aperçu du chronomètre en cours."""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("mini_chrono_card")
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        
        lbl_titre = QLabel("Aperçu Chrono")
        lbl_titre.setObjectName("lbl_mini_chrono_title")
        layout.addWidget(lbl_titre)
        
        self.lbl_time = QLabel("00:00:00")
        self.lbl_time.setObjectName("lbl_mini_chrono_time")
        self.lbl_time.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.lbl_time)
        
        self.lbl_info = QLabel("En pause")
        self.lbl_info.setObjectName("lbl_info")
        layout.addWidget(self.lbl_info)

    def update_display(self, time_text, status_text=None):
        """Met à jour l'affichage du temps et du statut."""
        self.lbl_time.setText(time_text)
        if status_text:
            self.lbl_info.setText(status_text)

class RecapCard(QFrame):
    """Widget affichant la liste des activités récentes."""
    def __init__(self):
        super().__init__()
        self.setObjectName("recap_card")
        
        layout = QVBoxLayout(self)
        
        lbl_title = QLabel("Activités Récentes")
        lbl_title.setObjectName("lbl_recap_title")
        layout.addWidget(lbl_title)
        
        self.list_widget = QListWidget()
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        self.list_widget.setObjectName("recap_list_widget")
        layout.addWidget(self.list_widget)

    def set_activities(self, activities):
        """Affiche la liste des activités récentes."""
        self.list_widget.clear()
        
        if not activities:
            item = QListWidgetItem("Aucune activité récente. Lancez un chrono !")
            item.setTextAlignment(Qt.AlignCenter)
            self.list_widget.addItem(item)
            return

        # On affiche les 10 dernières
        for act in activities[:10]:
            # act = (date, libelle, nom_saisi, duree)
            # get_history returns: SELECT s.date, a.libelle, s.nom_saisi, s.duree
            date_str = act[0]
            activite_nom = act[1]  # libelle
            duree_sec = int(act[3])  # duree is at index 3
            
            # Extract time from date_str
            try:
                time_part = date_str.split(' ')[1][:5]  # Get HH:MM
            except:
                time_part = "??:??"
            
            # Format duration
            m, s = divmod(duree_sec, 60)
            h, m = divmod(m, 60)
            if h > 0:
                dur_str = f"{h}h{m:02d}m"
            else:
                dur_str = f"{m}min"
            
            # Create item text
            item_text = f"{activite_nom} - {time_part} ({dur_str})"
            item = QListWidgetItem(item_text)
            self.list_widget.addItem(item)


class AccueilView(QWidget):
    """Vue principale de la page d'accueil."""
    def __init__(self):
        super().__init__()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)
        
        # Titre de la page
        lbl_welcome = QLabel("Bienvenue sur votre Tableau de Bord")
        lbl_welcome.setObjectName("lbl_welcome")
        main_layout.addWidget(lbl_welcome)
        
        # Zone Contenu
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Gauche : Mini Chrono (plus petit)
        self.mini_chrono = MiniChronoCard()
        # self.mini_chrono.setFixedWidth(250) # Removed fixed width
        # self.mini_chrono.setFixedHeight(200) # Removed fixed height
        self.mini_chrono.setMinimumWidth(250) # Ensure it doesn't get too small
        content_layout.addWidget(self.mini_chrono, 1) # Stretch factor 1
        
        # Droite : Recap (prend le reste)
        self.recap_card = RecapCard()
        content_layout.addWidget(self.recap_card, 2) # Stretch factor 2
        
        main_layout.addLayout(content_layout)
        main_layout.addStretch()

    def update_recap(self, activities):
        """Met à jour la liste des activités récentes."""
        self.recap_card.set_activities(activities)

    def update_chrono(self, time_text, status_text=None):
        """Met à jour l'affichage du chronomètre."""
        self.mini_chrono.update_display(time_text, status_text)
