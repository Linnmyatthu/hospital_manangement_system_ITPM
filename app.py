from flask import (
    Flask,
    render_template,
    send_from_directory,
    request,
    redirect,
    url_for,
    jsonify,
)
import os
import sqlite3
from datetime import datetime, timedelta, date
import random

app = Flask(__name__)
app.config["SECRET_KEY"] = "123"

try:
    os.makedirs(app.instance_path, exist_ok=True)
except OSError:
    pass

DATABASE_PATH = os.path.join(app.instance_path, "hospital.db")

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def log_activity(action_type, table_name, record_id, description, timestamp=None):
    conn = get_db_connection()
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    conn.execute(
        "INSERT INTO activity_log (action_type, table_name, record_id, description, timestamp) VALUES (?, ?, ?, ?, ?)",
        (action_type, table_name, record_id, description, timestamp)
    )
    conn.commit()
    conn.close()

def migrate_tables(cursor):
    cursor.execute("PRAGMA table_info(doctors)")
    doc_cols = [col[1] for col in cursor.fetchall()]
    for col, typ in [('team_id', 'INTEGER'), ('ward_id', 'INTEGER'), ('pager', 'TEXT'), ('email', 'TEXT')]:
        if col not in doc_cols:
            cursor.execute(f"ALTER TABLE doctors ADD COLUMN {col} {typ}")

    cursor.execute("PRAGMA table_info(patients)")
    pat_cols = [col[1] for col in cursor.fetchall()]
    if 'discharged_at' not in pat_cols:
        cursor.execute("ALTER TABLE patients ADD COLUMN discharged_at TIMESTAMP")

    cursor.execute("PRAGMA table_info(wards)")
    ward_cols = [col[1] for col in cursor.fetchall()]
    if 'gender_type' not in ward_cols:
        cursor.execute("ALTER TABLE wards ADD COLUMN gender_type TEXT DEFAULT 'Mixed'")

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    create_tables(cursor)
    migrate_tables(cursor)

    yesterday = datetime.now() - timedelta(days=1)
    base_time = yesterday.replace(hour=13, minute=0, second=0)
    sample_times = [
        (base_time - timedelta(minutes=10)).isoformat(),
        (base_time - timedelta(minutes=25)).isoformat(),
        (base_time - timedelta(minutes=40)).isoformat(),
        (base_time - timedelta(hours=1, minutes=0)).isoformat(),
        (base_time - timedelta(hours=1, minutes=15)).isoformat(),
        (base_time - timedelta(hours=1, minutes=30)).isoformat(),
    ]
    t1, t2, t3, t4, t5, t6 = sample_times

    if cursor.execute("SELECT COUNT(*) FROM wards").fetchone()[0] == 0:
        cursor.executescript("""
            INSERT INTO wards (name, code, type, capacity, occupied, lead_consultant, status, gender_type) VALUES
            ('Acute Medical Unit (AMU)', 'AMU', 'General', 32, 29, 'Dr. Morgan', 'active', 'Mixed'),
            ('Coronary Care Unit (CCU)', 'CCU', 'Cardiology', 14, 12, 'Dr. Khan', 'active', 'Mixed'),
            ('Intensive Care Unit (ICU)', 'ICU', 'Critical', 10, 9, 'Dr. J. Khan', 'active', 'Mixed'),
            ('Respiratory Ward (RESP)', 'RESP', 'Respiratory', 26, 19, 'Dr. Taylor', 'active', 'Mixed'),
            ('Short Stay Surgical (SSS)', 'SSS', 'Surgical', 24, 17, 'Dr. Chen', 'active', 'Mixed'),
            ('Paediatrics (PAED)', 'PAED', 'Paediatrics', 20, 14, 'Dr. Williams', 'active', 'Mixed'),
            ('Stroke Unit (STK)', 'STK', 'Neurology', 18, 10, 'Dr. Ahmed', 'active', 'Mixed'),
            ('Orthopaedic Ward (ORTH)', 'ORTH', 'Orthopaedics', 22, 15, 'Dr. N. Taylor', 'active', 'Mixed'),
            ('Ward A', 'WDA', 'General', 20, 12, 'Dr. Smith', 'active', 'Male'),
            ('Ward B', 'WDB', 'General', 20, 14, 'Dr. Jones', 'active', 'Female'),
            ('Ward C', 'WDC', 'General', 25, 18, 'Dr. Brown', 'active', 'Mixed');
        """)

    if cursor.execute("SELECT COUNT(*) FROM teams").fetchone()[0] == 0:
        cursor.executescript("""
            INSERT INTO teams (name, specialty, members, lead) VALUES
            ('Acute Medical Team A', 'Acute Medicine', 5, 'Dr. Riley Morgan'),
            ('Cardiology Team', 'Cardiology', 4, 'Dr. Noor Khan'),
            ('Respiratory Team', 'Respiratory', 3, 'Dr. Daniel Brooks'),
            ('ICU Team', 'Critical Care', 6, 'Dr. J. Khan'),
            ('Surgical Team', 'Surgery', 4, 'Dr. Laura Chen'),
            ('Paediatrics Team', 'Paediatrics', 4, 'Dr. S. Williams');
        """)

    if cursor.execute("SELECT COUNT(*) FROM doctors").fetchone()[0] == 0:
        first_names = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda', 'William', 'Elizabeth',
                       'David', 'Susan', 'Richard', 'Jessica', 'Joseph', 'Sarah', 'Thomas', 'Karen', 'Charles', 'Nancy']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
                      'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin']
        specialties = ['Acute Medicine', 'Cardiology', 'Respiratory', 'ICU', 'Surgery', 'Paediatrics', 'Neurology', 'Orthopaedics']
        grades = ['Consultant', 'ST7 Registrar', 'ST5 Registrar', 'ST3 Registrar', 'FY2', 'FY1', 'CT1', 'CT2']

        doctors = []
        for i in range(1, 63):
            name = f"Dr. {random.choice(first_names)} {random.choice(last_names)}"
            specialty = random.choice(specialties)
            grade = random.choice(grades)
            on_duty = 1
            team_id = random.randint(1, 6)
            ward_id = random.randint(1, 11)
            pager = f"{random.randint(1000, 9999)}"
            email = f"{name.lower().replace('dr. ', '').replace(' ', '.')}@hospital.nhs.uk"
            doctors.append((name, specialty, grade, on_duty, team_id, ward_id, pager, email))

        cursor.executemany("""
            INSERT INTO doctors (name, specialty, grade, on_duty, team_id, ward_id, pager, email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, doctors)

    if cursor.execute("SELECT COUNT(*) FROM patients").fetchone()[0] == 0:
        patients_data = [
            ('Sarah Johnson', '1970-01-01', 54, 'Female', 'NHS001', '0123456789', '123 Main St',
             t1, 1, 'Bay 4', 1, 'Sepsis', '', 'Active', None),
            ('Emily Brown', '1985-02-02', 39, 'Female', 'NHS002', '0123456780', '456 Oak Ave',
             (yesterday - timedelta(days=2)).isoformat(), 1, 'Bay 1', 1, 'UTI', '', 'Discharged', t2),
            ('James Carter', '1956-03-03', 68, 'Male', 'NHS003', '0123456781', '789 Pine Rd',
             t3, 1, 'Bay 2', 1, 'Pneumonia', '', 'Active', None),
            ('Mohammed Ali', '1975-04-04', 49, 'Male', 'NHS004', '0123456782', '321 Elm St',
             (yesterday - timedelta(hours=5)).isoformat(), 1, 'Side-room 1', 1, 'Chest pain', '', 'Active', None),
            ('Jennifer Lewis', '1995-05-05', 29, 'Female', 'NHS005', '0123456783', '654 Cedar Ln',
             (yesterday - timedelta(days=2)).isoformat(), 5, 'Bay 2', 1, 'Appendicitis', '', 'Discharged', t4),
            ('Thomas Wright', '1979-06-06', 45, 'Male', 'NHS006', '0123456784', '987 Birch Dr',
             t5, 2, 'Bay 1', 4, 'Acute MI', '', 'Active', None),
            ('Patricia White', '1958-07-07', 66, 'Female', 'NHS007', '0123456785', '147 Spruce Ct',
             (yesterday - timedelta(days=7)).isoformat(), 1, 'Bay 1', 1, 'COPD', '', 'Discharged', (yesterday - timedelta(hours=2)).isoformat()),
            ('David Wilson', '1980-08-08', 44, 'Male', 'NHS008', '0123456786', '258 Willow Way',
             t6, 1, 'Bay 5', 1, 'Observation', '', 'Active', None),
        ]
        cursor.executemany("""
            INSERT INTO patients 
            (name, dob, age, gender, nhs_number, phone, address, 
             admission_datetime, ward_id, bed, doctor_id, diagnosis, notes, status, discharged_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, patients_data)

    if cursor.execute("SELECT COUNT(*) FROM treatments").fetchone()[0] == 0:
        yesterday_str = yesterday.date().isoformat()
        treatments_data = [
            (1, 'IV Antibiotics', yesterday_str, ''),
            (4, 'IV Fluids', yesterday_str, ''),
            (3, 'Chest X-ray', yesterday_str, '')
        ]
        cursor.executemany(
            "INSERT INTO treatments (patient_id, treatment, date, notes) VALUES (?, ?, ?, ?)",
            treatments_data
        )

    if cursor.execute("SELECT COUNT(*) FROM activity_log").fetchone()[0] == 0:
        log_entries = [
            ('admission', 'patients', 1, 'Sarah Johnson (54F) admitted to AMU Bay 4 (Sepsis, Dr. R. Morgan)', t1),
            ('discharge', 'patients', 2, 'Emily Brown (39F) discharged from AMU Bay 1 (Length of stay: 2 days)', t2),
            ('alert', 'wards', 1, 'AMU capacity reached 91% (Critical threshold exceeded)', t3),
            ('admission', 'patients', 3, 'James Carter (68M) admitted to AMU Bay 2 (Pneumonia, Dr. R. Morgan)', t4),
            ('treatment', 'treatments', 2, 'Mohammed Ali received IV Fluids (AMU Side-room 1, Dr. A. Patel)', t5),
            ('discharge', 'patients', 5, 'Jennifer Lewis (29F) discharged from SSS Bay 2 (Length of stay: 1 day)', t6),
        ]
        for entry in log_entries:
            cursor.execute(
                "INSERT INTO activity_log (action_type, table_name, record_id, description, timestamp) VALUES (?, ?, ?, ?, ?)",
                entry
            )

    create_admin_user(cursor)
    conn.commit()
    conn.close()

def create_tables(cursor):
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS wards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT,
            type TEXT,
            capacity INTEGER NOT NULL,
            occupied INTEGER DEFAULT 0,
            lead_consultant TEXT,
            status TEXT DEFAULT 'active',
            gender_type TEXT DEFAULT 'Mixed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialty TEXT NOT NULL,
            members INTEGER DEFAULT 0,
            lead TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialty TEXT NOT NULL,
            grade TEXT DEFAULT 'Consultant',
            on_duty BOOLEAN DEFAULT 1,
            team_id INTEGER,
            ward_id INTEGER,
            pager TEXT,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES teams (id),
            FOREIGN KEY (ward_id) REFERENCES wards (id)
        );

        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            dob TEXT,
            age INTEGER,
            gender TEXT,
            nhs_number TEXT,
            phone TEXT,
            address TEXT,
            admission_datetime TEXT NOT NULL,
            ward_id INTEGER,
            bed TEXT NOT NULL,
            doctor_id INTEGER,
            diagnosis TEXT NOT NULL,
            notes TEXT,
            status TEXT DEFAULT 'Active',
            discharged_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ward_id) REFERENCES wards (id),
            FOREIGN KEY (doctor_id) REFERENCES doctors (id)
        );

        CREATE TABLE IF NOT EXISTS treatments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            treatment TEXT NOT NULL,
            date DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        );

        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action_type TEXT NOT NULL,
            table_name TEXT NOT NULL,
            record_id INTEGER,
            description TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

