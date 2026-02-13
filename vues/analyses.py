from datetime import date, datetime, timedelta
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, 
                               QListWidget, QListWidgetItem, QComboBox, QHBoxLayout, QDateEdit, QToolTip, 
                               QStackedWidget, QPushButton, QScrollArea, QSizePolicy)
from PySide6.QtGui import QPainter, QPixmap, QPainterPath, QColor, QPen
from PySide6.QtCore import Qt, QSize, QPoint, QRect, QRectF, Signal, QDate
import os
import math

class AnalysisCard(QFrame):
    """
    Carte simple avec un titre et une zone de contenu.
    """
    def __init__(self, title, card_id):
        super().__init__()
        self.setObjectName("analysis_card")
        self.card_id = card_id
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        # Titre
        self.lbl_title = QLabel(title)
        self.lbl_title.setObjectName("lbl_titre_choice")
        f = self.lbl_title.font()
        f.setBold(True)
        self.lbl_title.setFont(f)
        self.layout.addWidget(self.lbl_title)
        
        # Contenu
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 10, 0, 0)
        self.layout.addWidget(self.content_area)
        
    def set_content_widget(self, widget):
        self.content_layout.addWidget(widget)

class GraphiqueHebdomadaireWidget(QWidget):
    def __init__(self):
        super().__init__()
        # self.donnees_semaine est maintenant {date: {activity: seconds}}
        self.donnees_semaine = {} 
        self.color_map = {}
        self.setMinimumHeight(250)
        
        # Interaction mouse tracking
        self.setMouseTracking(True)
        self.interactive_rects = [] # list of (QRectF, label, duration)
    
    def set_data(self, data):
        self.donnees_semaine = data
        self.update()

    def set_color_map(self, colors):
        self.color_map = colors
        self.update()
        
    def mouseMoveEvent(self, event):
        pos = event.position() if hasattr(event, 'position') else event.pos()
        
        found = False
        for rect, label, duration in self.interactive_rects:
            if rect.contains(pos):
                # Format duration
                h, r = divmod(duration, 3600)
                m, s = divmod(r, 60)
                if h > 0:
                    time_str = f"{int(h)}h {int(m)}m"
                else:
                    time_str = f"{int(m)}m {int(s)}s"
                
                QToolTip.showText(event.globalPos(), f"{label}\n{time_str}", self)
                found = True
                break
        
        if not found:
            QToolTip.hideText()
            
        super().mouseMoveEvent(event)

    def paintEvent(self, event):
        dessinateur = QPainter(self)
        dessinateur.setRenderHint(QPainter.Antialiasing)
        
        # Reset interactive zones
        self.interactive_rects = []
        
        f = self.font()
        # Initialiser avec une taille raisonnable si le défaut est invalide
        if f.pointSize() <= 0: 
            f.setPointSize(9)
        dessinateur.setFont(f)
        
        w = self.width()
        h = self.height()
        m_left, m_right, m_top, m_bot = 60, 30, 20, 30 
        w_graph = w - m_left - m_right
        h_graph = h - m_top - m_bot
        
        # Calcul du maximum
        max_sec = 0
        if self.donnees_semaine:
            for day_data in self.donnees_semaine.values():
                val = sum(day_data.values()) if isinstance(day_data, dict) else day_data
                if val > max_sec: max_sec = val
        
        # Echelle adaptative
        if max_sec >= 3600:
            base_unit = 3600 # Heures
            top_units = math.ceil(max_sec / 3600) + 4
            scale_max = top_units * 3600
            step = 3600
        elif max_sec >= 60:
            base_unit = 60 # Minutes
            top_units = math.ceil(max_sec / 60) + 4
            scale_max = top_units * 60
            step = 60
        else:
            scale_max = 60 # Secondes
            step = 10
            base_unit = 1

        # Ajustement du pas
        display_step = step
        num_ticks = scale_max // step
        while num_ticks > 10:
             display_step *= 2
             num_ticks = scale_max // display_step
        
        # Dessiner les axes
        dessinateur.setPen(Qt.gray)
        dessinateur.drawLine(m_left, m_top, m_left, h - m_bot) # Y
        dessinateur.drawLine(m_left, h - m_bot, w - m_right, h - m_bot) # X
        
        # Grille et étiquettes Y
        grid_pen = QPen(QColor("#e0e0e0"))
        grid_pen.setStyle(Qt.DotLine)
        
        label_font = dessinateur.font()
        label_font.setPointSize(8)
        dessinateur.setFont(label_font)
        
        current_val = 0
        while current_val <= scale_max:
             y_pos = (h - m_bot) - (current_val / scale_max) * h_graph
             
             # Texte de l'étiquette
             if current_val == 0:
                 txt = "0"
             else:
                 if base_unit == 3600:
                     txt = f"{current_val//3600}h"
                 elif base_unit == 60:
                     txt = f"{current_val//60}m"
                 else:
                     txt = f"{current_val}s"
            
             # Dessiner la ligne de la grille
             if current_val > 0:
                 dessinateur.setPen(grid_pen)
                 dessinateur.drawLine(m_left, y_pos, w - m_right, y_pos)
                 
             # Dessiner le tiret et l'étiquette
             dessinateur.setPen(QColor("#F0EDEE"))
             dessinateur.drawLine(m_left - 4, int(y_pos), m_left, int(y_pos))
             
             r_lbl = QRectF(0, y_pos - 10, m_left - 6, 20)
             dessinateur.drawText(r_lbl, Qt.AlignRight | Qt.AlignVCenter, txt)
             
             current_val += display_step
             
        # Dessiner les barres empilées
        dates_sorted = sorted(self.donnees_semaine.keys())
        nb_barres = len(dates_sorted)
        if nb_barres == 0: return
        
        col_width = w_graph / nb_barres
        max_bar_w = 80
        bar_width = min(col_width * 0.6, max_bar_w)
        offset_x = (col_width - bar_width) / 2
        day_font = self.font()
        if day_font.pointSize() <= 0: 
            day_font.setPointSize(8)
        dessinateur.setFont(day_font)
        
        jours_map = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
        default_colors = ["#6200EA", "#d500f9", "#3700B3", "#FF4081", "#7C4DFF", "#03DAC6"]

        for i, date_iso in enumerate(dates_sorted):
            day_activities = self.donnees_semaine[date_iso] # Dict {activity: duration}
            
            # Position X
            x = m_left + (i * col_width) + offset_x
            
            # On commence en bas
            current_y_bottom = h - m_bot
            
            # Trier les segments
            sorted_segments = sorted(day_activities.items(), key=lambda x: x[0])
            
            color_idx = 0
            for act_label, duration in sorted_segments:
                if duration <= 0: continue
                bar_h = (duration / scale_max) * h_graph
                
                # Couleur
                if act_label in self.color_map:
                    col = QColor(self.color_map[act_label])
                else:
                    col = QColor(default_colors[color_idx % len(default_colors)])
                    color_idx += 1
                
                y = current_y_bottom - bar_h
                
                # Rectangle
                rect_bar = QRectF(x, y, bar_width, bar_h)
                
                dessinateur.setBrush(col)
                dessinateur.setPen(Qt.NoPen)
                dessinateur.drawRect(rect_bar)
                
                # Stocker pour interactivité
                self.interactive_rects.append((rect_bar, act_label, duration))
                
                current_y_bottom -= bar_h
            
            # Label date
            nom_jour = date_iso
            
            # Gérer les différents formats
            if date_iso.startswith("2") and "-W" in date_iso:
                # Format semaine : "2026-W05"
                try:
                    year, week = date_iso.split("-W")
                    # Calculer la date du lundi de cette semaine
                    from datetime import datetime, timedelta
                    jan1 = datetime(int(year), 1, 1)
                    week_start = jan1 + timedelta(weeks=int(week)-1)
                    # Ajuster au lundi
                    week_start = week_start - timedelta(days=week_start.weekday())
                    nom_jour = week_start.strftime("%d/%m")
                except:
                    nom_jour = f"S{week}"
            elif date_iso.count("-") == 1 and len(date_iso) == 7:
                # Format mois : "2026-01"
                try:
                    mois_map = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", 
                               "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]
                    year, month = date_iso.split("-")
                    nom_jour = mois_map[int(month)-1]
                except:
                    nom_jour = date_iso
            else:
                # Format date normale : "2026-02-13"
                try:
                    dt_obj = date.fromisoformat(date_iso)
                    if nb_barres > 7:
                        nom_jour = dt_obj.strftime("%d/%m")
                    else:
                        nom_jour = jours_map[dt_obj.weekday()]
                except:
                    nom_jour = date_iso
            
            dessinateur.setPen(QColor("#F0EDEE"))
            r_txt = QRectF(m_left + (i * col_width), h - 20, col_width, 20)
            dessinateur.drawText(r_txt, Qt.AlignCenter, nom_jour)

class PieChartWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.pie_data = [] 
        self.colors = ["#6200EA", "#d500f9", "#3700B3", "#FF4081", "#7C4DFF", "#03DAC6"]
        self.color_map = {}
        self.setMinimumHeight(250)
        
        # Interaction
        self.setMouseTracking(True)
        self.interactive_slices = [] # list of (start_angle_deg, span_angle_deg, label, val)
        self.pie_geometry = None # (center_QPoint, radius)

    def set_data(self, data):
        self.pie_data = data
        self.update()

    def set_color_map(self, map_colors):
        self.color_map = map_colors
        self.update()
        
    def mouseMoveEvent(self, event):
        if not self.pie_geometry or not self.interactive_slices:
            super().mouseMoveEvent(event)
            return

        pos = event.position() if hasattr(event, 'position') else event.pos()
        center, radius = self.pie_geometry
        
        dx = pos.x() - center.x()
        dy = pos.y() - center.y()
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist <= radius:
            # Calcul de l'angle en degrés [0, 360) (0 = 3h, sens anti-horaire visuel inversé par l'axe Y)
            angle_rad = math.atan2(-dy, dx)
            angle_deg = math.degrees(angle_rad)
            
            if angle_deg < 0:
                angle_deg += 360
            
            found = False
            for start, span, label, val in self.interactive_slices:
                diff = (angle_deg - start) % 360
                if diff <= span:
                    # Trouvé !
                    total_val = sum(x[1] for x in self.pie_data)
                    pct = (val / total_val) * 100 if total_val > 0 else 0
                    QToolTip.showText(event.globalPos(), f"{label}\n{pct:.1f}%", self)
                    found = True
                    break
            
            if not found:
                QToolTip.hideText()
        else:
             QToolTip.hideText()
             
        super().mouseMoveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Reset interaction data
        self.interactive_slices = []
        self.pie_geometry = None
        
        w, h = self.width(), self.height()
        
        total = sum(i[1] for i in self.pie_data)
        
        if total == 0:
             f = self.font()
             f.setPointSize(12)
             painter.setFont(f)
             painter.setPen(Qt.gray)
             painter.drawText(QRect(0, 0, w, h), Qt.AlignCenter, "Aucune donnée sur la période")
             return

        # Marges et Zones
        margin = 10
        is_horizontal = w > 400
        
        if is_horizontal:
            pie_zone_w = w * 0.6
            legend_zone_w = w * 0.4
            diameter = min(pie_zone_w - 2*margin, h - 2*margin)
            pie_rect = QRectF(margin + (pie_zone_w - 2*margin - diameter)/2, 
                              margin + (h - 2*margin - diameter)/2, 
                              diameter, diameter)
            legend_x_start = pie_zone_w + margin
            legend_y_start = margin + 20
        else:
            legend_h_estime = len(self.pie_data) * 25 + 20
            pie_available_h = h - legend_h_estime - 2*margin
            if pie_available_h < 100: pie_available_h = 100 
            diameter = min(w - 2*margin, pie_available_h)
            pie_rect = QRectF((w - diameter)/2, margin, diameter, diameter)
            legend_x_start = margin
            legend_y_start = margin + diameter + 20
            legend_zone_w = w - 2*margin

        # Sauver géométrie pour mouseMove
        center = pie_rect.center()
        radius = diameter / 2
        self.pie_geometry = (center, radius)

        # --- DESSIN PIE ---
        cx, cy = center.x(), center.y()
        
        start_angle = 0.0
        
        # Police pour le texte dans le pie
        f_slice = self.font()
        font_size = max(10, int(diameter / 20)) 
        f_slice.setPointSize(font_size)
        f_slice.setBold(True)
        painter.setFont(f_slice)
        
        for i, (lbl, val) in enumerate(self.pie_data):
            if val == 0: continue
            
            # Qt utilise des 1/16èmes de degré
            span_angle_deg = (val / total) * 360
            span_angle_qt = int(span_angle_deg * 16)
            start_angle_qt = int(start_angle * 16)
            
            col_hex = self.color_map.get(lbl, self.colors[i % len(self.colors)])
            painter.setBrush(QColor(col_hex))
            painter.setPen(QPen(Qt.white, 2))
            
            painter.drawPie(pie_rect, start_angle_qt, span_angle_qt)
            
            # Stockage des infos pour l'interaction
            self.interactive_slices.append((start_angle, span_angle_deg, lbl, val))
            
            # Affichage du pourcentage si assez d'espace
            pct = (val/total)*100
            if pct > 4: 
                # Angle milieu en radians
                mid_angle_deg = start_angle + span_angle_deg/2
                mid_angle_rad = math.radians(mid_angle_deg)
                
                r_txt = radius * 0.7
                
                # Projection coordonnées écran
                tx = cx + r_txt * math.cos(mid_angle_rad)
                ty = cy - r_txt * math.sin(mid_angle_rad)
                
                txt = f"{pct:.0f}%"
                fm = painter.fontMetrics()
                tw = fm.horizontalAdvance(txt)
                th = fm.height()
                
                painter.setPen(Qt.white)
                painter.drawText(tx - tw/2, ty + th/4, txt)
            
            start_angle += span_angle_deg

        # --- DESSIN LÉGENDE ---
        f_leg = self.font()
        f_leg.setPointSize(11) 
        painter.setFont(f_leg)
        
        item_height = 28
        curr_y = legend_y_start
        
        for i, (lbl, val) in enumerate(self.pie_data):
            if val == 0: continue
            if curr_y + item_height > h and is_horizontal: break
            
            col_hex = self.color_map.get(lbl, self.colors[i % len(self.colors)])
            
            painter.setBrush(QColor(col_hex))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(QRectF(legend_x_start, curr_y + 4, 16, 16), 4, 4)
            
            pct = (val/total)*100
            hours, rem = divmod(val, 3600)
            minutes, _ = divmod(rem, 60)
            t_str = f"{int(hours)}h{int(minutes):02d}" if hours > 0 else f"{int(minutes)}m"
            
            text_line = f"{lbl} ({pct:.1f}%) - {t_str}"
            
            painter.setPen(QColor("#F0EDEE"))
            painter.drawText(QRectF(legend_x_start + 25, curr_y, legend_zone_w - 25, item_height), 
                             Qt.AlignLeft | Qt.AlignVCenter, text_line)
            
            curr_y += item_height

