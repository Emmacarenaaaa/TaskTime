from PySide6.QtWidgets import QTreeWidgetItem, QMessageBox, QPushButton, QWidget, QHBoxLayout
from PySide6.QtGui import QColor, QBrush, Qt

class ActivitesPresenter:
    def __init__(self, view, model):
        self.view = view
        self.model = model
        
        self.is_editing = False
        self.edit_id = None
        
        # Connexions
        self.view.btn_add.clicked.connect(self.save_activity)
        self.view.btn_delete.clicked.connect(self.delete_activity)
        
        # Connection du changement de sélection
        self.view.tree.itemSelectionChanged.connect(self.on_selection_changed)
        
        self.refresh()

    def refresh(self):
        self.view.tree.blockSignals(True)
        self.update_list()
        self.update_parents_combo() 
        self.view.tree.blockSignals(False)
        self.reset_form_state()

    def reset_form_state(self):
        self.is_editing = False
        self.edit_id = None
        self.view.clear_form()
        self.view.btn_add.setText("Ajouter")

    def on_selection_changed(self):
        # Cancel delete confirmation if selection changes
        if hasattr(self, '_delete_confirm_id'):
            self._delete_confirm_id = None
            self.view.clear_message()
            
        selected = self.view.tree.selectedItems()
        if not selected:
            self.reset_form_state()
            return
            
        item = selected[0]
        # ID is now in column 2
        act_id = int(item.text(2))
        
        act_data = self.model.get_activity(act_id)
        if act_data:
            _, name, parent_id, color_id = act_data
            
            self.is_editing = True
            self.edit_id = act_id
            # On ne passe plus la couleur au formulaire
            self.view.set_form_data(name, parent_id)
            self.view.btn_add.setText("Modifier")

    def update_list(self):
        self.view.tree.clear()
        activities = self.model.get_activities()
        colors_db = self.model.get_all_colors()
        colors_map = {c[0]: c[2] for c in colors_db} 
        
        DEFAULT_COLORS = ["#4facfe", "#43e97b", "#fa709a", "#667eea", "#ff0844", "#fccb90"]
        
        items_map = {}
        act_data = {}
        
        for a in activities:
             a_id, libelle, p_id, c_id = a
             act_data[a_id] = {'libelle': libelle, 'parent_id': p_id, 'color_id': c_id, 'item': None}

        for act_id, data in act_data.items():
            # Colonnes: [Libelle, (Widget Couleur), ID]
            item = QTreeWidgetItem([data['libelle'], "", str(act_id)])
            
            p_id = data['parent_id']
            is_child = (p_id and p_id in act_data)

            # Logique de Couleur : Parents -> Propre Config, Enfants -> Héritage Strict
            hex_code = None
            
            if is_child:
                # Force Parent Color
                p_data = act_data[p_id]
                p_cid = p_data['color_id']
                if p_cid and p_cid in colors_map:
                    hex_code = colors_map[p_cid]
                else:
                    hex_code = DEFAULT_COLORS[p_id % len(DEFAULT_COLORS)]
            else:
                # Parent Logic
                c_id = data['color_id']
                if c_id and c_id in colors_map:
                    hex_code = colors_map[c_id]
                else:
                    hex_code = DEFAULT_COLORS[act_id % len(DEFAULT_COLORS)]
            
            data['item'] = item
            data['final_color'] = hex_code # Stockage pour usage widget
            items_map[act_id] = item

        # Construction Arbre
        from PySide6.QtWidgets import QLabel # Import local pour éviter modif header

        for act_id, data in act_data.items():
            parent_id = data['parent_id']
            item = data['item']
            
            if parent_id and parent_id in items_map:
                items_map[parent_id].addChild(item)
                items_map[parent_id].setExpanded(True)
            else:
                self.view.tree.addTopLevelItem(item)
                
            # Widget de couleur
            container = QWidget()
            layout_c = QHBoxLayout(container)
            layout_c.setContentsMargins(0, 0, 0, 0)
            layout_c.setAlignment(Qt.AlignCenter)
            
            color_hex = data['final_color']
            
            if parent_id: # C'est un enfant -> Badge statique
                lbl = QLabel()
                lbl.setFixedSize(24, 24)
                lbl.setStyleSheet(f"background-color: {color_hex}; border-radius: 12px; border: 1px solid #ccc;")
                lbl.setToolTip("Couleur héritée du parent")
                layout_c.addWidget(lbl)
            else: # C'est un parent -> Bouton éditable
                btn = QPushButton()
                btn.setFixedSize(24, 24)
                btn.setCursor(Qt.PointingHandCursor)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {color_hex};
                        border: 1px solid #ccc;
                        border-radius: 12px;
                    }}
                    QPushButton:hover {{
                        border: 2px solid #555;
                    }}
                """)
                btn.setToolTip(f"Modifier la couleur ({color_hex})")
                btn.clicked.connect(lambda checked=False, aid=act_id: self.change_activity_color(aid))
                layout_c.addWidget(btn)
            
            self.view.tree.setItemWidget(item, 1, container)


    def update_parents_combo(self):
        """Met à jour la liste des parents possibles (uniquement les activités de niveau racine)."""
        activities = self.model.get_activities()
        # CORRECTION : Ne proposer que les activités sans parent (niveau racine)
        # pour éviter de créer des sous-activités de sous-activités
        choices = [(a[0], a[1]) for a in activities if a[2] is None]  # a[2] = parent_id
        self.view.set_parents_choices(choices)

    def change_activity_color(self, act_id):
        """Ouvre le sélecteur de couleur personnalisé."""
        from vues.color_picker import ColorPicker
        
        # Récupérer la couleur actuelle
        act_data = self.model.get_activity(act_id)
        current_color = None
        if act_data and act_data[3]:  # color_id
            colors_db = self.model.get_all_colors()
            colors_map = {c[0]: c[2] for c in colors_db}
            if act_data[3] in colors_map:
                current_color = QColor(colors_map[act_data[3]])
        
        # Ouvrir le sélecteur
        color = ColorPicker.get_color_from_user(self.view, current_color)
        
        if color and color.isValid():
            hex_code = color.name()
            color_id = self.resolve_color_id(hex_code)
            self.model.update_activity_color(act_id, color_id)
            self.refresh()

    def resolve_color_id(self, hex_code):
        if not hex_code:
            return None
        colors = self.model.get_all_colors()
        for c in colors:
             if c[2].lower() == hex_code.lower():
                 return c[0]
        new_id = self.model.add_color(hex_code, hex_code)
        return new_id

    def save_activity(self):
        # Clear previous messages
        self.view.clear_message()

        name, parent_id, _ = self.view.get_new_activity_data()
        
        if not name:
            self.view.show_error("Le nom ne peut pas être vide.")
            return

        # CORRECTION : Vérifier que le parent sélectionné n'est pas lui-même un enfant
        if parent_id:
            parent_data = self.model.get_activity(parent_id)
            if parent_data and parent_data[2] is not None:  # parent_data[2] = parent_id du parent
                self.view.show_error("Impossible : vous ne pouvez créer qu'un seul niveau de sous-activités.")
                return

        if self.edit_id: # Mode Edition
            if parent_id == self.edit_id:
                self.view.show_error("Une activité ne peut pas être son propre parent.")
                return
            
            # Récupérer données existantes
            curr = self.model.get_activity(self.edit_id)
            if not curr: return
            
            curr_color_id = curr[3]
            old_parent_id = curr[2]
            
            # Check limit if changing parent
            if parent_id and parent_id != old_parent_id:
                count = self.model.get_children_count(parent_id)
                if count >= 10:
                    self.view.show_error("Ce parent a déjà 10 sous-activités.")
                    return
            
            self.model.update_activity(self.edit_id, name, parent_id, curr_color_id)
            self.view.show_success("Activité modifiée avec succès.")
        else: # Mode Ajout
            if parent_id:
                count = self.model.get_children_count(parent_id)
                if count >= 10:
                    self.view.show_error("Vous ne pouvez pas créer plus de 10 sous-activités.")
                    return

            self.model.add_activity(name, parent_id, None)
            self.view.show_success("Activité ajoutée avec succès.")
            
        self.refresh()
        # Reset form after delay or immediately? For now immediately via refresh->reset_form_state
        # But refresh clears the form. If I want to show success message, I should keep it visible.
        # refresh calls `reset_form_state` which calls `view.clear_form`.
        # I should probably let the success message stay until next interaction or clear it after a few seconds using QTimer.
        # For simplicity, I'll just show it. If `refresh` clears form, that's fine, message label is separate.
        # But `reset_form_state` might not clear message label if I didn't add it there.
        # Let's check `reset_form_state` at line 28. It calls `self.view.clear_form()`.
        # `view.clear_form` clears inputs.
        # `view.clear_message` is separate.
        # So message will persist. I should clear it when selection changes or editing starts.
        
    def delete_activity(self):
        selected = self.view.tree.selectedItems()
        if not selected:
            return
            
        item = selected[0]
        act_id = int(item.text(2))
        nom = item.text(0)
        
        # Check if we're in confirmation mode for this specific activity
        if hasattr(self, '_delete_confirm_id') and self._delete_confirm_id == act_id:
            # User confirmed, proceed with deletion
            self.model.delete_activity(act_id)
            self._delete_confirm_id = None
            self.view.clear_message()
            self.refresh()
        else:
            # First click - ask for confirmation inline
            self._delete_confirm_id = act_id
            msg = f"Supprimer '{nom}' ?"
            if item.childCount() > 0:
                msg += " (et ses sous-activités)"
            msg += " Cliquez à nouveau pour confirmer."
            self.view.show_error(msg)