def create_admin_user(cursor):
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                       ("admin", "admin123", "admin"))

init_db()

def get_dashboard_stats():
    conn = get_db_connection()
    active_wards = conn.execute("SELECT COUNT(*) FROM wards WHERE status='active'").fetchone()[0]
    total_teams = conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
    treatments_today = conn.execute("SELECT COUNT(*) FROM treatments WHERE date = date('now')").fetchone()[0]
    doctors_on_duty = conn.execute("SELECT COUNT(*) FROM doctors WHERE on_duty=1").fetchone()[0]
    total_patients = conn.execute("SELECT COUNT(*) FROM patients WHERE status='Active'").fetchone()[0]
    conn.close()
    return {
        "active_wards": active_wards,
        "total_teams": total_teams,
        "treatments_today": treatments_today,
        "doctors_on_duty": doctors_on_duty,
        "total_patients": total_patients,
    }

def get_doctors_summary():
    conn = get_db_connection()
    total = conn.execute("SELECT COUNT(*) FROM doctors").fetchone()[0]
    consultants = conn.execute("SELECT COUNT(*) FROM doctors WHERE grade LIKE '%Consultant%'").fetchone()[0]
    on_duty = conn.execute("SELECT COUNT(*) FROM doctors WHERE on_duty=1").fetchone()[0]
    conn.close()
    return total, consultants, on_duty

