# app.py  —  Hôtel Social • Kardex + Stats (Flask + SQLite + Chart.js)
# Python 3.12 x64 recommandé

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from io import StringIO
import csv
import json

from flask import Flask, request, redirect, url_for, render_template_string, make_response
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///hotel_social.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ============================
# Modèles
# ============================

class Family(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(120), index=True)         # ex: "Famille Dupont"
    room_number = db.Column(db.String(20), index=True)
    arrival_date = db.Column(db.Date, index=True)

    persons = db.relationship("Person", backref="family", cascade="all,delete", lazy="dynamic")

class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey("family.id"), index=True, nullable=False)
    first_name = db.Column(db.String(80), index=True, nullable=False)
    last_name  = db.Column(db.String(80), index=True, nullable=False)
    dob = db.Column(db.Date, index=True)
    sex = db.Column(db.String(12), index=True)            # "F","M","Autre/NP"

# ============================
# Helpers
# ============================

AGE_BUCKETS = [
    ("0-2",   0, 2),
    ("3-5",   3, 5),
    ("6-12",  6, 12),
    ("13-17", 13, 17),
    ("18-24", 18, 24),
    ("25-39", 25, 39),
    ("40-59", 40, 59),
    ("60+",   60, 200),
]

# Couleurs des tranches d'âge (Femmes / Hommes)
AGE_COLORS_F = ['#8bd0db', '#8fe4cb', '#93d3a2', '#ffe083', '#febe89', '#ed9aa2', '#b7a0e0', '#999c9f']
AGE_COLORS_M = ['#128193', '#19a078', '#208537', '#cc9a05', '#ca6410', '#b02a37', '#58349a', '#292e33']

SEX_CHOICES = ["F", "M", "Autre/NP"]

def parse_date(s: str | None):
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None

def fmt_date(d: date | None):
    if not d:
        return ""
    return d.strftime("%d/%m/%Y")

def age_years(dob: date | None, ref: date | None = None) -> int | None:
    if not dob:
        return None
    ref = ref or date.today()
    return relativedelta(ref, dob).years

def bucket_for_age(a: int | None):
    if a is None:
        return None
    for label, lo, hi in AGE_BUCKETS:
        if lo <= a <= hi:
            return label
    return None

def page(content_html: str, **ctx):
    """Injecte un fragment HTML dans le layout de base."""
    return render_template_string(
        TPL_BASE,
        content=render_template_string(content_html, fmt_date=fmt_date, **ctx),
    )

# ============================
# Routes
# ============================

@app.route("/")
def dashboard():
    today = date.today()
    persons = Person.query.all()

    # Répartition sexes
    sex_counts = {k: 0 for k in SEX_CHOICES}
    # Tranches d'âge par sexe
    age_counts = {b[0]: {"F": 0, "M": 0} for b in AGE_BUCKETS}

    for p in persons:
        s = p.sex if p.sex in sex_counts else "Autre/NP"
        sex_counts[s] += 1
        a = age_years(p.dob, today)
        b = bucket_for_age(a)
        if b and s in ("F", "M"):
            age_counts[b][s] += 1

    # Anniversaires du jour
    birthdays = [
        p for p in persons
        if p.dob and p.dob.month == today.month and p.dob.day == today.day
    ]

    # Familles récentes
    families = Family.query.order_by(Family.arrival_date.desc().nullslast(), Family.id.desc()).all()

    return page(
        TPL_DASHBOARD,
        total_clients=len(persons),
        sex_labels=list(sex_counts.keys()),
        sex_values=list(sex_counts.values()),
        age_labels=list(age_counts.keys()),
        age_f_values=[age_counts[k]["F"] for k in age_counts.keys()],
        age_m_values=[age_counts[k]["M"] for k in age_counts.keys()],
        age_colors_f=AGE_COLORS_F,
        age_colors_m=AGE_COLORS_M,
        families=families,
        birthdays=birthdays
    )