class CarteGraphiqueHebdo(AnalysisCard):
    def __init__(self):
        super().__init__("Évolution du Temps", "weekly_chart")
        self.graphique = GraphiqueHebdomadaireWidget()
        self.set_content_widget(self.graphique)

    def update_color_map(self, colors):
        self.graphique.set_color_map(colors)

    def update_data(self, lignes_bdd):
        donnees = {}
        
        if lignes_bdd:
            for time_lbl, label, sec in lignes_bdd:
                # time_lbl est soit "YYYY-MM-DD" (jour) soit "YYYY-MM" (mois) ou "HH" (heure)
                # On utilise time_lbl comme clé principale
                if time_lbl not in donnees: donnees[time_lbl] = {}
                if label not in donnees[time_lbl]: donnees[time_lbl][label] = 0
                donnees[time_lbl][label] += sec
        
        self.graphique.set_data(donnees)

class PieChartCard(AnalysisCard):
    def __init__(self):
        super().__init__("Répartition", "pie_chart")
        self.chart = PieChartWidget()
        self.set_content_widget(self.chart)
        
    def update_data(self, db_rows):
        self.chart.set_data(db_rows)

    def update_color_map(self, map_colors):
        self.chart.set_color_map(map_colors)

class ActivityListCard(AnalysisCard):
    def __init__(self):
        super().__init__("Activités", "activity_list")
        self.list_widget = QListWidget()
        self.list_widget.setObjectName("activity_list_widget")
        self.list_widget.setAlternatingRowColors(True)
        self.list_widget.setFocusPolicy(Qt.NoFocus)
        self.set_content_widget(self.list_widget)

    def update_data(self, data):
        self.list_widget.clear()
        if not data:
            self.list_widget.addItem(QListWidgetItem("Aucune activité."))
            return
            
        for row in data:
            raw_date, cat, lbl, dur = row
            d_str = raw_date
            
            h, m = divmod(dur, 3600)
            m, s = divmod(m, 60)
            t_fmt = f"{h:02d}:{m:02d}" if h>0 else f"{m:02d}:{s:02d}"
            
            desc = cat
            if cat == "Autre" and lbl: desc = lbl
            elif lbl and lbl != cat: desc += f" - {lbl}"
            
            self.list_widget.addItem(QListWidgetItem(f"{d_str} - {desc} -> {t_fmt}"))