@app.route("/")
def home():
    stats = get_dashboard_stats()
    return render_template("index.html", stats=stats)

@app.route("/wards")
def wards_page():
    conn = get_db_connection()
    wards = conn.execute("""
        SELECT id, name, code, type, capacity, occupied, lead_consultant, status, gender_type
        FROM wards ORDER BY name
    """).fetchall()

    ward_patients = {}
    for ward in wards:
        patients = conn.execute(
            "SELECT id, name, gender, age, diagnosis, bed FROM patients WHERE ward_id = ? AND status='Active'",
            (ward['id'],)
        ).fetchall()
        ward_patients[ward['id']] = patients

    total_wards = len(wards)
    total_occupancy = 0
    valid_wards = 0
    critical_wards = 0
    for ward in wards:
        if ward["capacity"] > 0:
            occupancy = (ward["occupied"] / ward["capacity"]) * 100
            total_occupancy += occupancy
            valid_wards += 1
            if occupancy >= 90:
                critical_wards += 1
    avg_occupancy = round(total_occupancy / valid_wards) if valid_wards > 0 else 0
    ward_stats = {
        "total_wards": total_wards,
        "avg_occupancy": avg_occupancy,
        "critical_wards": critical_wards,
    }
    conn.close()
    return render_template("wards.html", wards=wards, ward_patients=ward_patients, stats=ward_stats)