# ----- Familles -----

@app.route("/families")
def families_list():
    q = Family.query
    room = (request.args.get("room") or "").strip()
    label = (request.args.get("label") or "").strip()
    dmin = parse_date(request.args.get("dmin"))
    dmax = parse_date(request.args.get("dmax"))

    if room:
        q = q.filter(Family.room_number.like(f"%{room}%"))
    if label:
        q = q.filter(Family.label.like(f"%{label}%"))
    if dmin:
        q = q.filter(Family.arrival_date >= dmin)
    if dmax:
        q = q.filter(Family.arrival_date <= dmax)

    families = q.order_by(Family.arrival_date.desc().nullslast(), Family.id.desc()).all()
    return page(TPL_FAMILIES, families=families, room=room, label=label,
                dmin=request.args.get("dmin") or "", dmax=request.args.get("dmax") or "")

@app.route("/families/new", methods=["GET","POST"])
def families_new():
    if request.method == "POST":
        f = Family(
            label=request.form.get("label") or None,
            room_number=request.form.get("room_number") or None,
            arrival_date=parse_date(request.form.get("arrival_date"))
        )
        db.session.add(f)
        db.session.commit()
        return redirect(url_for("families_list"))
    return page(TPL_FAMILY_FORM, family=None)

@app.route("/families/<int:fid>/edit", methods=["GET","POST"])
def families_edit(fid):
    fam = Family.query.get_or_404(fid)
    if request.method == "POST":
        fam.label = request.form.get("label") or None
        fam.room_number = request.form.get("room_number") or None
        fam.arrival_date = parse_date(request.form.get("arrival_date"))
        db.session.commit()
        return redirect(url_for("families_list"))
    return page(TPL_FAMILY_FORM, family=fam)

@app.route("/families/<int:fid>/delete", methods=["POST"])
def families_delete(fid):
    fam = Family.query.get_or_404(fid)
    db.session.delete(fam)
    db.session.commit()
    return redirect(url_for("families_list"))

# ----- Personnes -----

@app.route("/persons/<int:fid>")
def persons_list(fid):
    fam = Family.query.get_or_404(fid)
    today = date.today()
    rows = []
    for p in fam.persons.order_by(Person.id.asc()).all():
        rows.append({
            "id": p.id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "dob": p.dob,
            "sex": p.sex,
            "age": age_years(p.dob, today)
        })
    return page(TPL_PERSONS, family=fam, persons=rows)

@app.route("/persons/<int:fid>/new", methods=["GET","POST"])
def persons_new(fid):
    fam = Family.query.get_or_404(fid)
    if request.method == "POST":
        p = Person(
            family_id=fid,
            first_name=request.form.get("first_name").strip(),
            last_name=request.form.get("last_name").strip(),
            dob=parse_date(request.form.get("dob")),
            sex=request.form.get("sex") or "Autre/NP"
        )
        db.session.add(p)
        db.session.commit()
        return redirect(url_for("persons_list", fid=fid))
    return page(TPL_PERSON_FORM, family=fam, person=None, sex_choices=SEX_CHOICES)

@app.route("/persons/<int:fid>/<int:pid>/edit", methods=["GET","POST"])
def persons_edit(fid, pid):
    fam = Family.query.get_or_404(fid)
    p = Person.query.get_or_404(pid)
    if request.method == "POST":
        p.first_name = request.form.get("first_name").strip()
        p.last_name  = request.form.get("last_name").strip()
        p.dob = parse_date(request.form.get("dob"))
        p.sex = request.form.get("sex") or "Autre/NP"
        db.session.commit()
        return redirect(url_for("persons_list", fid=fid))
    return page(TPL_PERSON_FORM, family=fam, person=p, sex_choices=SEX_CHOICES)

@app.route("/persons/<int:fid>/<int:pid>/delete", methods=["POST"])
def persons_delete(fid, pid):
    p = Person.query.get_or_404(pid)
    db.session.delete(p)
    db.session.commit()
    return redirect(url_for("persons_list", fid=fid))

