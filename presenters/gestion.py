from PySide6.QtWidgets import QInputDialog, QMessageBox, QDialog,  QWidget, QHBoxLayout, QLabel, QPushButton, QListWidgetItem, QLineEdit
from PySide6.QtCore import Qt, QSize
from vues.gestion import RoleDialog

class GestionPresenter:
    def __init__(self, view, model, return_callback):
        self.view = view
        self.model = model
        self.return_callback = return_callback
        
        # Suivi d'état
        self.current_mode = None # "user", "activity", "role"

        # --- Connexions Tableau de Bord ---
        self.view.btn_manage_users.clicked.connect(self.show_users)
        self.view.btn_manage_activities.clicked.connect(self.show_activities)
        self.view.btn_manage_roles.clicked.connect(self.show_roles)
        self.view.btn_back_home.clicked.connect(self.return_callback)

        # --- Connexions Vue Liste ---
        self.view.btn_back_dashboard.clicked.connect(self.go_dashboard)
        self.view.btn_add_item.clicked.connect(self.handle_add)

    def go_dashboard(self):
        self.view.stack.setCurrentIndex(0)
        self.current_mode = None

    def create_list_item(self, text, delete_callback):
        # Créer un élément pour la liste
        item = QListWidgetItem(self.view.list_widget)
        # Indice de taille ajusté pour des rangées plus petites
        item.setSizeHint(QSize(0, 70)) 
        
        # Widget personnalisé pour la rangée
        widget = QWidget()
        # Fond blanc pour effet de carte
        widget.setObjectName("admin_item_widget")
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(15, 0, 15, 0)
        layout.setAlignment(Qt.AlignVCenter) # Centrage vertical explicite
        
        lbl = QLabel(text)
        lbl.setObjectName("admin_item_label")
        layout.addWidget(lbl)
        
        layout.addStretch()
        
        # Bouton texte 'Supprimer' (Plat, texte coloré)
        btn_del = QPushButton("Supprimer")
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setFlat(True)
        # Utiliser une largeur minimale pour éviter de couper le texte
        btn_del.setMinimumWidth(180) 
        btn_del.setFixedHeight(50)
        btn_del.setObjectName("btn_delete_list_item")
        
        btn_del.clicked.connect(delete_callback)
        layout.addWidget(btn_del)
        
        self.view.list_widget.setItemWidget(item, widget)

    def show_users(self):
        self.current_mode = "user"
        self.view.set_title("Gestion des Utilisateurs")
        self.view.stack.setCurrentIndex(1)
        self.refresh_list()

    def show_activities(self):
        self.current_mode = "activity"
        self.view.set_title("Gestion des Activités")
        self.view.stack.setCurrentIndex(1)
        self.refresh_list()
        
    def show_roles(self):
        self.current_mode = "role"
        self.view.set_title("Gestion des Rôles")
        self.view.stack.setCurrentIndex(1)
        self.refresh_list()

    def refresh_list(self):
        self.view.list_widget.clear()
        
        if self.current_mode == "user":
            users = self.model.get_all_users()
            for u in users:
                # u = (id, nom, role)
                self.create_list_item(f"{u[1]} ({u[2]})", lambda checked=False, uid=u[0]: self.delete_user(uid))
                
        elif self.current_mode == "activity":
            acts = self.model.get_activities()
            act_map = {a[0]: a[1] for a in acts}
            for a in acts:
                # a = (id, libelle, parent_id)
                display_text = a[1]
                if a[2] and a[2] in act_map:
                    display_text += f" (sous {act_map[a[2]]})"
                self.create_list_item(display_text, lambda checked=False, aid=a[0]: self.delete_activity(aid))
                
        elif self.current_mode == "role":
            roles = self.model.get_all_roles() # liste de chaînes
            for r in roles:
                self.create_list_item(r, lambda checked=False, rname=r: self.delete_role(rname))

    def handle_add(self):
        if self.current_mode == "user":
            self.add_user()
        elif self.current_mode == "activity":
            self.add_activity()
        elif self.current_mode == "role":
            self.add_role_dialog()

    # --- Actions ---

    def add_user(self):
        nom, ok1 = QInputDialog.getText(self.view, "Utilisateur", "Nom d'utilisateur :")
        if ok1 and nom:
            mdp, ok2 = QInputDialog.getText(self.view, "Sécurité", "Mot de passe :", QLineEdit.Password)
            if ok2 and mdp:
                if len(mdp) < 8:
                    QMessageBox.warning(self.view, "Sécurité", "Le mot de passe est trop court.\nIl doit contenir au moins 8 caractères.")
                    return

                roles = self.model.get_all_roles()
                default_idx = roles.index("user") if "user" in roles else 0
                role, ok3 = QInputDialog.getItem(self.view, "Rôle", "Attribuer un rôle :", roles, default_idx, False)
                if ok3 and role:
                    self.model.add_user(nom, mdp, role)
                    self.refresh_list()

    def delete_user(self, uid):
        # Vérification pour éviter de supprimer 'admin' ou soi-même si nécessaire
        # On suppose que l'uid 1 est admin ou on vérifie via la logique, vérification simpliste pour l'instant
        # Mais on a besoin de savoir LEQUEL c'est plus robustement, ici on fait confiance à la logique d'ID ou on re-récupère pour vérifier le nom
        # Pour le MVP : essayer simplement de supprimer
        if uid == 1:
             QMessageBox.warning(self.view, "Err", "Impossible de supprimer l'admin principal.")
             return
             
        if QMessageBox.question(self.view, "Confirmer", "Supprimer cet utilisateur ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            self.model.delete_user(uid)
            self.refresh_list()

    def add_activity(self):
        nom, ok = QInputDialog.getText(self.view, "Activité", "Nom :")
        if ok and nom:
            # Proposer une activité parente
            acts = self.model.get_activities()
            # On construit la liste des choix
            choices = ["Aucun parent"] + [a[1] for a in acts]
            
            parent_name, ok_parent = QInputDialog.getItem(self.view, "Parent", "Activité parente (optionnel) :", choices, 0, False)
            
            parent_id = None
            if ok_parent and parent_name != "Aucun parent":
                # Retrouver l'ID via le nom (on suppose unicité ou on prend le premier trouvé)
                for a in acts:
                    if a[1] == parent_name:
                        parent_id = a[0]
                        break
            
            if parent_id:
                 if self.model.get_children_count(parent_id) >= 10:
                      QMessageBox.warning(self.view, "Limite atteinte", "Vous ne pouvez pas créer plus de 10 sous-activités pour une activité.")
                      return

            self.model.add_activity(None, nom, parent_id)
            self.refresh_list()

    def delete_activity(self, aid):
         if QMessageBox.question(self.view, "Confirmer", "Supprimer cette activité ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            self.model.delete_activity(aid)
            self.refresh_list()

    def add_role_dialog(self):
        # Réutilisation du dialogue personnalisé mais déclenché différemment
        dialog = RoleDialog(self.view)
        
        # Remplir les utilisateurs pour le dialogue ?
        # Attendez, l'utilisateur a demandé "gérer les rôles".
        # Le dialogue précédent était "Attribuer un rôle à l'utilisateur".
        # Si nous sommes dans "Gérer les rôles", peut-être voulons-nous juste créer une NOUVELLE définition de RÔLE ?
        # Mais les rôles sont liés à la table 'fonctions'. Créer un rôle implique juste de l'ajouter à cette table.
        # L'attribution c'est "Gérer l'utilisateur".
        # Donc "Ajouter un rôle" -> Juste demander le nom.
        
        code, ok = QInputDialog.getText(self.view, "Nouveau Rôle", "Nom du rôle (ex: MANAGER) :")
        if ok and code:
            self.model.add_role(code, code)
            self.refresh_list()

    def delete_role(self, rname):
        if rname in ["admin", "user"]:
            QMessageBox.warning(self.view, "Err", "Impossible de supprimer ce rôle système.")
            return
        if QMessageBox.question(self.view, "Confirmer", "Supprimer ce rôle ?", QMessageBox.Yes|QMessageBox.No) == QMessageBox.Yes:
            self.model.delete_role(rname)
            self.refresh_list()

