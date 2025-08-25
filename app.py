# app.py  —  Hôtel Social • Kardex + Stats (Flask + SQLite + Chart.js)
# Python 3.12 x64 recommandé

from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from io import StringIO
import csv
import json

from flask import Flask, request, redirect, url_for, render_template, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, text
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
    room_number2 = db.Column(db.String(20), index=True)
    arrival_date = db.Column(db.Date, index=True)
    departure_date = db.Column(db.Date, index=True)
    phone1 = db.Column(db.String(20), index=True)
    phone2 = db.Column(db.String(20), index=True)

    persons = db.relationship("Person", backref="family", cascade="all,delete", lazy="dynamic")

class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    family_id = db.Column(db.Integer, db.ForeignKey("family.id"), index=True, nullable=False)
    first_name = db.Column(db.String(80), index=True, nullable=False)
    last_name  = db.Column(db.String(80), index=True, nullable=False)
    dob = db.Column(db.Date, index=True)
    sex = db.Column(db.String(12), index=True)            # "F","M","Autre/NP"
    phone = db.Column(db.String(20), index=True)

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

AGE_LABELS = [b[0] for b in AGE_BUCKETS]

# Couleurs des tranches d'âge (Femmes / Hommes)
AGE_COLORS_F = ['#8bd0db', '#8fe4cb', '#93d3a2', '#ffe083', '#febe89', '#ed9aa2', '#b7a0e0', '#999c9f']
AGE_COLORS_M = ['#128193', '#19a078', '#208537', '#cc9a05', '#ca6410', '#b02a37', '#58349a', '#292e33']

SEX_CHOICES = ["F", "M", "Autre/NP"]

def clean_field(v: str | None) -> str | None:
    """Retourne None pour les champs vides ou contenant la chaîne 'None'."""
    if not v:
        return None
    v = v.strip()
    return None if v.lower() == "none" or v == "" else v

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

def age_days(dob: date | None, ref: date | None = None) -> int:
    if not dob:
        return -1
    ref = ref or date.today()
    return (ref - dob).days

def age_text(dob: date | None, ref: date | None = None) -> str:
    if not dob:
        return ""
    ref = ref or date.today()
    rd = relativedelta(ref, dob)
    if rd.years >= 1:
        return f"{rd.years} an{'s' if rd.years > 1 else ''}"
    if rd.months >= 1:
        return f"{rd.months} mois"
    return f"{rd.days} jour{'s' if rd.days > 1 else ''}"

def bucket_for_age(a: int | None):
    if a is None:
        return None
    for label, lo, hi in AGE_BUCKETS:
        if lo <= a <= hi:
            return label
    return None

def rooms_text(f: "Family") -> str:
    return " & ".join(r for r in [clean_field(f.room_number), clean_field(f.room_number2)] if r)

def phones_text(f: "Family") -> str:
    return " / ".join(p for p in [clean_field(f.phone1), clean_field(f.phone2)] if p)


def age_color(p: "Person", age: int | None = None) -> str:
    a = age if age is not None else age_years(p.dob)
    if a is None:
        return ""
    label = bucket_for_age(a)
    if not label:
        return ""
    idx = AGE_LABELS.index(label)
    colors = AGE_COLORS_M if p.sex == "M" else AGE_COLORS_F
    return colors[idx]