@app.route("/ward")
def ward_overview_page():
    conn = get_db_connection()
    wards = conn.execute("""
        SELECT id, name, code, type, capacity, occupied, lead_consultant, status, gender_type
        FROM wards ORDER BY name
    """).fetchall()

    ward_patients = {}
    for ward in wards:
        patients = conn.execute(
            "SELECT id, name, gender, age, diagnosis, bed FROM patients WHERE ward_id = ? AND status='Active'",
            (ward['id'],)
        ).fetchall()
        ward_patients[ward['id']] = patients

    conn.close()
    return render_template("ward.html", wards=wards, ward_patients=ward_patients)

@app.route("/ward/<int:ward_id>")
def ward_detail_page(ward_id):
    conn = get_db_connection()
    ward = conn.execute("SELECT * FROM wards WHERE id = ?", (ward_id,)).fetchone()
    if ward is None:
        conn.close()
        return redirect(url_for("wards_page"))

    patients = conn.execute(
        "SELECT id, name, gender, age, diagnosis, bed FROM patients WHERE ward_id = ?",
        (ward_id,)
    ).fetchall()
    conn.close()

    return render_template(
        "ward.html",
        wards=[ward],
        ward_patients={ward['id']: patients}
    )

@app.route("/teams")
def teams_page():
    conn = get_db_connection()
    teams = conn.execute("SELECT * FROM teams ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("teams.html", teams=teams)

@app.route("/patients")
def patients_page():
    conn = get_db_connection()
    patients = conn.execute("""
        SELECT p.*, w.name as ward_name, d.name as doctor_name 
        FROM patients p
        LEFT JOIN wards w ON p.ward_id = w.id
        LEFT JOIN doctors d ON p.doctor_id = d.id
        ORDER BY p.created_at DESC
    """).fetchall()
    wards = conn.execute("SELECT id, name, gender_type FROM wards WHERE status='active'").fetchall()
    doctors = conn.execute("SELECT id, name FROM doctors WHERE on_duty=1").fetchall()
    conn.close()
    return render_template("patient.html", patients=patients, wards=wards, doctors=doctors, now=datetime.now)

@app.route("/patients/add", methods=['GET', 'POST'])
def add_patient_page():
    if request.method == 'POST':
        data = request.get_json()
        first_name = data.get('firstName', '')
        last_name = data.get('lastName', '')
        full_name = f"{first_name} {last_name}".strip()
        dob = data.get('dob')
        age = data.get('age')
        sex = data.get('sex')
        nhs_number = data.get('nhsNumber')
        phone = data.get('phone')
        address = data.get('address')
        admission_date = data.get('admissionDate')
        ward_id = data.get('ward')
        bed = data.get('bed')
        doctor_id = data.get('consultant')
        diagnosis = data.get('diagnosis')
        notes = data.get('notes')
        status = 'Active'

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO patients 
            (name, dob, age, gender, nhs_number, phone, address, 
             admission_datetime, ward_id, bed, doctor_id, diagnosis, notes, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (full_name, dob, age, sex, nhs_number, phone, address,
              admission_date, ward_id, bed, doctor_id, diagnosis, notes, status))
        conn.commit()
        patient_id = cursor.lastrowid
        if ward_id:
            cursor.execute("UPDATE wards SET occupied = occupied + 1 WHERE id = ?", (ward_id,))
            conn.commit()

        ward_name = conn.execute("SELECT name FROM wards WHERE id = ?", (ward_id,)).fetchone()['name']
        doctor_name = conn.execute("SELECT name FROM doctors WHERE id = ?", (doctor_id,)).fetchone()['name']
        conn.close()

        description = f"{full_name} ({age}{sex[0]}) admitted to {ward_name} {bed} ({diagnosis}, {doctor_name})"
        log_activity('admission', 'patients', patient_id, description, admission_date)

        return jsonify({'success': True, 'patient_id': patient_id}), 201

    conn = get_db_connection()
    wards = conn.execute("SELECT id, name, gender_type FROM wards WHERE status='active'").fetchall()
    doctors = conn.execute("SELECT id, name FROM doctors WHERE on_duty=1").fetchall()
    conn.close()
    return render_template("add-patient.html", wards=wards, doctors=doctors, now=datetime.now)

@app.route("/patients/<int:patient_id>")
def patient_detail(patient_id):
    conn = get_db_connection()
    patient = conn.execute(
        """
        SELECT p.*, w.name as ward_name, d.name as doctor_name
        FROM patients p
        LEFT JOIN wards w ON p.ward_id = w.id
        LEFT JOIN doctors d ON p.doctor_id = d.id
        WHERE p.id = ?
        """, (patient_id,)
    ).fetchone()

    treatments = conn.execute(
        "SELECT * FROM treatments WHERE patient_id = ? ORDER BY date DESC", 
        (patient_id,)
    ).fetchall()

    conn.close()

    if patient is None:
        return redirect(url_for("patients_page"))

    return render_template("patient-detail.html", patient=patient, treatments=treatments)

@app.route("/team-patients")
def team_patient_page():
    return render_template("team-patients.html")

@app.route("/treatments")
def treatments_page():
    conn = get_db_connection()
    treatments = conn.execute("""
        SELECT t.*, p.name as patient_name 
        FROM treatments t
        LEFT JOIN patients p ON t.patient_id = p.id
        ORDER BY t.date DESC
    """).fetchall()
    patients = conn.execute("SELECT id, name FROM patients WHERE status='Active'").fetchall()
    conn.close()
    return render_template("record-treatment.html", treatments=treatments, patients=patients)

@app.route("/reports")
def reports_page():
    stats = get_dashboard_stats()
    return render_template("reports.html", stats=stats)

@app.route("/notifications")
def notifications_page():
    return render_template("notifications.html")

@app.route("/profile")
def profile_page():
    return render_template("profile-security.html")

@app.route("/manage-doctors")
def doctors_page():
    conn = get_db_connection()
    doctors = conn.execute("""
        SELECT d.*, t.name as team_name, w.name as ward_name
        FROM doctors d
        LEFT JOIN teams t ON d.team_id = t.id
        LEFT JOIN wards w ON d.ward_id = w.id
        ORDER BY d.name
    """).fetchall()
    teams = conn.execute("SELECT id, name FROM teams ORDER BY name").fetchall()
    wards = conn.execute("SELECT id, name FROM wards WHERE status='active' ORDER BY name").fetchall()
    total, consultants, on_duty = get_doctors_summary()
    conn.close()
    return render_template("manage-doctors.html", doctors=doctors, teams=teams, wards=wards,
                           total_doctors=total, total_consultants=consultants, total_on_duty=on_duty)

@app.route("/live")
def live_page():
    return render_template("live-activity.html")

@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)

