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
from datetime import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = "123"

# Ensure instance folder exists
try:
    os.makedirs(app.instance_path, exist_ok=True)
except OSError:
    pass

DATABASE_PATH = os.path.join(app.instance_path, "hospital.db")

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tables and sample data"""
    print(f"Creating database at: {DATABASE_PATH}")
    conn = get_db_connection()
    cursor = conn.cursor()
    create_tables(cursor)

    # Insert sample wards if none exist
    if cursor.execute("SELECT COUNT(*) FROM wards").fetchone()[0] == 0:
        cursor.executescript("""
            INSERT INTO wards (name, code, type, capacity, occupied, lead_consultant, status, gender_type) VALUES
            ('Acute Medical Unit (AMU)', 'AMU', 'General', 30, 0, 'Dr. Morgan', 'active', 'Mixed'),
            ('Coronary Care Unit (CCU)', 'CCU', 'Cardiology', 12, 0, 'Dr. Khan', 'active', 'Mixed'),
            ('Intensive Care Unit (ICU)', 'ICU', 'Critical', 10, 0, 'Dr. J. Khan', 'active', 'Mixed'),
            ('Respiratory Ward (RESP)', 'RESP', 'Respiratory', 20, 0, 'Dr. Taylor', 'active', 'Mixed'),
            ('Short Stay Surgical (SSS)', 'SSS', 'Surgical', 15, 0, 'Dr. Chen', 'active', 'Mixed'),
            ('Paediatrics (PAED)', 'PAED', 'Paediatrics', 25, 0, 'Dr. Williams', 'active', 'Mixed'),
            ('Stroke Unit (STK)', 'STK', 'Neurology', 18, 0, 'Dr. Ahmed', 'active', 'Mixed'),
            ('Orthopaedic Ward (ORTH)', 'ORTH', 'Orthopaedics', 22, 0, 'Dr. N. Taylor', 'active', 'Mixed'),
            ('Ward A', 'WDA', 'General', 20, 0, 'Dr. Smith', 'active', 'Male'),
            ('Ward B', 'WDB', 'General', 20, 0, 'Dr. Jones', 'active', 'Female'),
            ('Ward C', 'WDC', 'General', 25, 0, 'Dr. Brown', 'active', 'Mixed');
        """)

    # Insert sample doctors if none exist
    if cursor.execute("SELECT COUNT(*) FROM doctors").fetchone()[0] == 0:
        cursor.executescript("""
            INSERT INTO doctors (name, specialty, on_duty) VALUES
            ('Dr. Riley Morgan', 'Acute Medicine', 1),
            ('Dr. Aisha Patel', 'Acute Medicine', 1),
            ('Dr. Noor Khan', 'Cardiology', 1),
            ('Dr. J. Khan', 'ICU', 1),
            ('Dr. N. Taylor', 'Respiratory', 1),
            ('Dr. Peter Ahmed', 'Stroke', 1),
            ('Dr. Laura Chen', 'Surgery', 1),
            ('Dr. S. Williams', 'Paediatrics', 1);
        """)

    create_admin_user(cursor)
    conn.commit()
    conn.close()
    print("Database initialized successfully with sample data!")

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
            on_duty BOOLEAN DEFAULT 1,
            team_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES teams (id)
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
        print("Admin user created successfully!")

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

# ---------- Page Routes ----------
@app.route("/")
def home():
    stats = get_dashboard_stats()
    return render_template("index.html", stats=stats)

@app.route("/wards")
def wards_page():
    conn = get_db_connection()
    wards = conn.execute("""
        SELECT id, name, code, type, capacity, occupied, lead_consultant, status
        FROM wards ORDER BY name
    """).fetchall()
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
    return render_template("wards.html", wards=wards, stats=ward_stats)

@app.route("/ward")
def ward_overview_page():
    return render_template("ward.html")

@app.route("/ward/<int:ward_id>")
def ward_detail_page(ward_id):
    conn = get_db_connection()
    ward = conn.execute("SELECT * FROM wards WHERE id = ?", (ward_id,)).fetchone()
    if ward is None:
        conn.close()
        return redirect(url_for("wards_page"))
    patients = conn.execute("SELECT * FROM patients WHERE ward_id = ?", (ward_id,)).fetchall()
    conn.close()
    return render_template("ward.html", ward=ward, patients=patients)

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
        conn.close()
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
    conn.close()
    if patient is None:
        return redirect(url_for("patients_page"))
    return render_template("patient-detail.html", patient=patient, now=datetime.now)

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
    return render_template("manage-doctors.html")

@app.route("/live")
def live_page():
    return render_template("live-activity.html")

@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)

# ---------- API / Data Operation Routes ----------
@app.route("/api/wards", methods=["POST"])
def add_ward():
    data = request.form
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO wards (name, code, type, capacity, occupied, lead_consultant, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (data["name"], data.get("code", ""), data.get("type", "General"),
         data["capacity"], data.get("occupied", 0), data.get("lead_consultant", ""),
         data.get("status", "active")),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("wards_page"))

@app.route("/api/wards/<int:ward_id>", methods=["POST"])
def update_ward(ward_id):
    data = request.form
    conn = get_db_connection()
    conn.execute(
        "UPDATE wards SET name=?, code=?, type=?, capacity=?, occupied=?, lead_consultant=?, status=? WHERE id=?",
        (data["name"], data.get("code", ""), data.get("type", "General"),
         data["capacity"], data["occupied"], data.get("lead_consultant", ""),
         data.get("status", "active"), ward_id),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("wards_page"))

@app.route("/api/wards/<int:ward_id>/delete", methods=["POST"])
def delete_ward(ward_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM wards WHERE id=?", (ward_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("wards_page"))

@app.route("/api/teams", methods=["POST"])
def add_team():
    data = request.form
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO teams (name, specialty, members, lead) VALUES (?, ?, ?, ?)",
        (data["name"], data["specialty"], data.get("members", 0), data.get("lead", "")),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("teams_page"))

@app.route("/api/patients/<int:patient_id>/discharge", methods=["POST"])
def discharge_patient(patient_id):
    conn = get_db_connection()
    patient = conn.execute("SELECT ward_id FROM patients WHERE id=?", (patient_id,)).fetchone()
    conn.execute("UPDATE patients SET status='Discharged' WHERE id=?", (patient_id,))
    if patient and patient["ward_id"]:
        conn.execute("UPDATE wards SET occupied = occupied - 1 WHERE id = ?", (patient["ward_id"],))
    conn.commit()
    conn.close()
    return jsonify({'success': True}), 200

@app.route("/api/patients/<int:patient_id>/transfer", methods=["POST"])
def transfer_patient(patient_id):
    data = request.form
    new_ward_id = data.get("new_ward_id")
    conn = get_db_connection()
    patient = conn.execute("SELECT ward_id FROM patients WHERE id=?", (patient_id,)).fetchone()
    if patient and patient["ward_id"]:
        conn.execute("UPDATE wards SET occupied = occupied - 1 WHERE id = ?", (patient["ward_id"],))
    conn.execute("UPDATE patients SET ward_id=? WHERE id=?", (new_ward_id, patient_id))
    conn.execute("UPDATE wards SET occupied = occupied + 1 WHERE id = ?", (new_ward_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)