@app.context_processor
def inject_globals():
    return {
        "fmt_date": fmt_date,
        "sex_choices": SEX_CHOICES,
        "theme": request.cookies.get("theme", "dark"),
        "age_years": age_years,
        "age_text": age_text,
        "rooms_text": rooms_text,
        "phones_text": phones_text,
        "age_color": age_color,
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
    persons = Person.query.join(Family).filter(Family.departure_date.is_(None)).all()

    # Répartition sexes
    sex_counts = {k: 0 for k in SEX_CHOICES}
    # Tranches d'âge par sexe
    age_counts = {b[0]: {"F": 0, "M": 0} for b in AGE_BUCKETS}
    # Comptages adultes/enfants détaillés
    adult_female_count = adult_male_count = 0
    girl_count = boy_count = 0

    for p in persons:
        s = p.sex if p.sex in sex_counts else "Autre/NP"
        sex_counts[s] += 1
        a = age_years(p.dob, today)
        p._age = a
        b = bucket_for_age(a)
        if b and s in ("F", "M"):
            age_counts[b][s] += 1
        if a is not None and s in ("F", "M"):
            if a < 18:
                if s == "F":
                    girl_count += 1
                else:
                    boy_count += 1
            else:
                if s == "F":
                    adult_female_count += 1
                else:
                    adult_male_count += 1

    # Listes des 5 adultes/enfants les plus âgés et les plus jeunes
    adults = [p for p in persons if p._age is not None and p._age >= 18]
    children = [p for p in persons if p._age is not None and p._age < 18]
    oldest_adults = sorted(adults, key=lambda p: p._age, reverse=True)[:5]
    youngest_adults = sorted(adults, key=lambda p: p._age)[:5]
    oldest_children = sorted(children, key=lambda p: p._age, reverse=True)[:5]
    youngest_children = sorted(children, key=lambda p: p._age)[:5]

    # Anniversaires (semaine/mois passés et à venir)
    birthdays_today: list[dict] = []
    birthdays_week_ahead: list[dict] = []
    birthdays_week_past: list[dict] = []
    birthdays_month_ahead: list[dict] = []
    birthdays_month_past: list[dict] = []

    week_ahead_end = today + relativedelta(weeks=1)
    month_ahead_end = today + relativedelta(months=1)
    week_past_start = today - relativedelta(weeks=1)
    month_past_start = today - relativedelta(months=1)

    for p in persons:
        if not p.dob:
            continue
        dob_this_year = p.dob.replace(year=today.year)
        if dob_this_year == today:
            birthdays_today.append({
                "person": p,
                "age": age_years(p.dob, today),
            })
            continue

        next_bd = dob_this_year if dob_this_year > today else dob_this_year.replace(year=today.year + 1)
        prev_bd = dob_this_year if dob_this_year < today else dob_this_year.replace(year=today.year - 1)

        if today < next_bd <= week_ahead_end:
            birthdays_week_ahead.append({
                "person": p,
                "date": next_bd,
                "age": age_years(p.dob, next_bd),
            })
        elif today < next_bd <= month_ahead_end:
            birthdays_month_ahead.append({
                "person": p,
                "date": next_bd,
                "age": age_years(p.dob, next_bd),
            })

        if week_past_start <= prev_bd < today:
            birthdays_week_past.append({
                "person": p,
                "date": prev_bd,
                "age": age_years(p.dob, prev_bd),
            })
        elif month_past_start <= prev_bd < today:
            birthdays_month_past.append({
                "person": p,
                "date": prev_bd,
                "age": age_years(p.dob, prev_bd),
            })

    birthdays_week_ahead.sort(key=lambda b: b["date"])
    birthdays_month_ahead.sort(key=lambda b: b["date"])
    birthdays_week_past.sort(key=lambda b: b["date"], reverse=True)
    birthdays_month_past.sort(key=lambda b: b["date"], reverse=True)

    # Familles récentes et ancienneté
    families = Family.query.filter(Family.departure_date.is_(None)).order_by(
        Family.arrival_date.desc().nullslast(), Family.id.desc()
    ).all()
    recent_families = families[:5]
    old_families = (
        Family.query.filter(Family.departure_date.is_(None))
        .order_by(Family.arrival_date.asc().nullslast(), Family.id.asc())
        .limit(5)
        .all()
    )

    def days_since(arrival: date | None) -> int:
        return (today - arrival).days if arrival else 0

    def tenure_text(arrival: date | None) -> str:
        if not arrival:
            return "(0 jour)"
        rd = relativedelta(today, arrival)
        return f"({rd.years} ans et {rd.months} mois et {rd.days} jours)"

    old_labels = [f.label or f"Famille {f.id}" for f in old_families]
    old_values = [days_since(f.arrival_date) for f in old_families]
    old_tenures = [tenure_text(f.arrival_date) for f in old_families]
    recent_labels = [f.label or f"Famille {f.id}" for f in recent_families]
    recent_values = [days_since(f.arrival_date) for f in recent_families]
    recent_tenures = [tenure_text(f.arrival_date) for f in recent_families]

    # Alertes : sur-occupation, femmes isolées, bébés < 1 an
    overcrowded: list[Family] = []
    isolated_women: list[Person] = []
    baby_persons: list[Person] = []

    for f in families:
        persons_list = f.persons.all()

        rooms = [r for r in (f.room_number, f.room_number2) if r]
        capacity = 0
        for r in rooms:
            capacity += 8 if r in ("53", "54") else 3

        if rooms and len(persons_list) > capacity:
            overcrowded.append(f)

        adult_females: list[Person] = []
        has_adult_male = False
        for p in persons_list:
            a = age_years(p.dob, today)
            if a is None:
                continue
            if a >= 18:
                if p.sex == "M":
                    has_adult_male = True
                elif p.sex == "F":
                    adult_females.append(p)
            if a < 1:
                baby_persons.append(p)
        if adult_females and not has_adult_male:
            isolated_women.extend(adult_females)

    return render_template(
        "dashboard.html",
        total_clients=len(persons),
        sex_labels=list(sex_counts.keys()),
        sex_values=list(sex_counts.values()),
        sex_child_values=[girl_count, boy_count, 0],
        age_labels=list(age_counts.keys()),
        age_f_values=[age_counts[k]["F"] for k in age_counts.keys()],
        age_m_values=[age_counts[k]["M"] for k in age_counts.keys()],
        age_colors_f=AGE_COLORS_F,
        age_colors_m=AGE_COLORS_M,
        old_labels=old_labels,
        old_values=old_values,
        old_tenures=old_tenures,
        recent_labels=recent_labels,
        recent_values=recent_values,
        recent_tenures=recent_tenures,
        oldest_adults=oldest_adults,
        youngest_adults=youngest_adults,
        oldest_children=oldest_children,
        youngest_children=youngest_children,
        families=families,
        birthdays_today=birthdays_today,
        birthdays_week_ahead=birthdays_week_ahead,
        birthdays_week_past=birthdays_week_past,
        birthdays_month_ahead=birthdays_month_ahead,
        birthdays_month_past=birthdays_month_past,
        adult_female_count=adult_female_count,
        adult_male_count=adult_male_count,
        girl_count=girl_count,
        boy_count=boy_count,
        overcrowded_families=overcrowded,
        isolated_women=isolated_women,
        baby_persons=baby_persons,
        Person=Person,
    )

# ----- Familles -----

@app.route("/families")
def families_list():
    q = Family.query.filter(Family.departure_date.is_(None))
    room = (request.args.get("room") or "").strip()
    label = (request.args.get("label") or "").strip()
    dmin = parse_date(request.args.get("dmin"))
    dmax = parse_date(request.args.get("dmax"))

    if room:
        q = q.filter(or_(Family.room_number.like(f"%{room}%"), Family.room_number2.like(f"%{room}%")))
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
        Person=Person,
    )

