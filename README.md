# Hôtel Social – Kardex & Statistiques

Cette application web légère permet de gérer les familles hébergées dans un hôtel social et de visualiser des statistiques sur les personnes accueillies. Elle est conçue avec **Flask** et **SQLite** pour la partie serveur, et **Bootstrap** + **Chart.js** pour l’interface graphique.

## 🧩 Fonctionnalités

- Gestion des familles et des personnes (ajout, édition, suppression).
- Tableau de bord avec :
  - nombre total de clients,
  - répartition par sexe,
  - graphiques des tranches d’âge séparant filles et garçons,
  - rappel automatique des anniversaires du jour.
- Export/Import CSV des données.

## 🛠️ Installation locale

1. **Cloner le dépôt**
   ```bash
   git clone https://example.com/hotel_stats.git
   cd hotel_stats
   ```
2. **Créer un environnement virtuel** (facultatif mais recommandé)
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows : venv\Scripts\activate
   ```
3. **Installer les dépendances**
   ```bash
   pip install flask flask_sqlalchemy python-dateutil
   ```
4. **Lancer l’application**
   ```bash
   python app.py
   ```
   Le site est ensuite accessible sur [http://127.0.0.1:5000](http://127.0.0.1:5000).

## 💻 Utilisation

- Rendez-vous sur la page d’accueil pour consulter les statistiques et le rappel des anniversaires.
- Utilisez le menu pour gérer les familles puis les personnes (kardex).
- Les formulaires permettent de saisir les dates de naissance et le sexe afin d’alimenter correctement les statistiques.

## ☁️ Hébergement sur Internet

Pour mettre l’application en production :

1. **Configurer les variables d’environnement**
   ```bash
   export FLASK_ENV=production
   export DATABASE_URL="sqlite:///hotel_social.db"  # ou autre SGBD
   ```
2. **Utiliser un serveur WSGI** comme [Gunicorn](https://gunicorn.org/)
   ```bash
   pip install gunicorn
   gunicorn -w 4 app:app
   ```
3. **Placer l’application derrière un serveur HTTP** (Nginx, Apache) et configurer le reverse proxy.
4. **Sécuriser la base de données** et réaliser des sauvegardes régulières.

## 📝 Notes

- L’application crée automatiquement le fichier `hotel_social.db` au premier lancement.
- Chart.js et Bootstrap sont chargés via CDN ; assurez‑vous que le serveur a accès à Internet.

Bon développement ! 🎉