@app.route("/api/live/stats")
def live_stats():
    conn = get_db_connection()
    today_str = date.today().isoformat()
    admissions_today = conn.execute(
        "SELECT COUNT(*) FROM patients WHERE date(admission_datetime) = ?",
        (today_str,)
    ).fetchone()[0]
    discharges_today = conn.execute(
        "SELECT COUNT(*) FROM patients WHERE date(discharged_at) = ?",
        (today_str,)
    ).fetchone()[0]
    critical_wards = conn.execute(
        "SELECT COUNT(*) FROM wards WHERE (occupied * 1.0 / capacity) >= 0.9 AND status='active'"
    ).fetchone()[0]
    staff_on_duty = conn.execute("SELECT COUNT(*) FROM doctors WHERE on_duty=1").fetchone()[0]
    conn.close()
    return jsonify({
        "admissions_today": admissions_today,
        "discharges_today": discharges_today,
        "critical_alerts": critical_wards,
        "staff_on_duty": staff_on_duty
    })

@app.route("/api/live/feed")
def live_feed():
    conn = get_db_connection()
    logs = conn.execute("""
        SELECT action_type, description, timestamp
        FROM activity_log
        WHERE date(timestamp) = date('now')
        ORDER BY timestamp DESC
        LIMIT 20
    """).fetchall()
    conn.close()
    activities = []
    for log in logs:
        activities.append({
            "type": log['action_type'],
            "time": log['timestamp'][11:16],
            "description": log['description']
        })
    return jsonify(activities)