@app.route("/families/new", methods=["GET","POST"])
def families_new():
    if request.method == "POST":
        f = Family(
            label=clean_field(request.form.get("label")),
            room_number=clean_field(request.form.get("room_number")),
            room_number2=clean_field(request.form.get("room_number2")),
            arrival_date=parse_date(request.form.get("arrival_date")),
            phone1=clean_field(request.form.get("phone1")),
            phone2=clean_field(request.form.get("phone2")),
        )
        db.session.add(f)
        db.session.commit()
        return redirect(url_for("families_list"))
    return render_template("family_form.html", family=None)

@app.route("/families/<int:fid>/edit", methods=["GET","POST"])
def families_edit(fid):
    fam = Family.query.get_or_404(fid)
    if request.method == "POST":
        fam.label = clean_field(request.form.get("label"))
        fam.room_number = clean_field(request.form.get("room_number"))
        fam.room_number2 = clean_field(request.form.get("room_number2"))
        fam.arrival_date = parse_date(request.form.get("arrival_date"))
        fam.phone1 = clean_field(request.form.get("phone1"))
        fam.phone2 = clean_field(request.form.get("phone2"))
        db.session.commit()
        return redirect(url_for("families_list"))
    return render_template("family_form.html", family=fam)

@app.route("/families/<int:fid>/depart", methods=["GET","POST"])
def families_depart(fid):
    fam = Family.query.get_or_404(fid)
    if request.method == "POST":
        fam.departure_date = parse_date(request.form.get("departure_date"))
        db.session.commit()
        return redirect(url_for("families_list"))
    return render_template("family_depart.html", family=fam)

