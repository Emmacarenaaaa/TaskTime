"""
Sélecteur de couleur personnalisé pour TaskTime.
Design moderne et cohérent avec le thème de l'application.
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from vues.custom_dialog import StyledDialog


class ColorPicker(StyledDialog):
    """Sélecteur de couleur personnalisé avec palette prédéfinie."""
    
    color_selected = Signal(QColor)
    
    # Palette de couleurs modernes et vibrantes
    COLORS = [
        # Ligne 1 - Roses et rouges
        "#FF6699", "#FF0844", "#FA709A", "#FF85B3", "#C71585", "#E91E63",
        # Ligne 2 - Violets et mauves
        "#9F004C", "#667EEA", "#764BA2", "#A855F7", "#8B5CF6", "#7C3AED",
        # Ligne 3 - Bleus
        "#4FACFE", "#00F2FE", "#43E97B", "#38BDF8", "#3B82F6", "#2563EB",
        # Ligne 4 - Verts
        "#10B981", "#34D399", "#6EE7B7", "#14B8A6", "#2DD4BF", "#5EEAD4",
        # Ligne 5 - Jaunes et oranges
        "#FBBF24", "#F59E0B", "#F97316", "#FB923C", "#FDBA74", "#FCD34D",
        # Ligne 6 - Neutres
        "#6B7280", "#9CA3AF", "#D1D5DB", "#E5E7EB", "#F3F4F6", "#FFFFFF",
    ]
    
    def __init__(self, parent=None, current_color=None):
        super().__init__(parent, "Choisir une couleur")
        self.resize(500, 400)
        self.selected_color = current_color if current_color else QColor("#FF6699")
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Configure l'interface du sélecteur."""
        # Titre
        title = QLabel("Sélectionnez une couleur pour l'activité")
        title.setObjectName("lbl_titre_choice")
        title.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(title)
        
        # Grille de couleurs
        grid_widget = QWidget()
        grid_layout = QGridLayout(grid_widget)
        grid_layout.setSpacing(8)
        
        row = 0
        col = 0
        for color_hex in self.COLORS:
            btn = QPushButton()
            btn.setFixedSize(60, 60)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setProperty("color_hex", color_hex)
            
            # Style du bouton de couleur
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color_hex};
                    border: 3px solid #555;
                    border-radius: 8px;
                }}
                QPushButton:hover {{
                    border: 3px solid #FF6699;
                }}
                QPushButton:pressed {{
                    border: 3px solid #FFFFFF;
                }}
            """)
            
            btn.clicked.connect(lambda checked=False, c=color_hex: self._on_color_clicked(c))
            
            grid_layout.addWidget(btn, row, col)
            
            col += 1
            if col >= 6:  # 6 colonnes
                col = 0
                row += 1
        
        self.content_layout.addWidget(grid_widget)
        
        # Aperçu de la couleur sélectionnée
        preview_layout = QHBoxLayout()
        
        preview_label = QLabel("Couleur sélectionnée :")
        preview_label.setObjectName("lbl_field_title")
        preview_layout.addWidget(preview_label)
        
        self.preview_widget = QWidget()
        self.preview_widget.setFixedSize(100, 40)
        self.preview_widget.setStyleSheet(f"""
            background-color: {self.selected_color.name()};
            border: 2px solid #FF6699;
            border-radius: 8px;
        """)
        preview_layout.addWidget(self.preview_widget)
        
        self.lbl_color_code = QLabel(self.selected_color.name().upper())
        self.lbl_color_code.setObjectName("lbl_field_title")
        self.lbl_color_code.setStyleSheet("color: #FF6699; font-weight: bold; font-size: 14px;")
        preview_layout.addWidget(self.lbl_color_code)
        
        preview_layout.addStretch()
        
        self.content_layout.addLayout(preview_layout)
        
        self.content_layout.addStretch()
        
        # Boutons de validation
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        btn_cancel = QPushButton("Annuler")
        btn_cancel.setObjectName("btn_stop")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.setMinimumWidth(120)
        btn_cancel.setMinimumHeight(40)
        btn_cancel.clicked.connect(self.reject)
        buttons_layout.addWidget(btn_cancel)
        
        btn_ok = QPushButton("Valider")
        btn_ok.setObjectName("btn_add_activites")
        btn_ok.setCursor(Qt.PointingHandCursor)
        btn_ok.setMinimumWidth(120)
        btn_ok.setMinimumHeight(40)
        btn_ok.clicked.connect(self.accept)
        buttons_layout.addWidget(btn_ok)
        
        self.content_layout.addLayout(buttons_layout)
    
    def _on_color_clicked(self, color_hex):
        """Gère le clic sur une couleur."""
        self.selected_color = QColor(color_hex)
        
        # Mettre à jour l'aperçu
        self.preview_widget.setStyleSheet(f"""
            background-color: {color_hex};
            border: 2px solid #FF6699;
            border-radius: 8px;
        """)
        
        self.lbl_color_code.setText(color_hex.upper())
    
    def get_color(self):
        """Retourne la couleur sélectionnée."""
        return self.selected_color
    
    @staticmethod
    def get_color_from_user(parent=None, current_color=None):
        """Méthode statique pour obtenir une couleur de l'utilisateur."""
        dialog = ColorPicker(parent, current_color)
        if dialog.exec():
            return dialog.get_color()
        return None
