# Social Hotel – Kardex & Statistics
**Languages: [Français](README.md) | [English](README.en.md) | [العربية](README.ar.md)**

Lightweight web application to manage families hosted in a social hotel and analyze the hosted population. Built with **Flask**, **SQLite**, **Bootstrap** and **Chart.js**.

The goal is to offer a pleasant experience by taking care of both **interface** and **data**. Interactive charts, responsive tables, and customizable themes provide a clear presentation, while the database ensures reliable and complete content.

Recent updates bring a **full configuration page** (rooms, alerts, interactive layout) and phone number fields for families and individuals.

## Table of Contents
- [Features](#-features)
- [Installation](#-installation)
- [Usage](#-usage)
- [Backup & Export](#-backup--export)
- [Hosting](#-hosting)
- [License](#-license)

## ✨ Features

### 🎨 Presentation

- Sortable and filterable tables powered by *DataTables*.
- Interactive charts with *Chart.js*.
- Light/dark theme selector with persistence.
- Interactive room layout showing occupancy and free rooms.
- Drag-and-drop layout editor to design floors.

### 📚 Content & Statistics

- Complete management of families and people (add, edit, delete).
- Configuration page to define rooms, capacity limits and alerts.
- Interactive dashboard:
  - global statistics (gender, age ranges, adults/children),
  - room layout visualization with occupancy details,
  - automatic alerts (overcrowding, isolated women, babies < 1 year, available rooms),
  - birthday reminders for the day, upcoming weeks/months,
  - ranking of oldest/newest families, adults and children.
- Multi-criteria search for families and people currently hosted.
- Archive consultation (departed families/people) with filters.
- CSV export of families and people.
- JSON backup/restore of data.
- Phone numbers for families and individuals, plus a second room field for families.

## 🛠️ Installation

1. Clone the repository:

```bash
git clone https://example.com/hotel_stats.git
cd hotel_stats
```

2. (Optional) Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Run the application:

```bash
python app.py
```

The site is available at [http://127.0.0.1:5000](http://127.0.0.1:5000).

## 💻 Usage

- Access the dashboard to view statistics, alerts, and birthdays.
- Manage **families** then **people** via the menu.
- Use the **Search** and **Archives** pages to filter records.
- Tables are sortable and filterable, and forms accept dates and gender to feed statistics.

## 💾 Backup & Export

- **Export** button to obtain a JSON file with all data.
- **Restore** page to import a previously saved file.
- Save/load the hotel configuration from the interface.
- CSV export of families and people available from the navigation bar.

## ☁️ Hosting

For production:

1. Set environment variables:

```bash
export FLASK_ENV=production
export DATABASE_URL="sqlite:///hotel_social.db"  # or another DBMS
```

2. Use a WSGI server like [Gunicorn](https://gunicorn.org/):

```bash
pip install gunicorn
gunicorn -w 4 app:app
```

3. Put the application behind an HTTP server (Nginx, Apache) and configure reverse proxy.
4. Secure the database and perform regular backups.

## 📄 License

This project is distributed under the [MIT](LICENSE) license.

Happy coding! 🎉
