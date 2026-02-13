"""
Présentateur du chronomètre.
Gère la logique métier du chronomètre, des projets et des activités.
"""

from PySide6.QtCore import QTimer, QObject, Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox, QScrollArea, QWidget, QLabel

class ChronoPresenter(QObject):
    """
    Présentateur pour la vue du chronomètre.
    Gère le démarrage, l'arrêt, la pause et la sauvegarde des sessions de travail.
    """
    def __init__(self, view, model):
        super().__init__()
        self.view = view
        self.model = model
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        
        self.total_seconds = 0
        self.running = False
        self.current_task_id = None
        self.current_task_name = None
        self.current_project_id = None # ID du projet sélectionné
        
        # Connexions UI
        self.view.btn_stop.clicked.connect(self.handle_center_button)
        self.view.escape_pressed.connect(self.terminate_session)
        self.view.space_pressed.connect(self.handle_center_button)
        self.view.btn_add_project.clicked.connect(self.add_project)
        self.view.btn_delete_project.clicked.connect(self.delete_project)
        self.view.list_projects.itemClicked.connect(self.on_project_selected)
        
        # Connexion Gestion Affichage
        self.view.btn_manage_display.clicked.connect(self.open_display_dialog)
            
        self.load_projects()
        self.load_bubbles()
        
        # Charger configuration raccourcis
        self.update_shortcuts_config()

    def update_shortcuts_config(self):
        # 1. Defaults (Doit matcher ce qui est dans SettingsPresenter)
        actions = {
            "PAUSE_RESUME": "Space",
            "STOP_TIMER": "Esc"
        }
        for i in range(10):
            idx_str = str(i+1) if i < 9 else "0"
            actions[f"BUBBLE_{i}"] = f"Ctrl+{idx_str}"
            
        # 2. Overrides
        overrides = self.model.get_shortcut_overrides()
        if overrides:
            actions.update(overrides)
            
        self.view.set_shortcuts_config(actions)

    def load_projects(self):
        self.view.list_projects.clear()
        projects = self.model.get_projects()
        
        from PySide6.QtWidgets import QListWidgetItem
        
        for p in projects:
            p_id, p_nom, _, _ = p
            item = QListWidgetItem(p_nom)
            item.setData(Qt.UserRole, p_id)
            self.view.list_projects.addItem(item)
            
            if self.current_project_id == p_id:
                item.setSelected(True)

    def add_project(self):
        name = self.view.input_project.text().strip()
        if not name:
            return
            
        self.model.create_project(name)
        self.view.input_project.clear()
        self.load_projects()

    def on_project_selected(self, item):
        clicked_id = item.data(Qt.UserRole)
        
        if self.current_project_id == clicked_id:
            self.view.list_projects.clearSelection()
            self.view.list_projects.setCurrentItem(None)
            self.current_project_id = None
            print("Projet désélectionné")
        else:
            self.current_project_id = clicked_id
            print(f"Projet sélectionné : {item.text()} (ID: {self.current_project_id})")

    def delete_project(self):
        """Supprime le projet sélectionné après confirmation."""
        from vues.custom_dialog import CustomMessageBox
        
        selected_items = self.view.list_projects.selectedItems()
        if not selected_items:
            CustomMessageBox.warning(self.view, "Aucune sélection", 
                                    "Veuillez sélectionner un projet à supprimer.")
            return
        
        item = selected_items[0]
        project_id = item.data(Qt.UserRole)
        project_name = item.text()
        
        # Demander confirmation avec notre dialogue personnalisé
        result = CustomMessageBox.question(
            self.view, 
            "Confirmer la suppression",
            f"Voulez-vous vraiment supprimer le projet '{project_name}' ?\n\n"
            f"Les sessions associées seront conservées mais ne seront plus liées à ce projet."
        )
        
        if result:  # Si l'utilisateur a cliqué sur "Oui"
            try:
                self.model.delete_project(project_id)
                # Si le projet supprimé était sélectionné, le désélectionner
                if self.current_project_id == project_id:
                    self.current_project_id = None
                self.load_projects()
                print(f"Projet '{project_name}' supprimé avec succès")
            except Exception as e:
                CustomMessageBox.critical(self.view, "Erreur", 
                                        f"Erreur lors de la suppression du projet :\n{str(e)}")


    def load_bubbles(self):
        # Récupérer toutes les activités et les couleurs
        all_activities = self.model.get_activities() # (id, libelle, parent_id, color_id)
        all_colors = self.model.get_all_colors() # (id, nom, hex)
        
        # Récupérer les visibilités
        visible_ids = self.model.get_visible_activity_ids()
        
        # Map ID Couleur -> Hex
        color_map = {c[0]: c[2] for c in all_colors}
        
        # Couleurs par défaut (si aucune couleur définie)
        DEFAULT_COLORS = ["#4facfe", "#43e97b", "#fa709a", "#667eea", "#ff0844", "#fccb90"]
        
        # 1. Identifier les parents
        hierarchy = {}
        
        # D'abord les parents
        for a in all_activities:
            act_id, label, p_id, c_id = a
            
            if p_id is None:
                # Filtrage : Si des activités sont marquées visibles, on filtre. Sinon on montre tout
                if visible_ids and act_id not in visible_ids:
                    continue

                # Résolution couleur
                if c_id and c_id in color_map:
                    color_hex = color_map[c_id]
                else:
                    color_hex = DEFAULT_COLORS[act_id % len(DEFAULT_COLORS)]
                    
                hierarchy[act_id] = {'id': act_id, 'label': label, 'color': color_hex, 'children': []}
                
        # Ensuite les enfants
        for a in all_activities:
            act_id, label, p_id, c_id = a
            
            if p_id is not None and p_id in hierarchy:
                # Résolution couleur
                if c_id and c_id in color_map:
                    color_hex = color_map[c_id]
                else:
                    # Héritage parent (qui a déjà une couleur par défaut ou définie)
                    color_hex = hierarchy[p_id]['color']
                    
                hierarchy[p_id]['children'].append({'id': act_id, 'label': label, 'color': color_hex})
        
        # Limitation 10 enfants max par parent
        for p_data in hierarchy.values():
            if len(p_data['children']) > 10:
                p_data['children'] = p_data['children'][:10]
        
        data_for_view = list(hierarchy.values())
        self.view.set_activities(data_for_view, self.handle_bubble_click)

    def open_display_dialog(self):
        from vues.chrono import SelectionDialog
        dialog = SelectionDialog(self.view, "Sélection des activités (Max 10)")
        # dialog.setMinimumWidth(300) # Géré par SelectionDialog
        # dialog.setMinimumHeight(400)
        
        layout = dialog.content_layout
        
        # scroll bar 
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        container.setObjectName("dialog_container")
        vbox = QVBoxLayout(container)
        
        activities = self.model.get_activities()
        visible_ids = self.model.get_visible_activity_ids()
        
        # On ne liste que les parents pour le choix
        parents = [a for a in activities if a[2] is None]
        checkboxes = []
        
        for p in parents:
            p_id = p[0]
            p_label = p[1]
            
            cb = QCheckBox(p_label)
           
            if p_id in visible_ids:
                cb.setChecked(True)
                
            cb.setProperty("act_id", p_id)
            checkboxes.append(cb)
            vbox.addWidget(cb)
            
            # Gestion du max 10
            cb.stateChanged.connect(lambda state, c=cb: self.check_limit(checkboxes))

        vbox.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)
        
        # Boutons
        btn_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)
        layout.addWidget(btn_box)
        
        self.check_limit(checkboxes) # Init state check
        
        if dialog.exec() == QDialog.Accepted:
            selected_ids = [cb.property("act_id") for cb in checkboxes if cb.isChecked()]
            self.model.set_visible_activities(selected_ids)
            self.load_bubbles()

    def check_limit(self, checkboxes):
        checked = [cb for cb in checkboxes if cb.isChecked()]
        count = len(checked)
        
        # Si >= 10, on désactive les non-cochés
        full = count >= 10
        
        for cb in checkboxes:
            if not cb.isChecked():
                cb.setEnabled(not full)
                

    def handle_bubble_click(self, act_id, name, is_parent):
        """Dispatche l'action selon que c'est un parent ou un enfant"""
        
        if is_parent:
            # On vérifie si ce parent a des enfants en BDD
            has_children = self.model.has_children(act_id)
            if has_children:
                self.view.set_focus_parent(act_id)
                print(f"Focus sur parent : {name}")
            else:
                # Le parent n'a pas d'enfants (0 ou NULL) -> On le traite comme une activité
                print(f"Parent sans enfant détecté : Lancement de {name}")
                self.start_activity(act_id, name)
        else:
            # C'est un enfant -> On lance le chrono
            self.start_activity(act_id, name)


    def start_activity(self, act_id, name):
        """Lance une nouvelle session (Arrête la précédente si existante)"""
        
        # Si une tâche est déjà select (En cours ou en Pause), on la sauvegarde et on clean
        if self.current_task_id is not None:
             self.terminate_session()
             
        self.current_task_id = act_id
        self.current_task_name = name
        self.total_seconds = 0
        
        self.running = True
        self.timer.start(1000)
        
        # Mise à jour de l'interface
        self.view.update_time("00:00:00")
        self.view.set_activity_name(name)
        
        # Fermer le menu (reset focus)
        self.view.reset_focus()

        print(f"Démarrage activité : {name} (Projet ID: {self.current_project_id})")
        
        # Focus sur la vue pour capter Echap/Espace
        self.view.setFocus()

    def handle_center_button(self):
        """Gère le clic sur le bouton central OU ESPACE (Pause / Reprendre)"""
        if self.current_task_id is None:
            return # Rien à pauser si pas de tache

        if self.running:
            # Mettre en pause
            self.running = False
            self.timer.stop()
            print(f"Pause activité : {self.current_task_name}")
        else:
            # Reprendre
            self.running = True
            self.timer.start(1000)
            print(f"Reprise activité : {self.current_task_name}")
            
        self.update_display() # Mettre à jour état bouton / status accueil

    def terminate_session(self):
        """Arrêt définitif et sauvegarde (Appelé par Echap ou changement d'activité)"""
        # On arrête tout
        self.running = False
        self.timer.stop()
        self.view.btn_stop.hide()
        
        if self.current_task_id and self.total_seconds > 0:
             try:
                # Ajout du project_id ici
                self.model.save_session(self.current_task_id, self.current_task_name, self.total_seconds, self.current_project_id)
                print(f"Activité {self.current_task_name} enregistrée en base. Durée : {self.total_seconds}s. Projet: {self.current_project_id}")
             except Exception as e:
                 print(f"Erreur lors de la sauvegarde : {e}")
             
        # Réinitialisation complète de l'état
        self.current_task_id = None
        self.total_seconds = 0  # CORRECTION : Réinitialisation du compteur
        self.view.update_time("00:00:00")
        self.view.set_activity_name("")
        
        # Reset visuel focus
        self.view.reset_focus()
        
        # Reset accueil (remise à zero si stop) ou juste update status
        self.update_display()
        if hasattr(self, 'accueil_presenter') and self.accueil_presenter:
             self.accueil_presenter.update_chrono_state("00:00:00", "En pause")

    def tick(self):
        self.total_seconds += 1
        self.update_display()
        # Mettre à jour l'accueil si possible
        self.update_chrono_in_accueil()

    def update_chrono_in_accueil(self):
        if hasattr(self, 'accueil_presenter') and self.accueil_presenter:
            # Cette méthode tick appelle update_display qui appelle déjà update_chrono_state
            # Donc si set_accueil_presenter est fait, update_display suffit.
            # Cependant, si l'arrêt se produit, on veut aussi mettre à jour.
            pass 
    
    def set_accueil_presenter(self, accueil_presenter):
        self.accueil_presenter = accueil_presenter

    
    def refresh(self):
        """Recharge toutes les données (Projets, Bulles, Raccourcis)"""
        self.load_projects()
        self.load_bubbles()
        self.update_shortcuts_config()

    def update_display(self):
        h, m = divmod(self.total_seconds, 3600)
        m, s = divmod(m, 60)
        text = f"{h:02d}:{m:02d}:{s:02d}"
        self.view.update_time(text)
        
        if hasattr(self, 'accueil_presenter') and self.accueil_presenter:
            status = f"En cours : {self.current_task_name}" if self.running else "En pause"
            self.accueil_presenter.update_chrono_state(text, status)
