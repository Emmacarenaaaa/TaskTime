"""
Gestionnaire de base de données pour TaskTime.
Gère toutes les opérations CRUD sur la base de données SQLite.
"""

import sqlite3
from datetime import datetime, timedelta
import os

class DatabaseManager:
    """
    Gestionnaire principal de la base de données.
    Fournit des méthodes pour gérer les activités, sessions, projets, couleurs et raccourcis.
    """
    def __init__(self, db_name='tasktime.db'):
        self.conn = sqlite3.connect(db_name)
        self.setup_db()

    def setup_db(self):
        """Initialise les tables de la base de données si elles n'existent pas."""
        cur = self.conn.cursor()
        
        # 1. Activation des clés étrangères
        cur.execute("PRAGMA foreign_keys = ON")

        # 2. Table couleurs
        cur.execute("""
            CREATE TABLE IF NOT EXISTS couleurs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT,
                code_hex TEXT UNIQUE
            )
        """)
        
        # 3. Table activites
        cur.execute("""
            CREATE TABLE IF NOT EXISTS activites (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                libelle TEXT,
                parent_id INTEGER,
                id_couleur INTEGER,
                est_visible INTEGER DEFAULT 1,
                FOREIGN KEY (parent_id) REFERENCES activites(id) ON DELETE CASCADE,
                FOREIGN KEY (id_couleur) REFERENCES couleurs(id)
            )
        """)
        
        # 4. Table projets
        cur.execute("""
            CREATE TABLE IF NOT EXISTS projets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT,
                description TEXT,
                date_creation TEXT
            )
        """)

        # 5. Table sessions
        cur.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                id_act INTEGER, 
                nom_saisi TEXT, 
                duree INTEGER, 
                date TEXT,
                id_projet INTEGER,
                FOREIGN KEY (id_act) REFERENCES activites(id),
                FOREIGN KEY (id_projet) REFERENCES projets(id)
            )
        """)
        
        # 6. Table lien projet <-> activites
        cur.execute("""
            CREATE TABLE IF NOT EXISTS projet_activites (
                id_projet INTEGER,
                id_act INTEGER,
                PRIMARY KEY (id_projet, id_act),
                FOREIGN KEY (id_projet) REFERENCES projets(id) ON DELETE CASCADE,
                FOREIGN KEY (id_act) REFERENCES activites(id) ON DELETE CASCADE
            )
        """)
        
        # 7. Table raccourcis
        cur.execute("""
            CREATE TABLE IF NOT EXISTS raccourcis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                libelle TEXT,
                type_raccourci TEXT,
                cible TEXT
            )
        """)

        self.conn.commit()

    def get_activities(self):
        """Récupère toutes les activités."""
        cur = self.conn.cursor()
        cur.execute("SELECT id, libelle, parent_id, id_couleur FROM activites")
        return cur.fetchall()

    def get_activity(self, act_id):
        cur = self.conn.cursor()
        cur.execute("SELECT id, libelle, parent_id, id_couleur FROM activites WHERE id = ?", (act_id,))
        return cur.fetchone()

    def save_session(self, act_id, nom_libre, duree, project_id=None):
        """Enregistre une session de travail dans la base de données."""
        cur = self.conn.cursor()
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        cur.execute("""
            INSERT INTO sessions (id_act, nom_saisi, duree, date, id_projet) 
            VALUES (?, ?, ?, ?, ?)
        """, (act_id, nom_libre, duree, date_str, project_id))
        self.conn.commit()

    def add_activity(self, libelle, parent_id=None, color_id=None):
        """Ajoute une nouvelle activité dans la base de données."""
        cur = self.conn.cursor()
        cur.execute("INSERT INTO activites (libelle, parent_id, id_couleur) VALUES (?, ?, ?)", 
                    (libelle, parent_id, color_id))
        self.conn.commit()

    def update_activity(self, act_id, nom, parent_id, color_id):
        """Met à jour une activité existante."""
        cur = self.conn.cursor()
        cur.execute("UPDATE activites SET libelle = ?, parent_id = ?, id_couleur = ? WHERE id = ?", (nom, parent_id, color_id, act_id))
        self.conn.commit()

    def delete_activity(self, act_id):
        """Supprime une activité et toutes ses dépendances (enfants, sessions)."""
        cur = self.conn.cursor()
        try:
            cur.execute("""
                WITH RECURSIVE descendants(id) AS (
                    SELECT id FROM activites WHERE id = ?
                    UNION ALL
                    SELECT a.id FROM activites a
                    JOIN descendants d ON a.parent_id = d.id
                )
                SELECT id FROM descendants
            """, (act_id,))
            
            ids_to_delete = [row[0] for row in cur.fetchall()]
            
            if ids_to_delete:
                placeholders = ','.join(['?'] * len(ids_to_delete))
                cur.execute(f"DELETE FROM sessions WHERE id_act IN ({placeholders})", ids_to_delete)
                cur.execute("DELETE FROM activites WHERE id = ?", (act_id,))
                
            self.conn.commit()
            
        except Exception as e:
            print(f"Erreur lors de la suppression de l'activité {act_id}: {e}")
            self.conn.rollback()
            raise e

    def get_history(self):
        """Récupère les 10 dernières sessions enregistrées."""
        cur = self.conn.cursor()
        query = """
            SELECT s.date, a.libelle, s.nom_saisi, s.duree
            FROM sessions s
            JOIN activites a ON s.id_act = a.id
            ORDER BY s.date DESC
            LIMIT 10
        """
        cur.execute(query)
        return cur.fetchall()

    def get_today_history(self):
        cur = self.conn.cursor()
        today_start = datetime.now().strftime("%Y-%m-%d") + "%"
        query = """
            SELECT s.date, a.libelle, s.nom_saisi, s.duree
            FROM sessions s
            JOIN activites a ON s.id_act = a.id
            WHERE s.date LIKE ?
            ORDER BY s.date DESC
        """
        cur.execute(query, (today_start,))
        return cur.fetchall()

    def get_week_stats(self):
        cur = self.conn.cursor()
        query = """
            SELECT substr(date, 1, 10) as day, SUM(duree)
            FROM sessions 
            GROUP BY day
            ORDER BY day DESC
            LIMIT 7
        """
        cur.execute(query)
        return cur.fetchall()

    def _get_family_ids(self, root_id):
        cur = self.conn.cursor()
        cur.execute("""
            WITH RECURSIVE descendants(id) AS (
                SELECT id FROM activites WHERE id = ?
                UNION ALL
                SELECT a.id FROM activites a
                JOIN descendants d ON a.parent_id = d.id
            )
            SELECT id FROM descendants
        """, (root_id,))
        return [row[0] for row in cur.fetchall()]

    def get_filtered_history(self, mode, reference_date=None, activity_id=None, project_id=None):
        cur = self.conn.cursor()
        query = """
            SELECT s.date, a.libelle, s.nom_saisi, s.duree
            FROM sessions s
            JOIN activites a ON s.id_act = a.id
            WHERE 1=1
        """
        params = []
        
        if project_id and project_id != "all":
            query += " AND s.id_projet = ?"
            params.append(project_id)
        
        if activity_id and activity_id != "all":
            ids = self._get_family_ids(activity_id)
            if ids:
                placeholders = ','.join(['?'] * len(ids))
                query += f" AND s.id_act IN ({placeholders})"
                params.extend(ids)
        
        if mode == "Aujourd'hui":
            today = datetime.now().strftime("%Y-%m-%d")
            query += " AND s.date LIKE ?"
            params.append(f"{today}%")
        elif mode in ["Période", "Semaine", "Une semaine", "Un mois", "Cette année"]: 
            if isinstance(reference_date, (tuple, list)) and len(reference_date) >= 2:
                start_date = reference_date[0].strftime("%Y-%m-%d")
                end_date = reference_date[1].strftime("%Y-%m-%d")
                query += " AND date(s.date) BETWEEN ? AND ?"
                params.extend([start_date, end_date])
            elif reference_date: 
                 d_str = reference_date.strftime("%Y-%m-%d")
                 query += " AND date(s.date) = ?"
                 params.append(d_str)

        query += " ORDER BY s.date DESC"
        cur.execute(query, tuple(params))
        return cur.fetchall()

    def get_filtered_distribution(self, mode, reference_date=None, activity_id=None, project_id=None):
        cur = self.conn.cursor()
        query = """
            SELECT a.libelle, SUM(s.duree)
            FROM sessions s
            JOIN activites a ON s.id_act = a.id
            WHERE 1=1
        """
        params = []
        
        if project_id and project_id != "all":
            query += " AND s.id_projet = ?"
            params.append(project_id)
            
        if activity_id and activity_id != "all":
            ids = self._get_family_ids(activity_id)
            if ids:
                placeholders = ','.join(['?'] * len(ids))
                query += f" AND s.id_act IN ({placeholders})"
                params.extend(ids)
        
        if mode == "Aujourd'hui":
            today = datetime.now().strftime("%Y-%m-%d")
            query += " AND s.date LIKE ?"
            params.append(f"{today}%")
        elif mode in ["Période", "Semaine", "Une semaine", "Un mois", "Cette année"]:
            if isinstance(reference_date, (tuple, list)) and len(reference_date) >= 2:
                start_date = reference_date[0].strftime("%Y-%m-%d")
                end_date = reference_date[1].strftime("%Y-%m-%d")
                query += " AND date(s.date) BETWEEN ? AND ?"
                params.extend([start_date, end_date])
            
        query += " GROUP BY a.libelle"
        cur.execute(query, tuple(params))
        return cur.fetchall()

    def get_filtered_progression(self, mode, reference_date=None, activity_id=None, project_id=None):
        cur = self.conn.cursor()
        
        where_clause = "WHERE 1=1"
        params = []
        
        if project_id and project_id != "all":
            where_clause += " AND s.id_projet = ?"
            params.append(project_id)
            
        if activity_id and activity_id != "all":
            ids = self._get_family_ids(activity_id)
            if ids:
                placeholders = ','.join(['?'] * len(ids))
                where_clause += f" AND s.id_act IN ({placeholders})"
                params.extend(ids)
        
        granularity = "day"
        start_date_str = None
        end_date_str = None
        
        if mode == "Aujourd'hui":
            granularity = "hour"
            today = datetime.now().strftime("%Y-%m-%d")
            where_clause += " AND s.date LIKE ?"
            params.append(f"{today}%")
            
        elif mode in ["Période", "Semaine", "Une semaine", "Un mois", "Cette année"]:
            if isinstance(reference_date, (tuple, list)) and len(reference_date) >= 2:
                start_date_str = reference_date[0].strftime("%Y-%m-%d")
                end_date_str = reference_date[1].strftime("%Y-%m-%d")
                
                d1 = reference_date[0]
                d2 = reference_date[1]
                delta_days = (d2 - d1).days
                
                # Déterminer la granularité selon le mode et la période
                if mode == "Cette année":
                    granularity = "month"  # Année = affichage par mois
                elif mode == "Un mois":
                    granularity = "week"   # Mois = affichage par semaine
                elif mode == "Une semaine":
                    granularity = "day"    # Semaine = affichage par jour
                elif delta_days > 365:
                    granularity = "month"  # Plus d'un an = par mois
                elif delta_days > 14:
                    granularity = "week"   # Plus de 2 semaines = par semaine
                else:
                    granularity = "day"    # Moins de 2 semaines = par jour
                
                where_clause += " AND date(s.date) >= ? AND date(s.date) <= ?"
                params.extend([start_date_str, end_date_str])
            else:
                 start_date_str = datetime.now().strftime("%Y-%m-%d")
                 end_date_str = start_date_str
                 where_clause += " AND date(s.date) = ?"
                 params.append(start_date_str)
        else: 
            granularity = "month"

        if granularity == "hour":
            query = f"""
                SELECT strftime('%H', s.date) as t, a.libelle, SUM(s.duree)
                FROM sessions s
                JOIN activites a ON s.id_act = a.id
                {where_clause}
                GROUP BY t, a.libelle
                ORDER BY t
            """
        elif granularity == "week":
            query = f"""
                SELECT strftime('%Y-W%W', s.date) as t, a.libelle, SUM(s.duree)
                FROM sessions s
                JOIN activites a ON s.id_act = a.id
                {where_clause}
                GROUP BY t, a.libelle
                ORDER BY t
            """
        elif granularity == "month":
            query = f"""
                SELECT strftime('%Y-%m', s.date) as t, a.libelle, SUM(s.duree)
                FROM sessions s
                JOIN activites a ON s.id_act = a.id
                {where_clause}
                GROUP BY t, a.libelle
                ORDER BY t ASC
            """
        else: 
            query = f"""
                SELECT substr(s.date, 1, 10) as t, a.libelle, SUM(s.duree)
                FROM sessions s
                JOIN activites a ON s.id_act = a.id
                {where_clause}
                GROUP BY t, a.libelle
                ORDER BY t
            """
            
        cur.execute(query, tuple(params))
        return cur.fetchall()

    def get_average_daily_time(self, mode, reference_date=None, activity_id=None, project_id=None):
        cur = self.conn.cursor()
        
        query = "SELECT SUM(duree), MIN(date), MAX(date) FROM sessions WHERE 1=1"
        params = []
        
        if project_id and project_id != "all":
            query += " AND id_projet = ?"
            params.append(project_id)
            
        if activity_id and activity_id != "all":
            query += " AND id_act = ?"
            params.append(activity_id)
        
        start_date_str = None
        end_date_str = None
        
        if mode == "Période" or mode == "Semaine":
            if isinstance(reference_date, (tuple, list)) and len(reference_date) >= 2:
                start_date_str = reference_date[0].strftime("%Y-%m-%d")
                end_date_str = reference_date[1].strftime("%Y-%m-%d")
            else:
                today = datetime.now().date()
                start_date = today - timedelta(days=6)
                start_date_str = start_date.strftime("%Y-%m-%d")
                end_date_str = today.strftime("%Y-%m-%d")
            
            query += " AND date(date) >= ? AND date(date) <= ?"
            params.extend([start_date_str, end_date_str])
        
        elif mode == "Aujourd'hui":
             today = datetime.now().strftime("%Y-%m-%d")
             query += " AND date LIKE ?"
             params.append(f"{today}%")

        cur.execute(query, tuple(params))
        row = cur.fetchone()
        
        total_seconds = row[0] if row and row[0] else 0
        
        num_days = 1
        
        if mode == "Période" or mode == "Semaine":
            if start_date_str and end_date_str:
                d1 = datetime.strptime(start_date_str, "%Y-%m-%d")
                d2 = datetime.strptime(end_date_str, "%Y-%m-%d")
                num_days = (d2 - d1).days + 1
        elif mode == "Global":
            first_date_str = row[1]
            if first_date_str:
                try:
                    first = datetime.strptime(first_date_str.split(" ")[0], "%Y-%m-%d")
                    now = datetime.now()
                    days_diff = (now - first).days
                    num_days = days_diff + 1 if days_diff >= 0 else 1
                except:
                    num_days = 1
            else:
                 num_days = 1
        
        if num_days < 1: num_days = 1
        return total_seconds / num_days

    def add_color(self, nom, code_hex):
        cur = self.conn.cursor()
        try:
            cur.execute("INSERT INTO couleurs (nom, code_hex) VALUES (?, ?)", (nom, code_hex))
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_all_colors(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id, nom, code_hex FROM couleurs")
        return cur.fetchall()

    def update_activity_color(self, act_id, color_id):
        cur = self.conn.cursor()
        cur.execute("UPDATE activites SET id_couleur = ? WHERE id = ?", (color_id, act_id))
        self.conn.commit()

    def create_project(self, nom, description=""):
        """Crée un nouveau projet."""
        cur = self.conn.cursor()
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        cur.execute("INSERT INTO projets (nom, description, date_creation) VALUES (?, ?, ?)", 
                    (nom, description, date_str))
        self.conn.commit()
        return cur.lastrowid

    def get_projects(self):
        """Récupère tous les projets, triés du plus récent au plus ancien."""
        cur = self.conn.cursor()
        cur.execute("SELECT id, nom, description, date_creation FROM projets ORDER BY date_creation DESC")
        return cur.fetchall()

    def delete_project(self, project_id):
        """Supprime un projet et met à jour les sessions associées."""
        cur = self.conn.cursor()
        try:
            # Mettre à NULL le projet dans les sessions (au lieu de supprimer les sessions)
            cur.execute("UPDATE sessions SET id_projet = NULL WHERE id_projet = ?", (project_id,))
            # Supprimer le projet (CASCADE supprimera aussi les liens dans projet_activites)
            cur.execute("DELETE FROM projets WHERE id = ?", (project_id,))
            self.conn.commit()
        except Exception as e:
            print(f"Erreur lors de la suppression du projet {project_id}: {e}")
            self.conn.rollback()
            raise e

    def link_activity_to_project(self, project_id, act_id):
        cur = self.conn.cursor()
        try:
            cur.execute("INSERT INTO projet_activites (id_projet, id_act) VALUES (?, ?)", (project_id, act_id))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass

    def unlink_activity_from_project(self, project_id, act_id):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM projet_activites WHERE id_projet = ? AND id_act = ?", (project_id, act_id))
        self.conn.commit()

    def get_project_activities(self, project_id):
        cur = self.conn.cursor()
        cur.execute("""
            SELECT a.id, a.libelle, a.id_couleur 
            FROM activites a
            JOIN projet_activites pa ON a.id = pa.id_act
            WHERE pa.id_projet = ?
        """, (project_id,))
        return cur.fetchall()

    def add_shortcut(self, libelle, type_r, cible):
        cur = self.conn.cursor()
        cur.execute("INSERT INTO raccourcis (libelle, type_raccourci, cible) VALUES (?, ?, ?)", 
                    (libelle, type_r, cible))
        self.conn.commit()
        return cur.lastrowid

    def get_shortcuts(self):
        cur = self.conn.cursor()
        cur.execute("SELECT id, libelle, type_raccourci, cible FROM raccourcis")
        return cur.fetchall()

    def get_shortcut_overrides(self):
        shortcuts = self.get_shortcuts()
        return {s[1]: s[3] for s in shortcuts}

    def update_shortcut(self, action_code, key_sequence):
        cur = self.conn.cursor()
        cur.execute("SELECT id FROM raccourcis WHERE libelle = ?", (action_code,))
        row = cur.fetchone()
        
        if row:
            cur.execute("UPDATE raccourcis SET cible = ? WHERE id = ?", (key_sequence, row[0]))
        else:
            cur.execute("INSERT INTO raccourcis (libelle, type_raccourci, cible) VALUES (?, ?, ?)", 
                        (action_code, "CLAVIER", key_sequence))
        self.conn.commit()

    def get_visible_activity_ids(self):
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT id FROM activites WHERE est_visible = 1")
            return [row[0] for row in cur.fetchall()]
        except sqlite3.OperationalError:
            return []

    def set_visible_activities(self, ids):
        cur = self.conn.cursor()
        cur.execute("UPDATE activites SET est_visible = 0")
        if ids:
            placeholders = ','.join(['?'] * len(ids))
            query = f"UPDATE activites SET est_visible = 1 WHERE id IN ({placeholders})"
            cur.execute(query, ids)
        self.conn.commit()

    def has_children(self, parent_id):
        """Vérifie si une activité parent a des enfants."""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM activites WHERE parent_id = ?", (parent_id,))
        result = cur.fetchone()
        return result[0] > 0

    def get_children_count(self, parent_id):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM activites WHERE parent_id = ?", (parent_id,))
        result = cur.fetchone()
        return result[0]

    def get_export_data(self, mode, reference_date=None, project_id=None):
        """
        Récupère les données brutes pour l'export CSV.
        Retourne une liste de tuples : (id, date_debut, date_fin, nom_projet, nom_activite, duree_sec)
        """
        cur = self.conn.cursor()
        
        # Construction de la requête avec Jointures
        # On utilise datetime pour calculer la date de fin
        query = """
            SELECT 
                s.id, 
                s.date, 
                datetime(s.date, '+' || s.duree || ' seconds') as date_fin,
                p.nom, 
                a.libelle, 
                s.duree
            FROM sessions s
            JOIN activites a ON s.id_act = a.id
            LEFT JOIN projets p ON s.id_projet = p.id
            WHERE 1=1
        """
        params = []
        
        # Filtre Projet
        if project_id and project_id != "all":
            query += " AND s.id_projet = ?"
            params.append(project_id)
        
        # Filtre Date / Mode
        if mode == "Aujourd'hui":
            today = datetime.now().strftime("%Y-%m-%d")
            query += " AND s.date LIKE ?"
            params.append(f"{today}%")
            
        elif mode == "Période" or mode == "Semaine": 
            if isinstance(reference_date, (tuple, list)) and len(reference_date) >= 2:
                start_date = reference_date[0].strftime("%Y-%m-%d")
                end_date = reference_date[1].strftime("%Y-%m-%d")
                query += " AND date(s.date) BETWEEN ? AND ?"
                params.extend([start_date, end_date])
            elif reference_date: 
                 d_str = reference_date.strftime("%Y-%m-%d")
                 query += " AND date(s.date) = ?"
                 params.append(d_str)

        query += " ORDER BY s.date DESC"
        
        cur.execute(query, tuple(params))
        return cur.fetchall()
