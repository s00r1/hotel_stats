# app.py  —  Hôtel Social • Kardex + Stats (Flask + SQLite + Chart.js)
# Python 3.12 x64 recommandé

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from io import StringIO
import csv
import json

from flask import Flask, request, redirect, url_for, render_template, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import OperationalError

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

@app.context_processor
def inject_globals():
    return {
        "fmt_date": fmt_date,
        "sex_choices": SEX_CHOICES,
        "theme": request.cookies.get("theme", "dark"),
    }

@app.route("/theme/<mode>")
def set_theme(mode):
    if mode not in ("light", "dark"):
        mode = "dark"
    resp = redirect(request.referrer or url_for("dashboard"))
    resp.set_cookie("theme", mode, max_age=60 * 60 * 24 * 365)
    return resp

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

    return render_template(
        "dashboard.html",
        total_clients=len(persons),
        sex_labels=list(sex_counts.keys()),
        sex_values=list(sex_counts.values()),
        age_labels=list(age_counts.keys()),
        age_f_values=[age_counts[k]["F"] for k in age_counts.keys()],
        age_m_values=[age_counts[k]["M"] for k in age_counts.keys()],
        age_colors_f=AGE_COLORS_F,
        age_colors_m=AGE_COLORS_M,
        families=families,
        birthdays=birthdays,
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
    return render_template(
        "families.html",
        families=families,
        room=room,
        label=label,
        dmin=request.args.get("dmin") or "",
        dmax=request.args.get("dmax") or "",
    )

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
    return render_template("family_form.html", family=None)

@app.route("/families/<int:fid>/edit", methods=["GET","POST"])
def families_edit(fid):
    fam = Family.query.get_or_404(fid)
    if request.method == "POST":
        fam.label = request.form.get("label") or None
        fam.room_number = request.form.get("room_number") or None
        fam.arrival_date = parse_date(request.form.get("arrival_date"))
        db.session.commit()
        return redirect(url_for("families_list"))
    return render_template("family_form.html", family=fam)

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
    return render_template("persons.html", family=fam, persons=rows)

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
    return render_template("person_form.html", family=fam, person=None)

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
    return render_template("person_form.html", family=fam, person=p)

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
        try:
            data = json.load(file.stream)
        except json.JSONDecodeError:
            return redirect(url_for("restore"))
        Person.query.delete()
        Family.query.delete()
        db.session.commit()
        try:
            db.session.execute(db.text("DELETE FROM sqlite_sequence WHERE name IN ('family','person')"))
            db.session.commit()
        except OperationalError:
            db.session.rollback()
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
    return render_template("restore.html")

# ============================
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