@app.route("/api/live/wards")
def live_wards():
    conn = get_db_connection()
    wards = conn.execute("""
        SELECT name, code, occupied, capacity,
               ROUND((occupied * 100.0 / capacity), 0) as percent
        FROM wards
        WHERE status='active'
        ORDER BY name
    """).fetchall()
    conn.close()
    return jsonify([dict(w) for w in wards])

@app.route("/api/doctors/<int:doctor_id>")
def get_doctor(doctor_id):
    conn = get_db_connection()
    doctor = conn.execute(
        "SELECT id, name, specialty, grade, on_duty, team_id, ward_id, pager, email FROM doctors WHERE id = ?",
        (doctor_id,)
    ).fetchone()
    conn.close()
    if doctor is None:
        return jsonify({'error': 'Doctor not found'}), 404
    return jsonify(dict(doctor))

@app.route("/api/doctors/<int:doctor_id>", methods=["PUT"])
def update_doctor(doctor_id):
    data = request.get_json()
    name = data.get('name')
    specialty = data.get('specialty')
    grade = data.get('grade')
    on_duty = 1 if data.get('on_duty') else 0
    team_id = data.get('team_id')
    ward_id = data.get('ward_id')
    pager = data.get('pager')
    email = data.get('email')
    conn = get_db_connection()
    conn.execute(
        """UPDATE doctors 
           SET name = ?, specialty = ?, grade = ?, on_duty = ?, team_id = ?, ward_id = ?, pager = ?, email = ?
           WHERE id = ?""",
        (name, specialty, grade, on_duty, team_id, ward_id, pager, email, doctor_id)
    )
    conn.commit()
    conn.close()
    log_activity('update', 'doctors', doctor_id, f"Doctor updated: {name}")
    return jsonify({'success': True})

