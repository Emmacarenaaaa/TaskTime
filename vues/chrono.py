"""
Vue du chronomètre avec affichage en bulles.
Permet de sélectionner et chronométrer des activités de manière visuelle.
"""

from PySide6.QtWidgets import (QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, 
                                 QListWidget, QLineEdit, QFrame, QSizePolicy, QGraphicsDropShadowEffect, QDialog)
from PySide6.QtCore import Qt, QPoint, Signal, QTimer, QPropertyAnimation, QEasingCurve, QSize
from PySide6.QtGui import QIcon, QKeySequence
import math
import os

class BubbleLayoutManager:
    """
    Gestionnaire de disposition des bulles d'activités.
    Calcule et applique le positionnement des bulles parents et enfants.
    """
    @staticmethod
    def apply_layout(bubbles, center_widget, container_rect, focus_item=None):
        if container_rect.width() < 50: return
        cx, cy = container_rect.center().x(), container_rect.center().y()
        
        # -- 1. Calcul de l'espace disponible --
        min_dim = min(container_rect.width(), container_rect.height())
        
        # Marge de sécurité : Rayon Parent (50) + Rayon Enfant (20) + Orbit (15) + Marge (20) ≈ 105-115px
        # Cela évite que les enfants (fleurs) ne sortent du cadre
        safe_margin = 115 
        available_radius = (min_dim / 2) - safe_margin
        
        # Centrer l'horloge
        cw_w, cw_h = center_widget.width(), center_widget.height()
        center_widget.move(int(cx - cw_w/2), int(cy - cw_h/2))
        if not focus_item: center_widget.raise_()
 
        TOTAL_SLOTS = 8
        angle_step = 2 * math.pi / TOTAL_SLOTS

        # -- 2. Rayon du cercle principal --
        # On définit le rayon pour rester DANS la safe_margin
        # min 90 pour ne pas écraser l'horloge, max 280 pour l'esthétique
        dist_parent = min(280, max(90, available_radius))
        
        # -- 3. Calcul de la taille (Anti-Chevauchement) --
        # Corde disponible entre 2 bulles sur le cercle : C = 2 * R * sin(pi/N)
        # On veut size < C (avec une petite marge)
        chord = 2 * dist_parent * math.sin(math.pi / TOTAL_SLOTS)
        max_size_allowed = chord * 0.9 # 10% de marge entre bulles
        
        # Taille standard voulue : 100px
        # On réduit si nécessaire, mais pas en dessous de 50px
        base_size = int(min(100, max(50, max_size_allowed)))
        
        # Facteur d'échelle global déduit
        scale_factor = base_size / 100.0
        
        # Tailles dérivées
        size_parent = base_size
        size_parent_focus = int(140 * scale_factor) # ou fixe 140 si on a de la place au centre? Gardons l'échelle.
        size_child = int(40 * scale_factor)
        size_child_focus = int(90 * scale_factor)

        # Helper pour garantir Style Rond + Taille
        def apply_circle_style(btn, size, color):
            # Utilisation de border-radius: 50% pour un cercle parfait
            style = f"""
                QPushButton {{
                    background-color: {color};
                    border-radius: {size//2}px; /* Fallback si 50% bug */
                    color: white; font-weight: bold;
                    border: 2px solid transparent; /* Evite saut visuel au hover */
                }}
                QPushButton:hover {{ border: 2px solid white; }}
            """
            btn.setFixedSize(size, size)
            btn.setStyleSheet(style)

        for i, item in enumerate(bubbles):
            item['btn'].show()
            children = item['children']
            is_focused = (item == focus_item)
            
            p_btn = item['btn']
            # Récupération couleur
            p_color = item.get('color', '#333') 

            if is_focused:
                # --- Parent FOCUS : Au Centre ---
                # Au centre, on a de la place, on peut être un peu plus gros
                # Mais gardons la cohérence de scale
                apply_circle_style(p_btn, size_parent_focus, p_color)
                p_btn.move(int(cx - p_btn.width()/2), int(cy - p_btn.height()/2))
                
                # Enfants orbite
                radius_orbit = min(220, max(140, available_radius * 1.5)) # Un peu plus large si possible
                c_step = 2 * math.pi / max(1, len(children))
                
                for k, child_item in enumerate(children):
                     c_btn = child_item['btn'] if isinstance(child_item, dict) else child_item
                     c_color = item['children_colors'][k] if 'children_colors' in item and k < len(item['children_colors']) else '#555'

                     c_btn.show()
                     apply_circle_style(c_btn, size_child_focus, c_color)
                     
                     c_angle = c_step * k - (math.pi / 2)
                     c_px = cx + math.cos(c_angle) * radius_orbit
                     c_py = cy + math.sin(c_angle) * radius_orbit
                     c_btn.move(int(c_px - c_btn.width()/2), int(c_py - c_btn.height()/2))
                     c_btn.raise_() 

            else:
                # --- Parent NON-FOCUS ---
                apply_circle_style(p_btn, size_parent, p_color)

                if i < TOTAL_SLOTS:
                    angle = angle_step * i - (math.pi / 2)
                    px = cx + math.cos(angle) * dist_parent
                    py = cy + math.sin(angle) * dist_parent
                    
                    p_btn.move(int(px - p_btn.width()/2), int(py - p_btn.height()/2))
                    
                    # Enfants Fleur serrée
                    p_radius = p_btn.width() / 2
                    
                    for j, child_item in enumerate(children):
                        if j >= TOTAL_SLOTS: break
                        c_btn = child_item['btn'] if isinstance(child_item, dict) else child_item
                        c_color = item['children_colors'][j] if 'children_colors' in item and j < len(item['children_colors']) else '#555'
                        
                        c_btn.show()
                        apply_circle_style(c_btn, size_child, c_color)
                        
                        c_radius = c_btn.width() / 2
                        orbit_radius = p_radius + c_radius + (15 * scale_factor)
                        c_angle = angle_step * j - (math.pi / 2)
                        c_px = px + math.cos(c_angle) * orbit_radius
                        c_py = py + math.sin(c_angle) * orbit_radius
                        c_btn.move(int(c_px - c_btn.width()/2), int(c_py - c_btn.height()/2))
                else:
                     item['btn'].hide()
                     for c in children:
                         c_btn = c['btn'] if isinstance(c, dict) else c
                         c_btn.hide()

