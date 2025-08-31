# Social Hotel – Kardex & Statistics
**Languages: [Français](README.md) | [English](README.en.md) | [العربية](README.ar.md)**

Lightweight web application to manage families hosted in a social hotel and analyze the hosted population. Built with **Flask**, **SQLite**, **Bootstrap** and **Chart.js**.

The goal is to offer a pleasant experience by taking care of both **interface** and **data**. Interactive charts, responsive tables, and customizable themes provide a clear presentation, while the database ensures reliable and complete content.

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

### 📚 Content & Statistics

- Complete management of families and people (add, edit, delete).
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

## ⚙️ Interface Configuration

The **Configuration** page adapts the app to your hotel. Access it via the navigation bar; top buttons let you **export** or **import** your settings in JSON.

### Tab "Hotel"

#### Sub‑tab "Rooms"

- **Total number of rooms**: overall rooms managed.
- **Numbering type**: choose *Numeric*, *Alphabetic* or *Mixed*.
- **Numbering ranges**: specify start and end values (e.g., `1` to `20` or `A` to `D`).
- **Excluded rooms**: comma‑separated list of rooms to ignore (e.g., `13,A1`).

#### Sub‑tab "Occupation"

- **Default maximum occupancy**: standard capacity for each room.
- **Room groups**: define sets of rooms sharing a capacity (e.g., `1-5:3` means rooms 1–5 limited to 3 people).
- **Per-room occupancy**: set a specific capacity for individual room numbers.

### Tab "Alerts"

Enable or disable automatic reminders shown on the dashboard:

- **Free rooms**: highlight unoccupied rooms.
- **Overcrowding**: flag rooms exceeding their capacity.
- **Isolated women**: identify women hosted without another adult.
- **Baby age**: raise an alert for children below the chosen age limit.

### Tab "Layout"

Used to draw the hotel's floor plan:

- **Cell width/height** and **horizontal/vertical gaps**: control the grid.
- **Item palette**: drag elements (room, stairs, etc.) to build each floor.
- **Floor management**: add multiple levels and adjust zoom to refine the layout.

Click **Save** when finished to store your configuration.

## 💾 Backup & Export

- **Export** button to obtain a JSON file with all data.
- **Restore** page to import a previously saved file.
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
