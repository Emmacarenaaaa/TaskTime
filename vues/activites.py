from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                                 QLabel, QTreeWidget, QTreeWidgetItem, QLineEdit, 
                                 QComboBox, QHeaderView, QFrame, QGraphicsDropShadowEffect) # QMessageBox removed
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap, QIcon

class ActivitesView(QWidget):
    def __init__(self):
        super().__init__()
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(40, 40, 40, 40)
        self.layout.setSpacing(25)

        # Titre
        self.lbl_title = QLabel("Gestion des Activités")
        self.lbl_title.setObjectName("lbl_titre") # Use standard title ID
        self.layout.addWidget(self.lbl_title)



        # Zone d'ajout (Card style)
        self.panel_add = QFrame()
        self.panel_add.setObjectName("card_add")
        # Style managed in QSS
        
        self.layout_add = QHBoxLayout(self.panel_add)
        self.layout_add.setContentsMargins(20, 20, 20, 20)
        self.layout_add.setSpacing(15)
        
        self.input_name = QLineEdit()
        self.input_name.setObjectName("input_name_activites")
        self.input_name.setPlaceholderText("Nom (max 11 chars)...")
        self.input_name.setMaxLength(11)
        self.input_name.setMinimumHeight(45)
        
        self.combo_parents = QComboBox()
        self.combo_parents.setObjectName("combo_parents_activites")
        self.combo_parents.setMinimumHeight(45)
        self.combo_parents.setMinimumWidth(220)

        self.btn_add = QPushButton("Ajouter")
        self.btn_add.setObjectName("btn_add_activites")
        self.btn_add.setMinimumHeight(45)
        self.btn_add.setCursor(Qt.PointingHandCursor)
        
        self.layout_add.addWidget(self.input_name)
        self.layout_add.addWidget(self.combo_parents)
        self.layout_add.addWidget(self.btn_add)
        
        self.layout.addWidget(self.panel_add)

        # Zone de message inline (Alertes) - Entre le formulaire et la liste
        self.lbl_message = QLabel("")
        self.lbl_message.setObjectName("lbl_message_inline")
        self.lbl_message.setAlignment(Qt.AlignCenter)
        self.lbl_message.hide() # Caché par défaut
        self.layout.addWidget(self.lbl_message)

        # Liste arborescente
        self.tree = QTreeWidget()
        self.tree.setObjectName("tree_activites")
        self.tree.setHeaderLabels(["Activité", "Couleur", "ID"])
        self.tree.setColumnHidden(2, True) # Cacher l'ID
        self.tree.setColumnWidth(1, 100) 
        self.tree.header().setDefaultAlignment(Qt.AlignLeft) 
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.Fixed)
        self.tree.setAlternatingRowColors(True)
        self.tree.setIndentation(30)
        
        self.layout.addWidget(self.tree)

        # Actions de bas de page
        self.layout_bottom = QHBoxLayout()
        self.layout_bottom.setContentsMargins(0, 10, 0, 0)
        
        self.btn_delete = QPushButton("Supprimer l'activité sélectionnée")
        self.btn_delete.setObjectName("btn_delete_activites")
        self.btn_delete.setCursor(Qt.PointingHandCursor)
        # self.btn_delete.setMinimumHeight(45) # Removed for text link style

        
        self.layout_bottom.addStretch()
        self.layout_bottom.addWidget(self.btn_delete)
        
        self.layout.addLayout(self.layout_bottom)

    def set_parents_choices(self, items):
        """
        items: list of (id, label)
        """
        self.combo_parents.clear()
        self.combo_parents.addItem("Aucun parent", None)
        for act_id, label in items:
            self.combo_parents.addItem(label, act_id)

    def get_new_activity_data(self):
        name = self.input_name.text().strip()
        parent_id = self.combo_parents.currentData()
        return name, parent_id, None

    def get_selected_activity_id(self):
        item = self.tree.currentItem()
        if item:
            return item.text(2) # ID column is now index 2
        return None

    def clear_form(self):
        self.input_name.clear()
        self.combo_parents.setCurrentIndex(0)

    def set_form_data(self, name, parent_id):
        self.input_name.setText(name)
        
        # Select Parent
        idx_p = self.combo_parents.findData(parent_id)
        if idx_p >= 0:
            self.combo_parents.setCurrentIndex(idx_p)
        else:
            self.combo_parents.setCurrentIndex(0)

    def show_error(self, message):
        self.lbl_message.setText(message)
        # Texte blanc comme demandé
        self.lbl_message.setStyleSheet("color: #F0EDEE; font-weight: bold; background: transparent; font-size: 14px; margin-top: 5px;")
        self.lbl_message.show()

    def show_success(self, message):
        self.lbl_message.setText(message)
        # Texte blanc aussi pour uniformité ou vert ? "et en blanc le texte" -> Je mets tout en blanc.
        self.lbl_message.setStyleSheet("color: #F0EDEE; font-weight: bold; background: transparent; font-size: 14px; margin-top: 5px;")
        self.lbl_message.show()

    def clear_message(self):
        self.lbl_message.clear()
        self.lbl_message.hide()