# ----- Export CSV -----

@app.route("/export/families.csv")
def export_families_csv():
    out = StringIO()
    w = csv.writer(out, dialect="excel")
    w.writerow(["id","label","room_number","arrival_date","num_persons"])
    for f in Family.query.order_by(Family.id.asc()).all():
        w.writerow([f.id, f.label or "", f.room_number or "", f.arrival_date or "", f.persons.count()])
    resp = make_response(out.getvalue().encode("utf-8-sig"))
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    resp.headers["Content-Disposition"] = "attachment; filename=families.csv"
    return resp

@app.route("/export/persons.csv")
def export_persons_csv():
    out = StringIO()
    w = csv.writer(out, dialect="excel")
    w.writerow(["id","family_id","family_label","room_number","last_name","first_name","dob","sex","age"])
    today = date.today()
    for p in Person.query.order_by(Person.id.asc()).all():
        fam = p.family
        w.writerow([p.id, fam.id, fam.label or "", fam.room_number or "", p.last_name, p.first_name, p.dob or "", p.sex or "", age_years(p.dob, today) or ""])
    resp = make_response(out.getvalue().encode("utf-8-sig"))
    resp.headers["Content-Type"] = "text/csv; charset=utf-8"
    resp.headers["Content-Disposition"] = "attachment; filename=persons.csv"
    return resp

# ----- Sauvegarde / Restauration JSON -----

@app.route("/backup")
def backup():
    data = {
        "families": [
            {
                "id": f.id,
                "label": f.label,
                "room_number": f.room_number,
                "arrival_date": f.arrival_date.isoformat() if f.arrival_date else None,
            }
            for f in Family.query.order_by(Family.id.asc()).all()
        ],
        "persons": [
            {
                "id": p.id,
                "family_id": p.family_id,
                "first_name": p.first_name,
                "last_name": p.last_name,
                "dob": p.dob.isoformat() if p.dob else None,
                "sex": p.sex,
            }
            for p in Person.query.order_by(Person.id.asc()).all()
        ],
    }
    resp = make_response(json.dumps(data, ensure_ascii=False))
    resp.headers["Content-Type"] = "application/json; charset=utf-8"
    resp.headers["Content-Disposition"] = "attachment; filename=backup.json"
    return resp

@app.route("/restore", methods=["GET", "POST"])
def restore():
    if request.method == "POST":
        if request.form.get("confirm") != "yes":
            return redirect(url_for("restore"))
        file = request.files.get("file")
        if not file:
            return redirect(url_for("restore"))
        data = json.load(file)
        Person.query.delete()
        Family.query.delete()
        db.session.commit()
        db.session.execute(db.text("DELETE FROM sqlite_sequence WHERE name IN ('family','person')"))
        db.session.commit()
        for f in data.get("families", []):
            fam = Family(
                id=f.get("id"),
                label=f.get("label"),
                room_number=f.get("room_number"),
                arrival_date=parse_date(f.get("arrival_date")),
            )
            db.session.add(fam)
        db.session.commit()
        for p in data.get("persons", []):
            pers = Person(
                id=p.get("id"),
                family_id=p.get("family_id"),
                first_name=p.get("first_name"),
                last_name=p.get("last_name"),
                dob=parse_date(p.get("dob")),
                sex=p.get("sex"),
            )
            db.session.add(pers)
        db.session.commit()
        return redirect(url_for("dashboard"))
    return page(TPL_RESTORE)

# ============================
# Templates (inline + layout propre)
# ============================

