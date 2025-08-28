# Hôtel Social – Kardex & Statistiques
**Langues : [Français](README.md) | [English](README.en.md) | [العربية](README.ar.md)**

Application web légère pour gérer les familles hébergées dans un hôtel social et analyser la population accueillie. Conçue avec **Flask**, **SQLite**, **Bootstrap** et **Chart.js**.

L'objectif est de proposer une expérience conviviale en soignant autant **l'interface** que **les données**. Les graphiques, les tableaux responsives et les thèmes personnalisables offrent une présentation claire, tandis que la base de données assure un contenu fiable et complet.

## Sommaire
- [Fonctionnalités](#-fonctionnalités)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [Sauvegarde & export](#-sauvegarde--export)
- [Hébergement](#-hébergement)
- [Licence](#-licence)

## ✨ Fonctionnalités

### 🎨 Présentation

- Tableaux triables et filtrables grâce à *DataTables*.
- Graphiques interactifs illustrés par *Chart.js*.
- Sélecteur de thème clair/sombre avec mémorisation.
- Plan des chambres interactif affichant l'occupation et les chambres libres.

### 📚 Contenu & statistiques

- Gestion complète des familles et des personnes (ajout, édition, suppression).
- Tableau de bord interactif :
  - statistiques globales (sexe, tranches d’âge, adultes/enfants),
  - visualisation du plan des chambres avec détail de l'occupation,
  - alertes automatiques (sur‑occupation, femmes isolées, bébés < 1 an, chambres disponibles),
  - rappel des anniversaires du jour et des semaines/mois alentours,
  - classement des familles, adultes et enfants les plus anciens/récents.
- Recherche multi‑critères sur les familles et les personnes en cours d’hébergement.
- Consultation des archives (familles/personnes sorties) avec filtres.
- Export CSV des familles et des personnes.
- Sauvegarde/Restauration JSON des données.

## 🛠️ Installation

1. Cloner le dépôt :

```bash
git clone https://example.com/hotel_stats.git
cd hotel_stats
```

2. (Optionnel) Créer un environnement virtuel :

```bash
python -m venv venv
source venv/bin/activate  # Sous Windows : venv\Scripts\activate
```

3. Installer les dépendances :

```bash
pip install -r requirements.txt
```

4. Lancer l’application :

```bash
python app.py
```

Le site est accessible sur [http://127.0.0.1:5000](http://127.0.0.1:5000).

## 💻 Utilisation

- Accédez au tableau de bord pour visualiser les statistiques, alertes et anniversaires.
- Gérez les **familles** puis les **personnes** via le menu.
- Utilisez les pages **Recherche** et **Archives** pour filtrer les dossiers.
- Les tableaux sont triables et filtrables, et les formulaires acceptent les dates et le sexe pour alimenter les statistiques.

## 💾 Sauvegarde & export

- Bouton **Exporter** pour obtenir un fichier JSON de toutes les données.
- Page **Restauration** pour réinjecter un fichier précédemment sauvegardé.
- Export CSV des familles et des personnes disponible depuis la barre de navigation.

## ☁️ Hébergement

Pour la production :

1. Définir les variables d’environnement :

```bash
export FLASK_ENV=production
export DATABASE_URL="sqlite:///hotel_social.db"  # ou autre SGBD
```

2. Utiliser un serveur WSGI comme [Gunicorn](https://gunicorn.org/) :

```bash
pip install gunicorn
gunicorn -w 4 app:app
```

3. Mettre l’application derrière un serveur HTTP (Nginx, Apache) et configurer le reverse proxy.
4. Sécuriser la base de données et effectuer des sauvegardes régulières.

## 📄 Licence

Ce projet est distribué sous licence [MIT](LICENSE).

Bon développement ! 🎉
