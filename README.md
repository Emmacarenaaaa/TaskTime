# TaskTime - Gestionnaire de Temps et Productivité

Application de suivi du temps et de gestion de la productivité développée avec PySide6 (Qt for Python). TaskTime permet de suivre vos activités, projets et sessions de travail avec des visualisations graphiques détaillées.

## Table des matières

- [Fonctionnalités](#fonctionnalités)
- [Prérequis](#prérequis)
- [Installation](#installation)
  - [Windows](#installation-windows)
  - [macOS](#installation-macos)
- [Configuration du projet](#configuration-du-projet)
- [Utilisation](#utilisation)
- [Compilation en exécutable](#compilation-en-exécutable)
- [Architecture](#architecture)
- [Technologies utilisées](#technologies-utilisées)

---

## Fonctionnalités

- **Chronomètre interactif** : Suivi du temps en temps réel avec interface visuelle à bulles
- **Gestion d'activités** : Organisation hiérarchique des activités (parent/sous-activités)
- **Projets** : Association des sessions de travail à des projets spécifiques
- **Analyses visuelles** : Graphiques de répartition et d'évolution du temps
- **Filtres temporels** : Aujourd'hui, semaine, mois, année, période personnalisée
- **Export CSV** : Exportation des données pour analyse externe
- **Interface moderne** : Design sombre avec thème rose/violet

---

## Prérequis

### Tous systèmes

- **Python 3.8 ou supérieur**
- **pip** (gestionnaire de paquets Python)

### Windows

- Windows 10 ou supérieur
- PowerShell

### macOS

- macOS 10.14 (Mojave) ou supérieur
- Terminal

---

## Installation

### Installation Windows

#### 1. Installation de Python

1. Télécharger Python depuis [python.org](https://www.python.org/downloads/)
2. Lors de l'installation, **cocher impérativement** la case **"Add Python to PATH"**
3. Vérifier l'installation :
   ```powershell
   python --version
   ```

#### 2. Création de l'environnement virtuel

Ouvrir PowerShell dans le dossier du projet :

```powershell
# Créer le dossier du projet et y accéder
mkdir MonProjetChrono
cd MonProjetChrono

# Créer l'environnement virtuel
python -m venv venv

# Activer l'environnement virtuel
.\venv\Scripts\activate
```

#### 3. Installation des dépendances

Une fois l'environnement activé :

```powershell
pip install PySide6
pip install matplotlib
```

**Note** : SQLite3 est inclus avec Python par défaut.

---

### Installation macOS

#### 1. Installation de Python

Python 3 est généralement préinstallé sur macOS. Vérifier la version :

```bash
python3 --version
```

Si Python n'est pas installé ou si la version est inférieure à 3.8 :

```bash
# Installer Homebrew si nécessaire
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Installer Python
brew install python@3.11
```

#### 2. Création de l'environnement virtuel

Ouvrir Terminal dans le dossier du projet :

```bash
# Créer le dossier du projet et y accéder
mkdir MonProjetChrono
cd MonProjetChrono

# Créer l'environnement virtuel
python3 -m venv venv

# Activer l'environnement virtuel
source venv/bin/activate
```

#### 3. Installation des dépendances

Une fois l'environnement activé :

```bash
pip install PySide6
pip install matplotlib
```

---

## Configuration du projet

### Structure du projet

```
TaskTime/
├── main.py                 # Point d'entrée de l'application
├── models/
│   └── database.py         # Gestion de la base de données SQLite
├── vues/
│   ├── login.py            # Interface de connexion
│   ├── chrono.py           # Interface du chronomètre
│   ├── activites.py        # Gestion des activités
│   ├── analyses.py         # Visualisations et analyses
│   ├── accueil.py          # Page d'accueil
│   ├── settings.py         # Paramètres
│   ├── custom_dialog.py    # Dialogues personnalisés
│   └── color_picker.py     # Sélecteur de couleur
├── presenters/
│   ├── chrono.py           # Logique du chronomètre
│   ├── activites.py        # Logique des activités
│   ├── analyses.py         # Logique des analyses
│   ├── accueil.py          # Logique de l'accueil
│   └── settings.py         # Logique des paramètres
├── style/
│   └── style.qss           # Feuille de style Qt
├── assets/                 # Ressources (images, icônes)
├── requirements.txt        # Liste des dépendances
└── README.md              # Documentation
```

### Initialisation de la base de données

Au premier lancement, l'application créera automatiquement la base de données SQLite (`chrono.db`) avec les tables nécessaires.

---

## Utilisation

### Lancement de l'application

#### Windows (PowerShell)

```powershell
# Activer l'environnement virtuel
.\venv\Scripts\activate

# Lancer l'application
python main.py
```

#### macOS (Terminal)

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Lancer l'application
python main.py
```

### Fonctionnalités principales

1. **Chronomètre** : Cliquez sur une bulle d'activité pour démarrer le suivi
2. **Activités** : Créez et organisez vos activités avec des couleurs personnalisées
3. **Projets** : Associez vos sessions à des projets pour une meilleure organisation
4. **Analyses** : Consultez vos statistiques avec différentes périodes de filtrage
5. **Export** : Exportez vos données au format CSV pour analyse externe

---

## Compilation en exécutable

Pour distribuer l'application sans nécessiter Python, utilisez PyInstaller.

### Installation de PyInstaller

```bash
pip install pyinstaller
```

### Compilation

#### Windows

```powershell
pyinstaller --noconsole --onefile --windowed main.py
```

#### macOS

```bash
pyinstaller --noconsole --onefile --windowed main.py
```

### Options de compilation

- `--noconsole` : Supprime la fenêtre de console en arrière-plan
- `--onefile` : Package l'application dans un seul fichier exécutable
- `--windowed` : Indique qu'il s'agit d'une application graphique (requis pour PySide6/Qt)

L'exécutable sera généré dans le dossier `dist/`.

---

## Architecture

L'application suit le pattern **MVP (Model-View-Presenter)** :

- **Models** : Gestion des données et de la base de données SQLite
- **Views** : Interfaces graphiques (widgets PySide6)
- **Presenters** : Logique métier et communication entre Models et Views

### Base de données

**SQLite3** est utilisé pour le stockage local des données.

#### Schéma principal

- **utilisateurs** : Gestion des utilisateurs (actuellement mono-utilisateur)
- **activites** : Activités et sous-activités avec hiérarchie
- **couleurs** : Palette de couleurs pour les activités
- **projets** : Projets associés aux sessions
- **sessions** : Enregistrements de temps de travail
- **raccourcis** : Raccourcis clavier personnalisables

---

## Technologies utilisées

| Bibliothèque | Version minimale | Utilité |
|--------------|------------------|---------|
| **PySide6** | 6.0.0 | Framework d'interface graphique (Qt for Python) |
| **matplotlib** | 3.0.0 | Génération de graphiques et visualisations |
| **SQLite3** | Inclus avec Python | Base de données locale |

### Outils de développement recommandés

- **Visual Studio Code** avec l'extension "SQLite Viewer" pour visualiser la base de données
- **Qt Designer** (optionnel) pour la conception d'interfaces

---

## Support et contribution

Pour toute question ou suggestion d'amélioration, veuillez ouvrir une issue sur le dépôt du projet.

---

## Licence

Ce projet est développé à des fins éducatives et personnelles.