TPL_BASE = """
<!doctype html>
<html lang="fr" data-bs-theme="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Kardex Hôtel Social</title>
  <!-- Bootswatch (Darkly) + Icons -->
  <link href="https://cdn.jsdelivr.net/npm/bootswatch@5.3.3/dist/darkly/bootstrap.min.css" rel="stylesheet">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css" rel="stylesheet">
  <!-- DataTables -->
  <link rel="stylesheet" href="https://cdn.datatables.net/2.0.8/css/dataTables.bootstrap5.min.css">
  <!-- Chart.js + datalabels plugin -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1"></script>
  <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0"></script>
  <script>
    window.activeCharts = [];
    const storedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-bs-theme', storedTheme);
    const headStyles = getComputedStyle(document.documentElement);
    Chart.defaults.color = headStyles.getPropertyValue('--bs-body-color');
    Chart.defaults.borderColor = headStyles.getPropertyValue('--bs-border-color-translucent');
  </script>
  <style>
    :root {
      --card-radius: 18px;
    }
    .card { border-radius: var(--card-radius); }
    .shadow-soft { box-shadow: 0 10px 30px rgba(0,0,0,.25); }
    .badge-soft { background: rgba(var(--bs-body-color-rgb), .08); border: 1px solid rgba(var(--bs-body-color-rgb), .15); }
    .table>thead { position: sticky; top: 0; background: rgba(var(--bs-body-bg-rgb), .85); backdrop-filter: blur(6px); }
    .brand { font-weight: 800; letter-spacing: .6px; }
    .nav-link.active { font-weight: 600; }
    .form-floating>.form-control, .form-select { background: rgba(var(--bs-body-color-rgb), .04); }

    .form-control, .form-select {
      color: var(--bs-body-color) !important;
    }
    .form-control::placeholder {
      color: rgba(var(--bs-body-color-rgb), .5);
    }
    .form-floating>label {
      color: rgba(var(--bs-body-color-rgb), .7);
    }

    select.form-select {
      color: var(--bs-body-color) !important;
      background-color: var(--bs-body-bg) !important;
    }
    select.form-select option {
      color: var(--bs-body-color) !important;
      background-color: var(--bs-body-bg) !important;
    }
  </style>
</head>
<body>
<nav class="navbar navbar-expand-lg bg-body-tertiary border-bottom">
  <div class="container">
    <a class="navbar-brand brand" href="{{ url_for('dashboard') }}">
      <i class="bi bi-houses-fill me-2"></i>Kardex Hôtel Social
    </a>
    <div class="ms-auto d-flex gap-2">
      <button id="themeToggle" class="btn btn-outline-secondary" title="Basculer le thème"><i class="bi bi-sun"></i></button>
      <a class="btn btn-outline-info" href="{{ url_for('families_list') }}"><i class="bi bi-people me-1"></i>Familles</a>
      <div class="btn-group">
        <button class="btn btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown">
          <i class="bi bi-download me-1"></i>Export
        </button>
        <ul class="dropdown-menu dropdown-menu-end">
          <li><a class="dropdown-item" href="{{ url_for('export_families_csv') }}">Familles (CSV)</a></li>
          <li><a class="dropdown-item" href="{{ url_for('export_persons_csv') }}">Personnes (CSV)</a></li>
        </ul>
      </div>
      <a class="btn btn-outline-success" href="{{ url_for('backup') }}"><i class="bi bi-save me-1"></i>Sauvegarde</a>
      <a class="btn btn-outline-warning" href="{{ url_for('restore') }}"><i class="bi bi-arrow-counterclockwise me-1"></i>Restaurer</a>
      <a class="btn btn-primary" href="{{ url_for('families_new') }}"><i class="bi bi-plus-lg me-1"></i>Nouvelle famille</a>
    </div>
  </div>
</nav>

<main class="container py-4">
  {{ content|safe }}
</main>

<footer class="border-top py-3">
  <div class="container small text-secondary">
    <span>Local only. SQLite: <code>hotel_social.db</code></span>
  </div>
</footer>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdn.datatables.net/2.0.8/js/dataTables.min.js"></script>
<script src="https://cdn.datatables.net/2.0.8/js/dataTables.bootstrap5.min.js"></script>
<script>
(() => {
  const themeKey = 'theme';
  const applyTheme = t => {
    document.documentElement.setAttribute('data-bs-theme', t);
    const styles = getComputedStyle(document.documentElement);
    Chart.defaults.color = styles.getPropertyValue('--bs-body-color');
    Chart.defaults.borderColor = styles.getPropertyValue('--bs-border-color-translucent');
    window.activeCharts.forEach(c => c.update());
    const icon = document.querySelector('#themeToggle i');
    if (icon) {
      icon.classList.toggle('bi-sun', t === 'dark');
      icon.classList.toggle('bi-moon', t === 'light');
    }
  };
  applyTheme(document.documentElement.getAttribute('data-bs-theme'));
  const btn = document.getElementById('themeToggle');
  if (btn) {
    btn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-bs-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      localStorage.setItem(themeKey, next);
      applyTheme(next);
    });
  }
})();
</script>
</body>
</html>
"""