@app.route("/families/<int:fid>/delete", methods=["POST"])
def families_delete(fid):
    fam = Family.query.get_or_404(fid)
    db.session.delete(fam)
    db.session.commit()
    return redirect(url_for("families_list"))

# ----- Personnes -----

@app.route("/persons/<int:fid>")
def persons_list(fid):
    fam = Family.query.filter_by(id=fid).filter(Family.departure_date.is_(None)).first_or_404()
    today = date.today()
    rows = []
    for p in fam.persons.order_by(Person.id.asc()).all():
        rows.append({
            "id": p.id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "dob": p.dob,
            "sex": p.sex,
            "phone": p.phone,
            "age": age_years(p.dob, today),
            "age_text": age_text(p.dob, today),
            "age_days": age_days(p.dob, today)
        })
    return render_template("persons.html", family=fam, persons=rows)

@app.route("/persons/<int:fid>/new", methods=["GET","POST"])
def persons_new(fid):
    fam = Family.query.filter_by(id=fid).filter(Family.departure_date.is_(None)).first_or_404()
    if request.method == "POST":
        p = Person(
            family_id=fid,
            first_name=request.form.get("first_name").strip(),
            last_name=request.form.get("last_name").strip(),
            dob=parse_date(request.form.get("dob")),
            sex=request.form.get("sex") or "Autre/NP",
            phone=clean_field(request.form.get("phone")),
        )
        db.session.add(p)
        db.session.commit()
        return redirect(url_for("persons_list", fid=fid))
    return render_template("person_form.html", family=fam, person=None)

@app.route("/persons/<int:fid>/<int:pid>/edit", methods=["GET","POST"])
def persons_edit(fid, pid):
    fam = Family.query.filter_by(id=fid).filter(Family.departure_date.is_(None)).first_or_404()
    p = Person.query.join(Family).filter(Person.id == pid, Family.departure_date.is_(None)).first_or_404()
    if request.method == "POST":
        p.first_name = request.form.get("first_name").strip()
        p.last_name  = request.form.get("last_name").strip()
        p.dob = parse_date(request.form.get("dob"))
        p.sex = request.form.get("sex") or "Autre/NP"
        p.phone = clean_field(request.form.get("phone"))
        db.session.commit()
        return redirect(url_for("persons_list", fid=fid))
    return render_template("person_form.html", family=fam, person=p)

@app.route("/persons/<int:fid>/<int:pid>/delete", methods=["POST"])
def persons_delete(fid, pid):
    p = Person.query.join(Family).filter(Person.id == pid, Family.departure_date.is_(None)).first_or_404()
    db.session.delete(p)
    db.session.commit()
    return redirect(url_for("persons_list", fid=fid))

# ----- Résidents -----

@app.route("/residents")
def residents_list():
    today = date.today()
    rows = []
    for p in Person.query.join(Family).filter(Family.departure_date.is_(None)).all():
        fam = p.family
        rows.append({
            "id": p.id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "sex": p.sex,
            "age": age_years(p.dob, today),
            "age_text": age_text(p.dob, today),
            "age_days": age_days(p.dob, today),
            "family_label": fam.label,
            "room_number": rooms_text(fam),
            "arrival_date": fam.arrival_date,
            "phone": p.phone,
        })
    return render_template("residents.html", persons=rows)

# ----- Recherches -----

