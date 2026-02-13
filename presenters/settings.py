from PySide6.QtWidgets import QColorDialog, QListWidgetItem, QMessageBox
from PySide6.QtCore import Qt, QObject

class SettingsPresenter(QObject):

    def __init__(self, view, model):
        super().__init__()
        self.view = view
        self.model = model
        
        # Actions définies par le système (Action Code -> Defaut)
        self.ACTIONS = {
            "PAUSE_RESUME": {"label": "Pause / Reprendre", "default": "Space"},
            "STOP_TIMER":   {"label": "Arrêter Timer", "default": "Esc"},
        }
        # Ajout dynamique des bulles
        for i in range(1, 11):
             idx = i-1
             if i < 10:
                 self.ACTIONS[f"BUBBLE_{idx}"] = {"label": f"Sélectionner Bulle {i}", "default": f"Ctrl+{i}"}
             else:
                 self.ACTIONS[f"BUBBLE_{idx}"] = {"label": f"Sélectionner Bulle 10", "default": "Ctrl+0"}

        self.view.btn_edit_shortcut.clicked.connect(self.edit_shortcut)
        self.view.btn_del_shortcut.hide() # On ne supprime pas les actions système pour l'instant

        # Initial load
        self.load_data()
       
    def load_data(self):
        self.load_shortcuts()

    def load_shortcuts(self):
        from PySide6.QtWidgets import QTreeWidgetItem
        
        self.view.list_shortcuts.clear()
        
        overrides = self.model.get_shortcut_overrides()
        
        for code, details in self.ACTIONS.items():
            label = details["label"]
            shortcut = overrides.get(code, details["default"])
            
            # Item avec 2 colonnes
            item = QTreeWidgetItem([label, shortcut])
            item.setData(0, Qt.UserRole, code) # On stocke le CODE sur la colonne 0
            
            # Style subtil pour la colonne raccourci
            # item.setTextAlignment(1, Qt.AlignCenter) 
            
            self.view.list_shortcuts.addTopLevelItem(item)

    def edit_shortcut(self):
        selected_items = self.view.list_shortcuts.selectedItems()
        if not selected_items:
            QMessageBox.information(self.view, "Info", "Sélectionnez un raccourci à modifier.")
            return

        item = selected_items[0]
        code = item.data(0, Qt.UserRole)
        details = self.ACTIONS.get(code)
        
        if not details: 
            return

        from vues.settings import KeyCaptureDialog
        dlg = KeyCaptureDialog(self.view, details["label"])
        
        if dlg.exec():
            new_sequence = dlg.get_sequence()
            if not new_sequence:
                return

            # --- Détection de doublons ---
            # 1. Obtenir l'état actuel de tous les raccourcis
            overrides = self.model.get_shortcut_overrides()
            
            # 2. Chercher qui utilise déjà cette séquence
            conflict_code = None
            
            for action_code, action_details in self.ACTIONS.items():
                # Le raccourci actuel pour cette action est soit l'override, soit le défaut
                current_seq = overrides.get(action_code, action_details["default"])
                
                if current_seq == new_sequence:
                    conflict_code = action_code
                    break
            
            # 3. Si conflit trouvé (et ce n'est pas nous-mêmes)
            if conflict_code and conflict_code != code:
                conflict_label = self.ACTIONS[conflict_code]["label"]
                
                reply = QMessageBox.question(
                    self.view, 
                    "Raccourci déjà utilisé", 
                    f"Le raccourci '{new_sequence}' est déjà utilisé pour '{conflict_label}'.\n\nVoulez-vous le remplacer ?\n(L'ancien raccourci sera supprimé)",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.No:
                    return # Annuler tout
                
                # Si Oui, on "vide" le raccourci de l'action en conflit
                self.model.update_shortcut(conflict_code, "")
            
            # 4. Sauvegarder le nouveau raccourci
            self.model.update_shortcut(code, new_sequence)
            self.load_shortcuts()

    def delete_shortcut(self):
        pass # Disactivé pour le moment