TPL_DASHBOARD = """
{% if birthdays %}
<div class="alert alert-warning d-flex align-items-center mb-4">
  <i class="bi bi-cake2 me-2"></i>
  <div>
    Anniversaire{% if birthdays|length > 1 %}s{% endif %} aujourd'hui :
    {% for p in birthdays %}
      <strong>{{ p.first_name }} {{ p.last_name }}</strong>
      <span class="text-secondary">({{ p.family.label }})</span>{% if not loop.last %}, {% endif %}
    {% endfor %}
  </div>
</div>
{% endif %}
<div class="row g-4">
  <div class="col-12 col-xl-4">
    <div class="card shadow-soft p-3">
      <div class="d-flex align-items-center">
        <div class="display-6 me-3 text-info"><i class="bi bi-people-fill"></i></div>
        <div>
          <div class="text-secondary text-uppercase small">Total clients</div>
          <div class="h3 m-0">{{ total_clients }}</div>
        </div>
      </div>
    </div>
  </div>
  <div class="col-12 col-xl-4">
    <div class="card shadow-soft p-3">
      <h6 class="mb-3"><i class="bi bi-gender-ambiguous me-2"></i>Répartition par sexe</h6>
      <canvas id="sexChart" height="200"></canvas>
    </div>
  </div>
  <div class="col-12 col-xl-4">
    <div class="card shadow-soft p-3">
      <h6 class="mb-3"><i class="bi bi-activity me-2"></i>Tranches d’âge</h6>
      <canvas id="ageChart" height="200"></canvas>
      <div id="ageLegend" class="mt-2">
        {% for lbl in age_labels %}
        <div class="d-flex align-items-center mb-1">
          <span class="me-1" style="width:12px;height:12px;background-color:{{ age_colors_f[loop.index0] }};display:inline-block;border-radius:2px;"></span>
          <span class="me-2" style="width:12px;height:12px;background-color:{{ age_colors_m[loop.index0] }};display:inline-block;border-radius:2px;"></span>
          <span class="small">{{ lbl }}</span>
        </div>
        {% endfor %}
      </div>
    </div>
  </div>
</div>

<div class="card shadow-soft p-3 mt-4">
  <div class="d-flex align-items-center justify-content-between">
    <h6 class="mb-0"><i class="bi bi-clock-history me-2"></i>Familles récentes</h6>
    <span class="badge rounded-pill badge-soft">{{ families|length }} familles</span>
  </div>
  <div class="table-responsive mt-3" style="max-height: 420px;">
    <table class="table table-hover align-middle table-sm">
      <thead>
        <tr><th>#</th><th>Famille</th><th>Chambre</th><th>Arrivée</th><th>Personnes</th><th></th></tr>
      </thead>
      <tbody>
      {% for f in families %}
        <tr>
          <td class="text-secondary">{{ f.id }}</td>
          <td class="fw-semibold">{{ f.label or "—" }}</td>
          <td>{{ f.room_number or "—" }}</td>
          <td>{{ fmt_date(f.arrival_date) or "—" }}</td>
          <td><span class="badge text-bg-secondary">{{ f.persons.count() }}</span></td>
          <td class="text-end">
            <a class="btn btn-sm btn-outline-info" href="{{ url_for('persons_list', fid=f.id) }}"><i class="bi bi-arrow-right-circle"></i></a>
          </td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
</div>

<script>
Chart.register(ChartDataLabels);

// SEXES (hommes/femmes)
window.activeCharts.push(new Chart(document.getElementById('sexChart'), {
  type: 'doughnut',
  data: {
    labels: {{ sex_labels|tojson }},
    datasets: [{
      data: {{ sex_values|tojson }},
      backgroundColor: [
        '#e83e8c', // Femmes → rose
        '#007bff', // Hommes → bleu
        '#6c757d'  // Autre/NP → gris
      ]
    }]
  },
  options: {
    plugins: {
      legend: { position: 'bottom' },
      datalabels: {
        formatter: (v, ctx) => v || '',
        font: { weight: 600 }
      }
    },
    cutout: '60%'
  }
});

// ÂGES par sexe
const ageColorsF = {{ age_colors_f|tojson }};
const ageColorsM = {{ age_colors_m|tojson }};
window.activeCharts.push(new Chart(document.getElementById('ageChart'), {
  type: 'bar',
  data: {
    labels: {{ age_labels|tojson }},
    datasets: [
      {
        label: 'Femmes',
        data: {{ age_f_values|tojson }},
        backgroundColor: ageColorsF
      },
      {
        label: 'Hommes',
        data: {{ age_m_values|tojson }},
        backgroundColor: ageColorsM
      }
    ]
  },
  options: {
    plugins: {
      legend: { display: false },
      datalabels: { anchor: 'end', align: 'top', formatter: v => v || '' }
    },
    scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
  }
}));
</script>
"""