class ProjectsList(QWidget):
    project_selected = Signal(object) # Emit project_id

    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 20, 0) # Marge droite pour espacer du contenu
        
        lbl = QLabel("Projets")
        lbl.setObjectName("h2_sidebar")
        self.layout.addWidget(lbl)
        
        self.list_widget = QListWidget()
        self.list_widget.setCursor(Qt.PointingHandCursor)
        # Style géré globalement
        self.list_widget.setObjectName("sidebar_projects_list")

        self.list_widget.currentItemChanged.connect(self.on_selection)
        self.layout.addWidget(self.list_widget)
        
        # Largeur fixe pour la sidebar
        self.setFixedWidth(250)

    def set_projects(self, projects):
        """projects: list of (id, label)"""
        self.list_widget.clear()
        
        # Item "Tous les projets"
        item_all = QListWidgetItem("Vue d'ensemble")
        item_all.setData(Qt.UserRole, "all")
        self.list_widget.addItem(item_all)
        
        for pid, label in projects:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, pid)
            self.list_widget.addItem(item)
            
        self.list_widget.setCurrentRow(0)

    def on_selection(self, current, previous):
        if current:
            pid = current.data(Qt.UserRole)
            self.project_selected.emit(pid)

class AnalysesView(QWidget):
    global_filter_changed = Signal(str, object)
    project_selected = Signal(object)
    export_requested = Signal()
    
    def __init__(self):
        super().__init__()
        
        # Layout principal horizontal : [Liste Projets] | [Contenu Analyses]
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(0)
        
        # --- Colonne Gauche : Liste des Projets ---
        self.sidebar_projects = ProjectsList()
        self.sidebar_projects.project_selected.connect(self.project_selected.emit)
        self.main_layout.addWidget(self.sidebar_projects)
        
        # --- Colonne Droite : Dashboard Analyses ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        # Style optionnel pour la scrollbar si besoin, mais le natif est souvent ok
        
        self.content_area = QWidget()
        self.content_area.setObjectName("analysis_content_area") # Critical ID for QSS
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(20)
        
        self.scroll_area.setWidget(self.content_area)
        
        # 1. Barre de Filtres Globale
        self.filter_bar = QFrame()
        self.filter_bar.setObjectName("card") # Style card
        self.filter_bar.setFixedHeight(70)
        layout_filter = QHBoxLayout(self.filter_bar)
        layout_filter.setContentsMargins(20, 10, 20, 10)
        layout_filter.setSpacing(15)
        
        lbl_f = QLabel("Période :")
        lbl_f.setObjectName("lbl_filter")
        layout_filter.addWidget(lbl_f)
        
        self.combo_mode = QComboBox()
        self.combo_mode.setObjectName("modern_combo")
        self.combo_mode.addItems(["Période", "Aujourd'hui", "Une semaine", "Un mois", "Cette année", "Global"])
        self.combo_mode.setCurrentText("Période")
        self.combo_mode.currentTextChanged.connect(self.on_filter_change)
        layout_filter.addWidget(self.combo_mode)
        
        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDate(QDate.currentDate().addDays(-7))
        self.date_start.setDisplayFormat("dd/MM/yyyy")
        self.date_start.setFixedWidth(140)
        self.date_start.dateChanged.connect(self.on_date_changed)
        layout_filter.addWidget(self.date_start)
        
        self.lbl_sep = QLabel("au")
        layout_filter.addWidget(self.lbl_sep)
        
        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDate(QDate.currentDate())
        self.date_end.setDisplayFormat("dd/MM/yyyy")
        self.date_end.setFixedWidth(140)
        self.date_end.dateChanged.connect(self.on_date_changed)
        layout_filter.addWidget(self.date_end)
        
        layout_filter.addWidget(self.date_end)
        
        layout_filter.addStretch()
        
        # Bouton Export CSV
        self.btn_export = QPushButton("Export CSV")
        self.btn_export.setObjectName("btn_export_csv")
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.clicked.connect(self.export_requested.emit)
        layout_filter.addWidget(self.btn_export)
        
        self.content_layout.addWidget(self.filter_bar)
        
        # 2. Graphiques
        self.card_week = CarteGraphiqueHebdo() 
        self.card_pie = PieChartCard()
        self.card_list = ActivityListCard() 
        
        self.content_layout.addWidget(self.card_week, 1)
        
        self.content_layout.addWidget(self.card_pie, 1)
        
        self.main_layout.addWidget(self.scroll_area)
        
        # Init visibility
        self.on_filter_change("Période")

    def on_filter_change(self, text):
        is_period = (text == "Période")
        self.date_start.setVisible(is_period)
        self.date_end.setVisible(is_period)
        self.lbl_sep.setVisible(is_period)
        self.emit_filter()

    def on_date_changed(self, _):
        self.emit_filter()

    def emit_filter(self):
        mode = self.combo_mode.currentText()
        dates = None
        if mode == "Période":
            dates = (self.date_start.date().toPython(), self.date_end.date().toPython())
        self.global_filter_changed.emit(mode, dates)

    def set_projects_list(self, projects):
        self.sidebar_projects.set_projects(projects)

    def update_history(self, today_data, week_data, pie_data, color_map=None):
        self.card_list.update_data(today_data)
        self.card_week.update_data(week_data)
        
        if color_map:
            self.card_pie.update_color_map(color_map)
            self.card_week.update_color_map(color_map)
            
        self.card_pie.update_data(pie_data)
