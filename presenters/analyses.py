"""
Présentateur des analyses et statistiques.
Gère la logique métier des graphiques, filtres et exports de données.
"""

from datetime import date, timedelta

class AnalysesPresenter:
    """
    Présentateur pour la vue d'analyse.
    Gère les filtres, les graphiques et l'export CSV des données.
    """
    def __init__(self, view, model):
        self.view = view
        self.model = model
        
        self.current_project_id = "all"
        self.current_color_map = {}
        
        # Filtres courants (valeurs par défaut)
        today = date.today()
        start = today - timedelta(days=7)
        self.current_mode = "Période"
        self.current_dates = (start, today)
        
        # Connecter les signaux de la vue

        self.view.global_filter_changed.connect(self.on_global_filter_changed)
        self.view.project_selected.connect(self.on_project_selected)
        self.view.export_requested.connect(self.on_export_csv)
        
        # Chargement initial
        self.refresh()
        
    def on_export_csv(self):
        from PySide6.QtWidgets import QFileDialog
        import csv
        import os
        
        # Get data based on current filters
        rows = self.model.get_export_data(self.current_mode, self.current_dates, self.current_project_id)
        
        # Prompt for save location
        filename, _ = QFileDialog.getSaveFileName(self.view, "Exporter en CSV", 
                                                  f"export_activites_{date.today()}.csv",
                                                  "Fichiers CSV (*.csv)")
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile, delimiter=';') # Excel friendly in FR
                    writer.writerow(['Date', 'HeureDébut', 'HeureFin', 'Projet', 'Activité', 'Durée (s)', 'Durée (h:m:s)'])
                    
                    for r in rows:
                        # r = (id, date_debut, date_fin, projet_nom, activite_nom, duree_sec)
                        # Adaptez selon ce que get_export_data renvoie
                        # Supposons que le helper renvoie les champs bruts
                        d_debut = r[1]
                        d_fin = r[2]
                        proj = r[3] if r[3] else "Aucun"
                        act = r[4]
                        dur = r[5]
                        
                        # Formatage durée
                        m, s = divmod(dur, 60)
                        h, m = divmod(m, 60)
                        dur_fmt = f"{h:02d}:{m:02d}:{s:02d}"
                        
                        # Split date/time if date fields are datetime objects or strings
                        # Assuming strings YYYY-MM-DD HH:MM:SS for simplicity from SQLite
                        try:
                            date_str = d_debut.split(' ')[0]
                            time_start = d_debut.split(' ')[1]
                            time_end = d_fin.split(' ')[1] if d_fin else ""
                        except:
                            date_str = str(d_debut)
                            time_start = ""
                            time_end = ""

                        writer.writerow([date_str, time_start, time_end, proj, act, dur, dur_fmt])
                        
                from vues.custom_dialog import CustomMessageBox
                CustomMessageBox.information(self.view, "Export réussi", f"Données exportées vers :\n{filename}")
            except Exception as e:
                from vues.custom_dialog import CustomMessageBox
                CustomMessageBox.critical(self.view, "Erreur", f"Échec de l'export :\n{str(e)}")
        
    def refresh(self):
        # Charge les données de référence et raffraichit les graphes
        self.load_reference_data()
        self._refresh_charts()

    def load_reference_data(self):
        # 1. Récupérer la liste des projets
        projects = self.model.get_projects() # list of (id, nom, desc, date)
        # On extrait juste (id, nom) pour la vue
        project_choices = [(p[0], p[1]) for p in projects]
        self.view.set_projects_list(project_choices)
        
        # 2. Récupérer activités 
        activities = self.model.get_activities() 
        
        # 3. Préparer la map des couleurs
        all_colors = self.model.get_all_colors() 
        
        color_db_map = {c[0]: c[2] for c in all_colors} 
        act_map = {}
        for a in activities:
            act_map[a[0]] = {'lib': a[1], 'pid': a[2], 'cid': a[3]}
            
        name_to_color_map = {}
        DEFAULT_COLORS = ["#4facfe", "#43e97b", "#fa709a", "#667eea", "#ff0844", "#fccb90"]
        
        def get_color(aid):
            if aid not in act_map: return "#cccccc"
            data = act_map[aid]
            cid, pid = data['cid'], data['pid']
            if cid and cid in color_db_map: return color_db_map[cid]
            if pid and pid in act_map:
                p_cid = act_map[pid]['cid']
                if p_cid and p_cid in color_db_map: return color_db_map[p_cid]
                return DEFAULT_COLORS[pid % len(DEFAULT_COLORS)]
            return DEFAULT_COLORS[aid % len(DEFAULT_COLORS)]

        for aid, data in act_map.items():
            name_to_color_map[data['lib']] = get_color(aid)
            
        # Stocker la color map dans self pour la réutiliser
        self.current_color_map = name_to_color_map

    def _refresh_charts(self):
        """Met à jour tous les graphiques avec le projet courant et dates globales"""
        pid = self.current_project_id
        mode = self.current_mode
        dates = self.current_dates
        
        # Historique
        history_data = self.model.get_filtered_history(mode, dates, project_id=pid)
        
        # Graphique Hebdo (ou mensuel selon période)
        progression_data = self.model.get_filtered_progression(mode, dates, project_id=pid)
        
        # Pie Chart
        # Le Pie chart est souvent "Global" mais ici on lui applique le filtre global s'il est cohérent
        # ou alors on garde la logique "Répartition sur la période sélectionnée"
        pie_data = self.model.get_filtered_distribution(mode, dates, project_id=pid)
        
        self.view.update_history(history_data, progression_data, pie_data, self.current_color_map)

    def on_project_selected(self, project_id):
        self.current_project_id = project_id
        # On garde les dates actuelles
        self._refresh_charts()

    def on_global_filter_changed(self, mode, dates):
        """Gère le changement de filtre global et calcule les dates selon le mode."""
        self.current_mode = mode
        
        # Calculer les dates selon le mode
        if mode == "Aujourd'hui":
            today = date.today()
            self.current_dates = (today, today)
        elif mode == "Une semaine":
            today = date.today()
            week_ago = today - timedelta(days=7)
            self.current_dates = (week_ago, today)
        elif mode == "Un mois":
            today = date.today()
            month_ago = today - timedelta(days=30)
            self.current_dates = (month_ago, today)
        elif mode == "Cette année":
            today = date.today()
            year_start = date(today.year, 1, 1)
            self.current_dates = (year_start, today)
        elif mode == "Période":
            # Utiliser les dates fournies par la vue
            self.current_dates = dates
        else:  # Global
            self.current_dates = None
        
        self._refresh_charts()