TPL_FAMILIES = """
<div class="card shadow-soft p-3">
  <div class="d-flex flex-wrap gap-2 justify-content-between align-items-end">
    <h4 class="m-0"><i class="bi bi-people me-2"></i>Familles</h4>
    <form class="row g-2" method="get">
      <div class="col-auto">
        <div class="form-floating">
          <input class="form-control" name="label" id="f1" placeholder="Label" value="{{ label }}">
          <label for="f1">Label</label>
        </div>
      </div>
      <div class="col-auto">
        <div class="form-floating">
          <input class="form-control" name="room" id="f2" placeholder="Chambre" value="{{ room }}">
          <label for="f2">Chambre</label>
        </div>
      </div>
      <div class="col-auto">
        <div class="form-floating">
          <input type="date" class="form-control" name="dmin" id="f3" value="{{ dmin }}">
          <label for="f3">Arrivée min</label>
        </div>
      </div>
      <div class="col-auto">
        <div class="form-floating">
          <input type="date" class="form-control" name="dmax" id="f4" value="{{ dmax }}">
          <label for="f4">Arrivée max</label>
        </div>
      </div>
      <div class="col-auto">
        <button class="btn btn-outline-info"><i class="bi bi-search"></i></button>
        <a class="btn btn-outline-secondary" href="{{ url_for('families_list') }}"><i class="bi bi-x-lg"></i></a>
        <a class="btn btn-primary" href="{{ url_for('families_new') }}"><i class="bi bi-plus-lg me-1"></i>Nouvelle famille</a>
      </div>
    </form>
  </div>

  <div class="table-responsive mt-3" style="max-height: 60vh;">
    <table class="table table-hover table-sm align-middle">
      <thead><tr><th>#</th><th>Label</th><th>Chambre</th><th>Arrivée</th><th>Personnes</th><th class="text-end">Actions</th></tr></thead>
      <tbody>
      {% for f in families %}
        <tr>
          <td class="text-secondary">{{ f.id }}</td>
          <td class="fw-semibold">{{ f.label or "—" }}</td>
          <td>{{ f.room_number or "—" }}</td>
          <td>{{ fmt_date(f.arrival_date) or "—" }}</td>
          <td><span class="badge text-bg-secondary">{{ f.persons.count() }}</span></td>
          <td class="text-end">
            <a class="btn btn-sm btn-outline-info" href="{{ url_for('persons_list', fid=f.id) }}"><i class="bi bi-person-lines-fill"></i></a>
            <a class="btn btn-sm btn-outline-warning" href="{{ url_for('families_edit', fid=f.id) }}"><i class="bi bi-pencil-square"></i></a>
            <form method="post" action="{{ url_for('families_delete', fid=f.id) }}" class="d-inline" onsubmit="return confirm('Supprimer la famille et ses membres ?');">
              <button class="btn btn-sm btn-outline-danger"><i class="bi bi-trash3"></i></button>
            </form>
          </td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
</div>
"""