from vues.custom_dialog import StyledDialog

class SelectionDialog(StyledDialog):
    """
    Dialogue de sélection d'activités pour le Chrono.
    Hérite du style global.
    """
    def __init__(self, parent=None, title="Sélection"):
        super().__init__(parent, title)
        # Le layout principal est déjà self.content_layout
        # On peut ajouter des styles spécifiques ici si nécessaire


class NewChronoView(QWidget):
    escape_pressed = Signal()
    space_pressed = Signal()
    
    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.StrongFocus) 
        
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # --- Sidebar ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("project_sidebar")
        self.sidebar.setFixedWidth(250)
        
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header (Titre + Toggle)
        header_layout = QHBoxLayout()
        
        # Sidebar à Droite : Toggle (Gauche/Intérieur) - Titre (Droite)
        
        self.btn_toggle_panel = QPushButton()
        self.btn_toggle_panel.setObjectName("btn_toggle_sidebar")
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "icons", "menu.svg")
        if os.path.exists(icon_path):
             self.btn_toggle_panel.setIcon(QIcon(icon_path))
             self.btn_toggle_panel.setIconSize(QSize(20, 20))
        else:
             self.btn_toggle_panel.setText("☰")
             
        self.btn_toggle_panel.setFixedSize(30, 30)
        self.btn_toggle_panel.setCursor(Qt.PointingHandCursor)
        self.btn_toggle_panel.clicked.connect(self.toggle_panel)
        header_layout.addWidget(self.btn_toggle_panel, 0, Qt.AlignLeft)

        self.lbl_proj = QLabel("Projets")
        self.lbl_proj.setObjectName("lbl_proj")
        self.lbl_proj.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header_layout.addWidget(self.lbl_proj)
        
        self.sidebar_layout.addLayout(header_layout)
        
        # Content Wrapper
        self.panel_content = QWidget()
        content_layout = QVBoxLayout(self.panel_content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        # Bouton Choix des activités (Placé en haut pour être bien visible)
        self.btn_manage_display = QPushButton("Choix des activités")
        self.btn_manage_display.setObjectName("btn_manage_display")
        self.btn_manage_display.setToolTip("Sélectionner les bulles parents à afficher")
        content_layout.addWidget(self.btn_manage_display)
        
        # Séparateur visuel (optionnel, ou juste de l'espace)
        content_layout.addSpacing(10)

        self.list_projects = QListWidget()
        self.list_projects.setObjectName("list_projects")
        content_layout.addWidget(self.list_projects)
        
        self.input_project = QLineEdit()
        self.input_project.setObjectName("input_project")
        self.input_project.setPlaceholderText("Nouveau projet...")
        content_layout.addWidget(self.input_project)
        
        self.btn_add_project = QPushButton("Créer")
        self.btn_add_project.setObjectName("btn_add_project")
        content_layout.addWidget(self.btn_add_project)
        
        self.btn_delete_project = QPushButton("Supprimer le projet sélectionné")
        self.btn_delete_project.setObjectName("btn_delete_project")
        self.btn_delete_project.setToolTip("Supprimer le projet sélectionné dans la liste")
        content_layout.addWidget(self.btn_delete_project)
        
        content_layout.addStretch()
        
        self.sidebar_layout.addWidget(self.panel_content)
        
        # --- Container des Bulles ---
        self.bubble_container = QWidget()
        self.bubble_container.setObjectName("bubble_container")
        self.main_layout.addWidget(self.bubble_container)

        # Style géré via QSS (ID: #project_sidebar)

        self.main_layout.addWidget(self.sidebar)

        self.bubbles = []
        self.current_focus_ptr = None # Pour stocker le parent focus actuel

        # --- Dimmer pour le mode Focus ---
        self.dimmer = QWidget(self.bubble_container)
        self.dimmer.setStyleSheet("background-color: rgba(0, 0, 0, 200);") # Tres sombre (200/255)
        self.dimmer.hide()
        self.dimmer.resize(2000, 2000) # Assez grand (sera resize dans resizeEvent)
        
        # --- Cœur du Chrono ---
        self.center_widget = QWidget(self.bubble_container)
        self.center_widget.setObjectName("chrono_center_bubble")
        self.center_widget.setFixedSize(140, 140)
        # Style géré dans le QSS maintenant
        
        self.lbl_time = QLabel("00:00:00", self.center_widget)
        self.lbl_time.setAlignment(Qt.AlignCenter)
        self.lbl_time.setLayoutDirection(Qt.LeftToRight) # Just in case default alignment issues
        self.lbl_time.setGeometry(0, 70, 140, 30)
        self.lbl_time.setObjectName("lbl_time_bubble")

        self.lbl_activity_name = QLabel("", self.center_widget)
        self.lbl_activity_name.setAlignment(Qt.AlignCenter)
        self.lbl_activity_name.setObjectName("lbl_activity_bubble")
        self.lbl_activity_name.setGeometry(10, 30, 120, 40)
        self.lbl_activity_name.setWordWrap(True)

        # Bouton Stop
        self.btn_stop = QPushButton("Stop", self.center_widget)
        self.btn_stop.setObjectName("btn_stop_center")
        self.btn_stop.hide() 

        # Lancer le repositionnement après un court délai pour laisser le layout s'installer
        QTimer.singleShot(50, self.reposition_bubbles)

    def set_activities(self, activities_data, on_click_callback):
        # 1. Sauvegarder focus
        old_focus_id = self.current_focus_ptr['id'] if self.current_focus_ptr else None
        self.current_focus_ptr = None
        if hasattr(self, 'dimmer'): self.dimmer.hide()
        
        for item in self.bubbles:
            item['btn'].deleteLater()
            for child_btn in item['children']:
                child_btn.deleteLater()
        self.bubbles = []

        for parent_data in activities_data:
            p_id, p_label = parent_data['id'], parent_data['label']
            p_color = parent_data.get('color', '#cccccc')
            
            p_btn = self.create_bubble_btn(p_label, 100, f"background-color: {p_color}; border-radius: 50px;") 
            p_btn.show()
            
            p_btn.clicked.connect(lambda checked=False, aid=p_id, lbl=p_label: on_click_callback(aid, lbl, True))
            
            children_btns = []
            for child_data in parent_data['children']:
                c_btn = self.create_bubble_btn(child_data['label'], 40, f"background-color: {child_data.get('color', p_color)}; border-radius: 20px;")
                c_btn.show()
                # On cache le texte des petites bulles par défaut
                lbl = c_btn.findChild(QLabel)
                if lbl: lbl.hide()
                
                c_btn.clicked.connect(lambda checked=False, aid=child_data['id'], lbl=child_data['label']: on_click_callback(aid, lbl, False))
                children_btns.append(c_btn)
            
            self.bubbles.append({
                'id': p_id, 'btn': p_btn, 'children': children_btns,
                'expanded': False, 'color': p_color,
                'children_colors': [c.get('color', p_color) for c in parent_data['children']]
            })

        # Relance du layout / Restauration du focus
        def restore():
            if old_focus_id:
                # Tenter de retrouver le parent
                found = False
                for item in self.bubbles:
                    if item['id'] == old_focus_id:
                        self.set_focus_parent(old_focus_id)
                        found = True
                        break
                if not found:
                    self.reposition_bubbles()
            else:
                self.reposition_bubbles()
                
        QTimer.singleShot(10, restore)

    def create_bubble_btn(self, text, size, style):
        btn = QPushButton(self.bubble_container) 
        btn.setFixedSize(size, size)
        btn.setStyleSheet(style)
        layout = QVBoxLayout(btn)
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setStyleSheet("color: white; font-weight: bold; border: none; background: transparent;")
        lbl.setAttribute(Qt.WA_TransparentForMouseEvents)
        layout.addWidget(lbl)
        return btn

    def reposition_bubbles(self, force=True):
        BubbleLayoutManager.apply_layout(self.bubbles, self.center_widget, self.bubble_container.rect(), self.current_focus_ptr)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.dimmer.resize(self.bubble_container.size()) # Adapter le dimmer
        
        # Auto-collapse sidebar si très petit (Note: c'est un sous-composant, donc on vérifie sa propre largeur)
        # Si la largeur totale est < 600, on réduit le panneau
        if event.size().width() < 600:
             if self.sidebar.width() > 100:
                 self.set_panel_collapsed(True)
                 
        self.reposition_bubbles()

    def set_shortcuts_config(self, config_dict):
        """Reçoit {ACTION_CODE: STR_SEQUENCE}"""
        self.shortcuts_map = {}
        for code, seq_str in config_dict.items():
            self.shortcuts_map[code] = QKeySequence(seq_str)

    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        
        # On construit une sequence à partir de l'event pour comparer
        # Utilisation du cast en int pour compatibilité PySide6 robuste sans QKeyCombination explicite
        # .value requis pour les ENUMS PySide6, mais safe check si int
        m_val = modifiers.value if hasattr(modifiers, 'value') else int(modifiers)
        k_val = key.value if hasattr(key, 'value') else int(key)
        
        val = m_val | k_val
        event_seq = QKeySequence(val)
        
        # On compare avec notre map
        # Note: matches() de QKeySequence est parfois tricky avec les modifiers.
        # Une comparaison simple d'égalité sur les objets QKeySequence ou sur toString() fonctionne souvent mieux pour des raccourcis simples.
        
        matched_action = None
        
        if hasattr(self, 'shortcuts_map'):
            for code, seq in self.shortcuts_map.items():
                if seq.matches(event_seq) == QKeySequence.ExactMatch:
                    matched_action = code
                    break
        
        if matched_action:
            if matched_action == "PAUSE_RESUME":
                self.space_pressed.emit()
            elif matched_action == "STOP_TIMER":
                self.escape_pressed.emit()
            elif matched_action.startswith("BUBBLE_"):
                try:
                    idx = int(matched_action.split("_")[1])
                    self.trigger_bubble_at_index(idx)
                except:
                    pass
            event.accept()
            return
            
        # Fallback pour touches standards si pas de match (pour éviter de bloquer l'input normal si besoin)
        # Mais ici c'est une vue principale, donc on pass
        super().keyPressEvent(event)

    def trigger_bubble_at_index(self, index):
        if self.current_focus_ptr:
            # Mode Focus : Sélection d'un enfant
            children = self.current_focus_ptr['children']
            if 0 <= index < len(children):
                children[index].animateClick() # animateClick donne un feedback visuel
        else:
            # Mode Racine : Sélection d'un parent
            # On ne prend que ceux qui sont affichés (les 10 premiers max)
            visible_bubbles = self.bubbles[:10]
            if 0 <= index < len(visible_bubbles):
                visible_bubbles[index]['btn'].animateClick()

    def update_time(self, text):
        self.lbl_time.setText(text)

    def set_activity_name(self, text):
        self.lbl_activity_name.setText(text) 

    def add_shadow(self, widget):
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(15)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(Qt.black) 
        widget.setGraphicsEffect(shadow)

    def get_parent_style(self, active, color):
        size = 130 if active else 100
        radius = size // 2
        return f"""
            QPushButton {{
                background-color: {color};
                border-radius: {radius}px;
                color: white; font-weight: bold;
            }}
            QPushButton:hover {{ border: 2px solid white; }}
        """

    def get_child_style(self, active, color):
        size = 90 if active else 40 # 90 pour le mode focus
        radius = size // 2
        return f"""
            QPushButton {{
                background-color: {color};
                border-radius: {radius}px;
                color: white; font-weight: bold;
            }}
            QPushButton:hover {{ border: 2px solid white; }}
        """

    def set_focus_parent(self, parent_id):
        # Gestion de l'état "Focus"
        focus_item = None
        
        for item in self.bubbles:
            is_target = (item['id'] == parent_id)
            item['expanded'] = is_target 
            
            p_btn = item['btn']
            color = item['color']
            children = item['children']
            c_colors = item['children_colors']
            
            if is_target:
                focus_item = item
                
                p_btn.setFixedSize(140, 140) 
                p_btn.setStyleSheet(self.get_parent_style(True, color))
                
                
                for i, c_btn in enumerate(children):
                    c_btn.setFixedSize(90, 90) # Devenues grosses
                    c_btn.setStyleSheet(self.get_child_style(True, c_colors[i]))
                    # Afficher texte
                    lbl = c_btn.findChild(QLabel)
                    if lbl: lbl.show()
            else:
                # Style normal
                p_btn.setFixedSize(100, 100)
                p_btn.setStyleSheet(self.get_parent_style(False, color))
                
                for i, c_btn in enumerate(children):
                    c_btn.setFixedSize(40, 40)
                    c_btn.setStyleSheet(self.get_child_style(False, c_colors[i]))
                    # Cacher texte
                    lbl = c_btn.findChild(QLabel)
                    if lbl: lbl.hide()
        
        self.current_focus_ptr = focus_item
        self.dimmer.show() # Activer le fond sombre
        self.dimmer.raise_() # Devant le fond
        
        # Important : Raise le focus au dessus du dimmer
        if focus_item:
            focus_item['btn'].raise_()
            for c in focus_item['children']: c.raise_()
        
        self.reposition_bubbles()

    def reset_focus(self):
        self.current_focus_ptr = None
        self.dimmer.hide()
        
        for item in self.bubbles:
            item['expanded'] = False
            item['btn'].show() # Tout remontrer
            item['btn'].setFixedSize(100, 100)
            item['btn'].setStyleSheet(self.get_parent_style(False, item['color']))
            
            children = item['children']
            c_colors = item['children_colors']
            for i, c_btn in enumerate(children):
                c_btn.show() # Tout remontrer
                c_btn.setFixedSize(40, 40)
                c_btn.setStyleSheet(self.get_child_style(False, c_colors[i]))
                # Cacher texte
                lbl = c_btn.findChild(QLabel)
                if lbl: lbl.hide()
                
        self.reposition_bubbles()

    def toggle_panel(self):
        width = self.sidebar.width()
        is_expanded = (width > 100)
        self.set_panel_collapsed(is_expanded)

    def set_panel_collapsed(self, collapsed):
        current_width = self.sidebar.width()
        currently_collapsed = (current_width < 100)
        
        if collapsed == currently_collapsed:
            return # Rien à faire

        target_width = 60 if collapsed else 250
        
        # Prepare Animation
        self.anim_min = QPropertyAnimation(self.sidebar, b"minimumWidth")
        self.anim_min.setDuration(300)
        self.anim_min.setStartValue(current_width)
        self.anim_min.setEndValue(target_width)
        self.anim_min.setEasingCurve(QEasingCurve.InOutQuart)
        
        self.anim_max = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self.anim_max.setDuration(300)
        self.anim_max.setStartValue(current_width)
        self.anim_max.setEndValue(target_width)
        self.anim_max.setEasingCurve(QEasingCurve.InOutQuart)

        # Logic before animation
        if collapsed:
            self.btn_toggle_panel.setToolTip("Afficher Projets")

        # Logic after animation
        def on_finished():
            if not collapsed: # Expanded
                self.panel_content.show()
                self.lbl_proj.show()
                self.btn_toggle_panel.setToolTip("Masquer")
            else: # Collapsed
                self.panel_content.hide()
                self.lbl_proj.hide()
                
            self.reposition_bubbles()
            self.dimmer.resize(self.bubble_container.size())

        self.anim_max.finished.connect(on_finished)
        self.anim_min.start()
        self.anim_max.start()

        # Si on collapse, on peut cacher le texte tout de suite pour éviter glitch visuel
        if collapsed:
             self.panel_content.hide()
             self.lbl_proj.hide()