@app.route("/search")
def search():
    fam_label = (request.args.get("fam_label") or "").strip()
    fam_room = (request.args.get("fam_room") or "").strip()
    fam_arrival = parse_date(request.args.get("fam_arrival"))
    fam_dmin = parse_date(request.args.get("fam_dmin"))
    fam_dmax = parse_date(request.args.get("fam_dmax"))

    p_last = (request.args.get("p_last") or "").strip()
    p_first = (request.args.get("p_first") or "").strip()
    p_dob = parse_date(request.args.get("p_dob"))
    p_arrival = parse_date(request.args.get("p_arrival"))
    p_room = (request.args.get("p_room") or "").strip()
    p_phone = (request.args.get("p_phone") or "").strip()

    families = []
    if any([fam_label, fam_room, fam_arrival, fam_dmin, fam_dmax]):
        qf = Family.query.filter(Family.departure_date.is_(None))
        if fam_label:
            qf = qf.filter(Family.label.like(f"%{fam_label}%"))
        if fam_room:
            qf = qf.filter(or_(Family.room_number.like(f"%{fam_room}%"), Family.room_number2.like(f"%{fam_room}%")))
        if fam_arrival:
            qf = qf.filter(Family.arrival_date == fam_arrival)
        if fam_dmin:
            qf = qf.filter(Family.arrival_date >= fam_dmin)
        if fam_dmax:
            qf = qf.filter(Family.arrival_date <= fam_dmax)
        families = qf.order_by(Family.arrival_date.desc().nullslast()).all()

    persons = []
    if any([p_last, p_first, p_dob, p_arrival, p_room, p_phone]):
        qp = Person.query.join(Family).filter(Family.departure_date.is_(None))
        if p_last:
            qp = qp.filter(Person.last_name.like(f"%{p_last}%"))
        if p_first:
            qp = qp.filter(Person.first_name.like(f"%{p_first}%"))
        if p_dob:
            qp = qp.filter(Person.dob == p_dob)
        if p_arrival:
            qp = qp.filter(Family.arrival_date == p_arrival)
        if p_room:
            qp = qp.filter(or_(Family.room_number.like(f"%{p_room}%"), Family.room_number2.like(f"%{p_room}%")))
        if p_phone:
            qp = qp.filter(Person.phone.like(f"%{p_phone}%"))
        today = date.today()
        persons = [
            {
                "id": p.id,
                "first_name": p.first_name,
                "last_name": p.last_name,
                "age": age_years(p.dob, today),
                "age_text": age_text(p.dob, today),
                "age_days": age_days(p.dob, today),
                "room_number": rooms_text(p.family),
                "arrival_date": p.family.arrival_date,
                "phone": p.phone,
            }
            for p in qp.all()
        ]

    return render_template(
        "search.html",
        families=families,
        persons=persons,
        fam_label=fam_label,
        fam_room=fam_room,
        fam_arrival=request.args.get("fam_arrival") or "",
        fam_dmin=request.args.get("fam_dmin") or "",
        fam_dmax=request.args.get("fam_dmax") or "",
        p_last=p_last,
        p_first=p_first,
        p_dob=request.args.get("p_dob") or "",
        p_arrival=request.args.get("p_arrival") or "",
        p_room=p_room,
        p_phone=p_phone,
    )