TPL_FAMILY_FORM = """
<div class="card shadow-soft p-3">
  <h4 class="mb-3">{{ 'Modifier la famille' if family else 'Nouvelle famille' }}</h4>
  <form method="post" class="row g-3">
    <div class="col-md-5">
      <div class="form-floating">
        <input name="label" class="form-control" id="fl1" placeholder="Label" value="{{ family.label if family else '' }}">
        <label for="fl1">Label (ex: Famille Dupont)</label>
      </div>
    </div>
    <div class="col-md-3">
      <div class="form-floating">
        <input name="room_number" class="form-control" id="fl2" placeholder="Chambre" value="{{ family.room_number if family else '' }}">
        <label for="fl2">Chambre</label>
      </div>
    </div>
    <div class="col-md-4">
      <div class="form-floating">
        <input type="text" name="arrival_date" class="form-control" id="fl3" value="{{ fmt_date(family.arrival_date) if family and family.arrival_date else '' }}" placeholder="jj/mm/aaaa" pattern="[0-9]{2}/[0-9]{2}/[0-9]{4}">
        <label for="fl3">Date d'arrivée</label>
      </div>
    </div>
    <div class="col-12 d-flex gap-2">
      <button class="btn btn-primary"><i class="bi bi-check2-circle me-1"></i>Enregistrer</button>
      <a class="btn btn-outline-secondary" href="{{ url_for('families_list') }}">Annuler</a>
    </div>
  </form>
</div>
"""

TPL_PERSONS = """
<div class="d-flex align-items-center justify-content-between mb-3">
  <h4 class="m-0"><i class="bi bi-person-lines-fill me-2"></i>{{ family.label or 'Famille' }} <span class="text-secondary">| Chambre {{ family.room_number or '—' }}</span></h4>
  <div class="d-flex gap-2">
    <a class="btn btn-outline-secondary" href="{{ url_for('families_list') }}"><i class="bi bi-arrow-left"></i> Retour</a>
    <a class="btn btn-primary" href="{{ url_for('persons_new', fid=family.id) }}"><i class="bi bi-plus-lg me-1"></i>Ajouter une personne</a>
  </div>
</div>

<div class="card shadow-soft p-3">
  <div class="table-responsive">
    <table id="personsTable" class="table table-hover table-sm align-middle">
      <thead>
        <tr>
          <th>#</th>
          <th>Nom</th>
          <th>Prénom</th>
          <th>Naissance</th>
          <th>Sexe</th>
          <th>Âge</th>
          <th class="text-end">Actions</th>
          <th>Chambre</th>
          <th>Arrivée</th>
        </tr>
      </thead>
      <tbody>
      {% for p in persons %}
        <tr>
          <td class="text-secondary">{{ p.id }}</td>
          <td class="fw-semibold">{{ p.last_name }}</td>
          <td>{{ p.first_name }}</td>
          <td data-order="{{ p.dob.isoformat() if p.dob else '' }}">{{ fmt_date(p.dob) or "—" }}</td>
          <td>{{ p.sex or "—" }}</td>
          <td>{{ p.age if p.age is not none else "—" }}</td>
          <td class="text-end">
            <a class="btn btn-sm btn-outline-warning" href="{{ url_for('persons_edit', fid=family.id, pid=p.id) }}"><i class="bi bi-pencil"></i></a>
            <form method="post" action="{{ url_for('persons_delete', fid=family.id, pid=p.id) }}" class="d-inline" onsubmit="return confirm('Supprimer cette personne ?');">
              <button class="btn btn-sm btn-outline-danger"><i class="bi bi-trash3"></i></button>
            </form>
          </td>
          <td>{{ family.room_number or "—" }}</td>
          <td data-order="{{ family.arrival_date.isoformat() if family.arrival_date else '' }}">{{ fmt_date(family.arrival_date) or "—" }}</td>
        </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
</div>
<script>
document.addEventListener('DOMContentLoaded', () => {
  new DataTable('#personsTable', {
    columnDefs: [
      { orderable: false, targets: [0,5,6,7,8] },
      { visible: false, targets: [7,8] }
    ],
    language: {
      url: 'https://cdn.datatables.net/plug-ins/2.0.8/i18n/fr-FR.json'
    }
  });
}));
</script>
"""