@app.route("/api/doctors", methods=["POST"])
def add_doctor():
    data = request.get_json()
    name = data.get('name')
    specialty = data.get('specialty')
    grade = data.get('grade')
    on_duty = 1 if data.get('on_duty') else 0
    team_id = data.get('team_id')
    ward_id = data.get('ward_id')
    pager = data.get('pager')
    email = data.get('email')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO doctors (name, specialty, grade, on_duty, team_id, ward_id, pager, email)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, specialty, grade, on_duty, team_id, ward_id, pager, email)
    )
    conn.commit()
    doctor_id = cursor.lastrowid
    conn.close()
    log_activity('create', 'doctors', doctor_id, f"New doctor added: {name}")
    return jsonify({'success': True, 'doctor_id': doctor_id}), 201

@app.route("/api/teams/list")
def list_teams():
    conn = get_db_connection()
    teams = conn.execute("SELECT id, name FROM teams ORDER BY name").fetchall()
    conn.close()
    return jsonify([dict(team) for team in teams])

@app.route("/api/wards/list")
def list_wards():
    conn = get_db_connection()
    wards = conn.execute("SELECT id, name FROM wards WHERE status='active' ORDER BY name").fetchall()
    conn.close()
    return jsonify([dict(ward) for ward in wards])

@app.route("/api/wards", methods=["POST"])
def add_ward():
    data = request.form
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO wards (name, code, type, capacity, occupied, lead_consultant, status, gender_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (data["name"], data.get("code", ""), data.get("type", "General"),
         data["capacity"], data.get("occupied", 0), data.get("lead_consultant", ""),
         data.get("status", "active"), data.get("gender_type", "Mixed")),
    )
    conn.commit()
    ward_id = cursor.lastrowid
    conn.close()
    log_activity('create', 'wards', ward_id, f"New ward added: {data['name']}")
    return redirect(url_for("wards_page"))

@app.route("/api/wards/<int:ward_id>", methods=["POST"])
def update_ward(ward_id):
    data = request.form
    conn = get_db_connection()
    conn.execute(
        "UPDATE wards SET name=?, code=?, type=?, capacity=?, occupied=?, lead_consultant=?, status=?, gender_type=? WHERE id=?",
        (data["name"], data.get("code", ""), data.get("type", "General"),
         data["capacity"], data["occupied"], data.get("lead_consultant", ""),
         data.get("status", "active"), data.get("gender_type", "Mixed"), ward_id),
    )
    conn.commit()
    conn.close()
    log_activity('update', 'wards', ward_id, f"Ward updated: {data['name']}")
    return redirect(url_for("wards_page"))

@app.route("/api/wards/<int:ward_id>/delete", methods=["POST"])
def delete_ward(ward_id):
    conn = get_db_connection()
    ward = conn.execute("SELECT name FROM wards WHERE id=?", (ward_id,)).fetchone()
    conn.execute("DELETE FROM wards WHERE id=?", (ward_id,))
    conn.commit()
    conn.close()
    if ward:
        log_activity('delete', 'wards', ward_id, f"Ward deleted: {ward['name']}")
    return redirect(url_for("wards_page"))

@app.route("/api/teams", methods=["POST"])
def add_team():
    data = request.form
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO teams (name, specialty, members, lead) VALUES (?, ?, ?, ?)",
        (data["name"], data["specialty"], data.get("members", 0), data.get("lead", "")),
    )
    conn.commit()
    team_id = cursor.lastrowid
    conn.close()
    log_activity('create', 'teams', team_id, f"New team added: {data['name']}")
    return redirect(url_for("teams_page"))