@app.route("/archive")
def archive():
    fam_label = (request.args.get("fam_label") or "").strip()
    fam_room = (request.args.get("fam_room") or "").strip()
    fam_arrival = parse_date(request.args.get("fam_arrival"))
    fam_dmin = parse_date(request.args.get("fam_dmin"))
    fam_dmax = parse_date(request.args.get("fam_dmax"))

    p_last = (request.args.get("p_last") or "").strip()
    p_first = (request.args.get("p_first") or "").strip()
    p_dob = parse_date(request.args.get("p_dob"))
    p_arrival = parse_date(request.args.get("p_arrival"))
    p_room = (request.args.get("p_room") or "").strip()
    p_phone = (request.args.get("p_phone") or "").strip()

    families = []
    if any([fam_label, fam_room, fam_arrival, fam_dmin, fam_dmax]):
        qf = Family.query.filter(Family.departure_date.isnot(None))
        if fam_label:
            qf = qf.filter(Family.label.like(f"%{fam_label}%"))
        if fam_room:
            qf = qf.filter(or_(Family.room_number.like(f"%{fam_room}%"), Family.room_number2.like(f"%{fam_room}%")))
        if fam_arrival:
            qf = qf.filter(Family.arrival_date == fam_arrival)
        if fam_dmin:
            qf = qf.filter(Family.arrival_date >= fam_dmin)
        if fam_dmax:
            qf = qf.filter(Family.arrival_date <= fam_dmax)
        families = qf.order_by(Family.arrival_date.desc().nullslast()).all()

    persons = []
    if any([p_last, p_first, p_dob, p_arrival, p_room, p_phone]):
        qp = Person.query.join(Family).filter(Family.departure_date.isnot(None))
        if p_last:
            qp = qp.filter(Person.last_name.like(f"%{p_last}%"))
        if p_first:
            qp = qp.filter(Person.first_name.like(f"%{p_first}%"))
        if p_dob:
            qp = qp.filter(Person.dob == p_dob)
        if p_arrival:
            qp = qp.filter(Family.arrival_date == p_arrival)
        if p_room:
            qp = qp.filter(or_(Family.room_number.like(f"%{p_room}%"), Family.room_number2.like(f"%{p_room}%")))
        if p_phone:
            qp = qp.filter(Person.phone.like(f"%{p_phone}%"))
        today = date.today()
        persons = [
            {
                "id": p.id,
                "first_name": p.first_name,
                "last_name": p.last_name,
                "age": age_years(p.dob, today),
                "age_text": age_text(p.dob, today),
                "age_days": age_days(p.dob, today),
                "room_number": rooms_text(p.family),
                "arrival_date": p.family.arrival_date,
                "phone": p.phone,
            }
            for p in qp.all()
        ]

    return render_template(
        "archive.html",
        families=families,
        persons=persons,
        fam_label=fam_label,
        fam_room=fam_room,
        fam_arrival=request.args.get("fam_arrival") or "",
        fam_dmin=request.args.get("fam_dmin") or "",
        fam_dmax=request.args.get("fam_dmax") or "",
        p_last=p_last,
        p_first=p_first,
        p_dob=request.args.get("p_dob") or "",
        p_arrival=request.args.get("p_arrival") or "",
        p_room=p_room,
        p_phone=p_phone,
    )

# ----- Export CSV -----

@app.route("/export/families.csv")
def export_families_csv():
    out = StringIO()
    w = csv.writer(out, dialect="excel")
    w.writerow(["id","label","room_number","arrival_date","num_persons"])
    for f in Family.query.filter(Family.departure_date.is_(None)).order_by(Family.id.asc()).all():
        w.writerow([f.id, f.label or "", rooms_text(f) or "", f.arrival_date or "", f.persons.count()])
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
    for p in Person.query.join(Family).filter(Family.departure_date.is_(None)).order_by(Person.id.asc()).all():
        fam = p.family
        w.writerow([p.id, fam.id, fam.label or "", rooms_text(fam) or "", p.last_name, p.first_name, p.dob or "", p.sex or "", age_years(p.dob, today) or ""])
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
                "room_number2": f.room_number2,
                "arrival_date": f.arrival_date.isoformat() if f.arrival_date else None,
                "departure_date": f.departure_date.isoformat() if f.departure_date else None,
                "phone1": f.phone1,
                "phone2": f.phone2,
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
                "phone": p.phone,
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
                room_number2=f.get("room_number2"),
                arrival_date=parse_date(f.get("arrival_date")),
                departure_date=parse_date(f.get("departure_date")),
                phone1=f.get("phone1"),
                phone2=f.get("phone2"),
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
                phone=p.get("phone"),
            )
            db.session.add(pers)
        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("restore.html")

# ============================
with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE family ADD COLUMN room_number2 VARCHAR(20)"))
        db.session.commit()
    except OperationalError:
        db.session.rollback()
    try:
        db.session.execute(text("ALTER TABLE family ADD COLUMN phone1 VARCHAR(20)"))
        db.session.commit()
    except OperationalError:
        db.session.rollback()
    try:
        db.session.execute(text("ALTER TABLE family ADD COLUMN phone2 VARCHAR(20)"))
        db.session.commit()
    except OperationalError:
        db.session.rollback()
    try:
        db.session.execute(text("ALTER TABLE person ADD COLUMN phone VARCHAR(20)"))
        db.session.commit()
    except OperationalError:
        db.session.rollback()
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