TPL_PERSON_FORM = """
<div class="card shadow-soft p-3">
  <h4 class="mb-3">{{ 'Modifier' if person else 'Ajouter' }} une personne <span class="text-secondary">dans {{ family.label or 'Famille' }}</span></h4>
  <form method="post" class="row g-3">
    <div class="col-md-3">
      <div class="form-floating">
        <input name="last_name" class="form-control" id="p1" placeholder="Nom" value="{{ person.last_name if person else '' }}" required>
        <label for="p1">Nom</label>
      </div>
    </div>
    <div class="col-md-3">
      <div class="form-floating">
        <input name="first_name" class="form-control" id="p2" placeholder="Prénom" value="{{ person.first_name if person else '' }}" required>
        <label for="p2">Prénom</label>
      </div>
    </div>
    <div class="col-md-3">
      <div class="form-floating">
        <input type="text" name="dob" class="form-control" id="p3" value="{{ fmt_date(person.dob) if person and person.dob else '' }}" placeholder="jj/mm/aaaa" pattern="[0-9]{2}/[0-9]{2}/[0-9]{4}">
        <label for="p3">Date de naissance</label>
      </div>
    </div>
    <div class="col-md-3">
      <div class="form-floating">
        <select name="sex" class="form-select" id="p4">
          {% for s in sex_choices %}
            <option value="{{ s }}" {% if person and person.sex==s %}selected{% endif %}>{{ s }}</option>
          {% endfor %}
        </select>
        <label for="p4">Sexe</label>
      </div>
    </div>
    <div class="col-12 d-flex gap-2">
      <button class="btn btn-primary"><i class="bi bi-check2-circle me-1"></i>Enregistrer</button>
      <a class="btn btn-outline-secondary" href="{{ url_for('persons_list', fid=family.id) }}">Annuler</a>
    </div>
  </form>
</div>
"""

TPL_RESTORE = """
<div class="card shadow-soft p-3 col-md-6 mx-auto">
  <h4 class="mb-3">Restauration</h4>
  <div class="alert alert-warning">Cette opération effacera toutes les données existantes.</div>
  <form method="post" enctype="multipart/form-data" onsubmit="return confirm('Cette action écrasera les données actuelles. Continuer ?');">
    <div class="mb-3">
      <input type="file" name="file" accept="application/json" class="form-control" required>
    </div>
    <button class="btn btn-danger" name="confirm" value="yes"><i class="bi bi-arrow-counterclockwise me-1"></i>Restaurer</button>
    <a class="btn btn-outline-secondary" href="{{ url_for('dashboard') }}">Annuler</a>
  </form>
</div>
"""

# ============================
# Init DB
# ============================
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
