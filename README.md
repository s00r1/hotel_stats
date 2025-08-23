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
- Légende détaillée des graphiques.
- Tri et recherche dynamiques sur les listes de familles et de personnes.
- Sélecteur de thème clair/sombre.
- Sauvegarde et restauration des données en JSON.

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

### 📊 Légende détaillée des graphiques

Les couleurs des diagrammes représentent clairement les catégories :

```javascript
window.activeCharts.push(new Chart(document.getElementById('sexChart'), {
  type: 'doughnut',
  data: {
    labels: ['Femmes', 'Hommes', 'Autre/NP'],
    datasets: [{
      backgroundColor: ['#e83e8c', '#007bff', '#6c757d']
    }]
  },
  options: { plugins: { legend: { position: 'bottom' } } }
}));
```

### 🔍 Tri et recherche sur les listes

Les tableaux des familles et des personnes s’appuient sur **DataTables** pour offrir un tri et une recherche instantanés.

```javascript
document.querySelectorAll('.sortable-table').forEach(t => new DataTable(t, {
  columnDefs: [
    { orderable: false, targets: [0,5,6,7,8] },
    { visible: false, targets: [7,8] }
  ],
  language: { url: 'https://cdn.datatables.net/plug-ins/2.0.8/i18n/fr-FR.json' }
}));
```

### 🎨 Sélecteur de thème

Un bouton permet de basculer entre les thèmes **clair** et **sombre** en mémorisant le choix dans `localStorage`.

```javascript
const themeKey = 'theme';
function applyTheme(t) {
  document.documentElement.setAttribute('data-bs-theme', t);
}
applyTheme(localStorage.getItem(themeKey) || 'dark');
document.getElementById('themeToggle').addEventListener('click', () => {
  const next = document.documentElement.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
  localStorage.setItem(themeKey, next);
  applyTheme(next);
});
```

### 💾 Sauvegarde et restauration

L’interface propose l’export des données au format **JSON** et la restauration depuis un fichier de sauvegarde :

```html
<form method="post" enctype="multipart/form-data"
      onsubmit="return confirm('Cette action écrasera les données actuelles. Continuer ?');">
  <input type="file" name="file" accept="application/json" required>
  <button class="btn btn-danger" name="confirm" value="yes">Restaurer</button>
</form>
```

Pour sauvegarder, utilisez le bouton **Exporter** depuis le tableau de bord ;
pour restaurer, accédez à la page **Restauration** et téléversez le fichier obtenu précédemment.

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
