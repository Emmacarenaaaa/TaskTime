"""
Présentateur de la page d'accueil.
Gère l'affichage des activités récentes et du chronomètre.
"""

class AccueilPresenter:
    """Présentateur pour la vue d'accueil."""
    
    def __init__(self, view, db):
        self.view = view
        self.db = db
        self.refresh()
        
    def refresh(self):
        """Rafraîchit l'affichage des activités récentes."""
        history = self.db.get_history()
        if hasattr(self.view, 'update_recap'):
             self.view.update_recap(history)

    def update_chrono_state(self, time_text, status_text=None):
        """Met à jour l'affichage du chronomètre dans la vue."""
        if hasattr(self.view, 'update_chrono'):
            self.view.update_chrono(time_text, status_text)