@app.route("/api/patients/<int:patient_id>/discharge", methods=["POST"])
def discharge_patient(patient_id):
    conn = get_db_connection()
    patient = conn.execute(
        "SELECT p.name, p.age, p.gender, p.ward_id, p.bed, w.name as ward_name "
        "FROM patients p LEFT JOIN wards w ON p.ward_id = w.id WHERE p.id=?",
        (patient_id,)
    ).fetchone()
    if not patient:
        conn.close()
        return jsonify({'error': 'Patient not found'}), 404
    conn.execute("UPDATE patients SET status='Discharged', discharged_at=datetime('now') WHERE id=?", (patient_id,))
    if patient["ward_id"]:
        conn.execute("UPDATE wards SET occupied = occupied - 1 WHERE id = ?", (patient["ward_id"],))
    conn.commit()
    conn.close()
    los = "?"
    description = f"{patient['name']} ({patient['age']}{patient['gender'][0]}) discharged from {patient['ward_name']} {patient['bed']} (Length of stay: {los} days)"
    log_activity('discharge', 'patients', patient_id, description)
    return jsonify({'success': True}), 200

@app.route("/api/patients/<int:patient_id>/transfer", methods=["POST"])
def transfer_patient(patient_id):
    data = request.form
    new_ward_id = data.get("new_ward_id")
    conn = get_db_connection()
    patient = conn.execute(
        "SELECT p.name, p.age, p.gender, p.ward_id, p.bed FROM patients p WHERE id=?",
        (patient_id,)
    ).fetchone()
    if not patient:
        conn.close()
        return jsonify({'error': 'Patient not found'}), 404

    target_ward = conn.execute("SELECT gender_type FROM wards WHERE id = ?", (new_ward_id,)).fetchone()
    if target_ward and target_ward['gender_type'] != 'Mixed' and target_ward['gender_type'] != patient['gender']:
        conn.close()
        return jsonify({'error': 'Gender mismatch: patient cannot be transferred to this ward'}), 400

    old_ward_id = patient["ward_id"]
    if old_ward_id:
        conn.execute("UPDATE wards SET occupied = occupied - 1 WHERE id = ?", (old_ward_id,))
    conn.execute("UPDATE patients SET ward_id=? WHERE id=?", (new_ward_id, patient_id))
    conn.execute("UPDATE wards SET occupied = occupied + 1 WHERE id = ?", (new_ward_id,))
    new_ward_name = conn.execute("SELECT name FROM wards WHERE id=?", (new_ward_id,)).fetchone()['name']
    conn.commit()
    conn.close()

    description = f"{patient['name']} ({patient['age']}{patient['gender'][0]}) transferred to {new_ward_name}"
    log_activity('transfer', 'patients', patient_id, description)
    return jsonify({'success': True}), 200

@app.route("/api/treatments", methods=["POST"])
def add_treatment():
    data = request.get_json()
    patient_id = data.get('patient_id')
    treatment = data.get('treatment')
    date_val = data.get('date', datetime.now().isoformat()[:10])
    notes = data.get('notes', '')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO treatments (patient_id, treatment, date, notes) VALUES (?, ?, ?, ?)",
        (patient_id, treatment, date_val, notes)
    )
    conn.commit()
    treatment_id = cursor.lastrowid
    patient = conn.execute(
        "SELECT p.name, p.age, p.gender, p.ward_id, p.bed, w.name as ward_name "
        "FROM patients p LEFT JOIN wards w ON p.ward_id = w.id WHERE p.id=?",
        (patient_id,)
    ).fetchone()
    conn.close()
    if patient:
        description = f"{patient['name']} ({patient['age']}{patient['gender'][0]}) received {treatment} ({patient['ward_name']} {patient['bed']})"
        log_activity('treatment', 'treatments', treatment_id, description)
    return jsonify({'success': True, 'treatment_id': treatment_id}), 201

if __name__ == "__main__":
    app.run(debug=True, port=5000)