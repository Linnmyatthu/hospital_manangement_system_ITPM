from flask import (
    Flask,
    render_template,
    send_from_directory,
    request,
    redirect,
    url_for,
    jsonify,
    make_response,
    session       
)
import tempfile
from functools import wraps
import os
import sqlite3
import csv           
from io import StringIO 
from datetime import datetime, timedelta, date
import random

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-in-production-123"

@app.context_processor
def inject_user():
    return dict(user_role=session.get('role'), user_id=session.get('user_id'))

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login_page"))
        return f(*args, **kwargs)
    return decorated

def role_required(allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get("role") not in allowed_roles:
                return jsonify({"error": "Permission denied"}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

try:
    os.makedirs(app.instance_path, exist_ok=True)
except OSError:
    pass

DATABASE_PATH = os.path.join(tempfile.gettempdir(), "hospital.db") if os.environ.get('VERCEL') else os.path.join(app.instance_path, "hospital.db")

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
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

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
    cursor.execute("PRAGMA table_info(users)")
    user_cols = [col[1] for col in cursor.fetchall()]
    if 'email' not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN email TEXT")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users (email)")

def fix_missing_team_ids():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM doctors WHERE team_id IS NULL")
    if cursor.fetchone()[0] > 0:
        team_ids = cursor.execute("SELECT id FROM teams").fetchall()
        if team_ids:
            team_id_list = [t['id'] for t in team_ids]
            cursor.execute("SELECT id, ward_id FROM doctors WHERE team_id IS NULL")
            null_team_doctors = cursor.fetchall()
            for doc in null_team_doctors:
                assigned_team = None
                if doc['ward_id']:
                    ward_team = cursor.execute(
                        "SELECT team_id FROM doctors WHERE ward_id = ? AND team_id IS NOT NULL LIMIT 1",
                        (doc['ward_id'],)
                    ).fetchone()
                    if ward_team:
                        assigned_team = ward_team['team_id']
                if not assigned_team:
                    assigned_team = random.choice(team_id_list)
                cursor.execute("UPDATE doctors SET team_id = ? WHERE id = ?", (assigned_team, doc['id']))
            conn.commit()
    conn.close()

def fix_missing_patient_doctors():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM patients WHERE doctor_id IS NULL AND ward_id IS NOT NULL")
    if cursor.fetchone()[0] > 0:
        patients = cursor.execute("SELECT id, ward_id FROM patients WHERE doctor_id IS NULL AND ward_id IS NOT NULL").fetchall()
        for patient in patients:
            doc = cursor.execute(
                "SELECT id FROM doctors WHERE ward_id = ? AND on_duty = 1 LIMIT 1",
                (patient['ward_id'],)
            ).fetchone()
            if doc:
                cursor.execute("UPDATE patients SET doctor_id = ? WHERE id = ?", (doc['id'], patient['id']))
        conn.commit()
    conn.close()

def create_default_users(cursor):
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
            ("admin", "admin@hospital.com", "admin123", "admin"),
        )
    cursor.execute("SELECT * FROM users WHERE username = 'consultant'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
            ("consultant", "consultant@hospital.com", "consultant123", "consultant"),
        )
    cursor.execute("SELECT * FROM users WHERE username = 'junior'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, email, password, role) VALUES (?, ?, ?, ?)",
            ("junior", "junior@hospital.com", "junior123", "junior"),
        )

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    create_tables(cursor)
    migrate_tables(cursor)
    create_default_users(cursor)
    conn.commit()

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

    now = datetime.now()
    two_days_ago = (now - timedelta(days=2)).isoformat()
    one_week_ago = (now - timedelta(days=7)).isoformat()
    three_days_ago = (now - timedelta(days=3)).isoformat()
    today_morning = now.replace(hour=9, minute=30, second=0).isoformat()
    today_afternoon = now.replace(hour=14, minute=15, second=0).isoformat()
    yesterday_evening = (now - timedelta(days=1)).replace(hour=18, minute=45, second=0).isoformat()
    yesterday_iso = (now - timedelta(days=1)).isoformat()
    two_days_iso = (now - timedelta(days=2)).isoformat()
    now_iso = now.isoformat()

    if cursor.execute("SELECT COUNT(*) FROM wards").fetchone()[0] == 0:
        cursor.executescript("""
            INSERT INTO wards (name, code, type, capacity, occupied, lead_consultant, status, gender_type) VALUES
            ('Acute Medical Unit (AMU)', 'AMU', 'General', 32, 0, 'Dr. Morgan', 'active', 'Mixed'),
            ('Coronary Care Unit (CCU)', 'CCU', 'Cardiology', 14, 0, 'Dr. Khan', 'active', 'Mixed'),
            ('Intensive Care Unit (ICU)', 'ICU', 'Critical', 10, 0, 'Dr. J. Khan', 'active', 'Mixed'),
            ('Respiratory Ward (RESP)', 'RESP', 'Respiratory', 26, 0, 'Dr. Taylor', 'active', 'Mixed'),
            ('Short Stay Surgical (SSS)', 'SSS', 'Surgical', 24, 0, 'Dr. Chen', 'active', 'Mixed'),
            ('Paediatrics (PAED)', 'PAED', 'Paediatrics', 20, 0, 'Dr. Williams', 'active', 'Mixed'),
            ('Stroke Unit (STK)', 'STK', 'Neurology', 18, 0, 'Dr. Ahmed', 'active', 'Mixed'),
            ('Orthopaedic Ward (ORTH)', 'ORTH', 'Orthopaedics', 22, 0, 'Dr. N. Taylor', 'active', 'Mixed'),
            ('Ward A', 'WDA', 'General', 20, 0, 'Dr. Smith', 'active', 'Male'),
            ('Ward B', 'WDB', 'General', 20, 0, 'Dr. Jones', 'active', 'Female'),
            ('Ward C', 'WDC', 'General', 25, 0, 'Dr. Brown', 'active', 'Mixed');
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
            ('Sarah Johnson', '1970-01-01', 54, 'Female', 'NHS001', '0123456789', '123 Main St', t1, 1, 'Bay 4', 1, 'Sepsis', 'Patient presented with high fever and hypotension', 'Active', None),
            ('Emily Brown', '1985-02-02', 39, 'Female', 'NHS002', '0123456780', '456 Oak Ave', (yesterday - timedelta(days=2)).isoformat(), 1, 'Bay 1', 1, 'UTI', 'Recurrent urinary infections', 'Discharged', t2),
            ('James Carter', '1956-03-03', 68, 'Male', 'NHS003', '0123456781', '789 Pine Rd', t3, 1, 'Bay 2', 1, 'Pneumonia', 'Cough, fever, chest pain', 'Active', None),
            ('Mohammed Ali', '1975-04-04', 49, 'Male', 'NHS004', '0123456782', '321 Elm St', (yesterday - timedelta(hours=5)).isoformat(), 1, 'Side-room 1', 1, 'Chest pain', 'ECG shows ST elevation', 'Active', None),
            ('Jennifer Lewis', '1995-05-05', 29, 'Female', 'NHS005', '0123456783', '654 Cedar Ln', (yesterday - timedelta(days=2)).isoformat(), 5, 'Bay 2', 1, 'Appendicitis', 'Right lower quadrant pain', 'Discharged', t4),
            ('Thomas Wright', '1979-06-06', 45, 'Male', 'NHS006', '0123456784', '987 Birch Dr', t5, 2, 'Bay 1', 4, 'Acute MI', 'Chest pain radiating to left arm', 'Active', None),
            ('Patricia White', '1958-07-07', 66, 'Female', 'NHS007', '0123456785', '147 Spruce Ct', (yesterday - timedelta(days=7)).isoformat(), 1, 'Bay 1', 1, 'COPD', 'Shortness of breath, wheezing', 'Discharged', (yesterday - timedelta(hours=2)).isoformat()),
            ('David Wilson', '1980-08-08', 44, 'Male', 'NHS008', '0123456786', '258 Willow Way', t6, 1, 'Bay 5', 1, 'Observation', 'Rule out cardiac event', 'Active', None),
            ('Linda Martinez', '1965-11-12', 58, 'Female', 'NHS009', '0771234567', '12 Church St', two_days_ago, 4, 'Bed 6', 3, 'Asthma exacerbation', 'Wheeze, peak flow reduced', 'Active', None),
            ('Robert Taylor', '1949-03-22', 75, 'Male', 'NHS010', '0772345678', '45 High St', one_week_ago, 7, 'Bay 3', 6, 'Ischemic stroke', 'Left-sided weakness, slurred speech', 'Active', None),
            ('Susan Clark', '1992-07-19', 32, 'Female', 'NHS011', '0773456789', '89 Park Ave', three_days_ago, 9, 'Bed 12', 9, 'Femur fracture', 'Fall from height, awaiting surgery', 'Active', None),
            ('Paul Lewis', '1972-09-30', 52, 'Male', 'NHS012', '0774567890', '34 Queen St', today_morning, 2, 'CCU Bed 3', 5, 'Heart failure', 'Dyspnoea, peripheral oedema', 'Active', None),
            ('Emma Young', '2005-01-15', 19, 'Female', 'NHS013', '0775678901', '7 Victoria Rd', three_days_ago, 6, 'Bay 2', 7, 'Pneumonia', 'Fever, cough, reduced air entry', 'Active', None),
            ('George King', '1988-05-28', 38, 'Male', 'NHS014', '0776789012', '23 The Meadows', two_days_ago, 5, 'Bay 4', 8, 'Cholecystitis', 'Right upper quadrant pain, fever', 'Active', None),
            ('Margaret Scott', '1953-12-02', 72, 'Female', 'NHS015', '0777890123', '101 Green Lane', one_week_ago, 10, 'Bed 5', 10, 'Hip replacement', 'Post-operative day 5, mobilising', 'Active', None),
            ('Steven Adams', '1962-06-17', 62, 'Male', 'NHS016', '0778901234', '22 Bridge St', yesterday_evening, 3, 'ICU Bed 2', 11, 'Sepsis', 'Multi-organ dysfunction', 'Critical', None),
            ('Angela Baker', '1983-04-08', 43, 'Female', 'NHS017', '0779012345', '11 Hilltop', three_days_ago, 4, 'Bay 1', 12, 'COPD exacerbation', 'Hypercapnia, on NIV', 'Active', None),
            ('Charles Evans', '1990-10-25', 35, 'Male', 'NHS018', '0780123456', '9 Station Rd', today_afternoon, 1, 'Bay 3', 13, 'Diabetic ketoacidosis', 'Blood glucose 28 mmol/L, acidosis', 'Active', None),
            ('Deborah Green', '1945-08-14', 80, 'Female', 'NHS019', '0781234567', '76 Church Lane', one_week_ago, 8, 'Bed 8', 14, 'Fractured NOF', 'Awaiting surgery, pain controlled', 'Active', None),
            ('Kevin Hall', '1976-12-01', 49, 'Male', 'NHS020', '0782345678', '5 Park Crescent', two_days_ago, 9, 'Bay 2', 15, 'Cellulitis', 'Right leg redness, swelling', 'Active', None),
            ('Nancy Allen', '2008-03-11', 16, 'Female', 'NHS021', '0783456789', '32 West End', three_days_ago, 6, 'Bed 1', 16, 'Asthma', 'Mild attack, responding to inhalers', 'Active', None),
            ('Gary Wright', '1957-07-19', 67, 'Male', 'NHS022', '0784567890', '88 South Rd', one_week_ago, 7, 'Bay 1', 17, 'TIA', 'Resolved symptoms, awaiting outpatient', 'Active', None),
            ('Helen Robinson', '1995-09-23', 30, 'Female', 'NHS023', '0785678901', '41 East Ave', today_morning, 10, 'Bed 3', 18, 'Pregnancy induced hypertension', 'BP 150/95, proteinuria', 'Active', None),
            ('Peter Mitchell', '1969-02-14', 55, 'Male', 'NHS024', '0786789012', '19 North St', three_days_ago, 11, 'Bay 6', 19, 'Alcohol withdrawal', 'CIWA protocol started', 'Active', None),
            ('Ruth Carter', '1973-11-21', 50, 'Female', 'NHS025', '0787890123', '63 The Crescent', two_days_ago, 2, 'CCU Bed 2', 20, 'Atrial fibrillation', 'Rate controlled, warfarin started', 'Active', None),
            ('Frank Phillips', '1950-01-30', 74, 'Male', 'NHS026', '0788901234', '7 Manor Road', one_week_ago, 5, 'Bay 5', 21, 'Pancreatitis', 'Abdominal pain, raised amylase', 'Active', None),
            ('Diana Campbell', '1987-06-18', 38, 'Female', 'NHS027', '0789012345', '22 Brookside', yesterday_evening, 4, 'Side-room 2', 22, 'Pulmonary embolism', 'Chest pain, hypoxia, on anticoagulation', 'Active', None),
            ('Stephen Parker', '2002-12-05', 22, 'Male', 'NHS028', '0790123456', '15 Riverside', three_days_ago, 6, 'Bay 3', 23, 'Appendicectomy', 'Post-op day 2, recovering well', 'Active', None),
        ]
        cursor.executemany("""
            INSERT INTO patients 
            (name, dob, age, gender, nhs_number, phone, address, 
             admission_datetime, ward_id, bed, doctor_id, diagnosis, notes, status, discharged_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, patients_data)
        cursor.execute("UPDATE wards SET occupied = 0")
        cursor.execute("""
            UPDATE wards SET occupied = (
                SELECT COUNT(*) FROM patients 
                WHERE patients.ward_id = wards.id AND patients.status = 'Active'
            )
        """)

    if cursor.execute("SELECT COUNT(*) FROM treatments").fetchone()[0] == 0:
        treatments_data = [
            (1, 'IV Antibiotics', (datetime.now() - timedelta(days=1)).date().isoformat(), 'Ceftriaxone 2g daily'),
            (4, 'IV Fluids', (datetime.now() - timedelta(days=1)).date().isoformat(), '1L NaCl 0.9% over 8h'),
            (3, 'Chest X-ray', (datetime.now() - timedelta(days=1)).date().isoformat(), 'Bilateral infiltrates'),
            (9, 'Nebulised Salbutamol', (datetime.now() - timedelta(days=1)).date().isoformat(), '2.5mg 6 hourly'),
            (10, 'CT Head', (datetime.now() - timedelta(days=2)).date().isoformat(), 'No acute bleed'),
            (11, 'Traction', (datetime.now() - timedelta(days=2)).date().isoformat(), 'Lower limb'),
            (12, 'Echocardiogram', (datetime.now() - timedelta(days=1)).date().isoformat(), 'LVEF 35%'),
            (13, 'Chest Physiotherapy', (datetime.now() - timedelta(days=1)).date().isoformat(), 'Twice daily'),
            (14, 'Laparoscopic Cholecystectomy', (datetime.now() - timedelta(days=1)).date().isoformat(), 'Performed 12/04'),
            (15, 'IV Paracetamol', (datetime.now() - timedelta(days=1)).date().isoformat(), '1g 6 hourly'),
            (16, 'Noradrenaline Infusion', (datetime.now() - timedelta(hours=12)).isoformat()[:10], '0.1 mcg/kg/min'),
            (17, 'Non-invasive Ventilation', (datetime.now() - timedelta(days=1)).date().isoformat(), 'ST mode, IPAP 14'),
            (18, 'Insulin Infusion', datetime.now().date().isoformat(), 'Actrapid 5 units/hr'),
            (19, 'Pre-op Assessment', (datetime.now() - timedelta(days=2)).date().isoformat(), 'Fit for surgery'),
            (20, 'Flucloxacillin', (datetime.now() - timedelta(days=1)).date().isoformat(), '500mg QDS'),
            (21, 'Salbutamol MDI', datetime.now().date().isoformat(), '2 puffs PRN'),
            (22, 'Aspirin 300mg', (datetime.now() - timedelta(days=1)).date().isoformat(), 'Loading dose'),
            (23, 'Labetalol', datetime.now().date().isoformat(), '200mg TDS'),
            (24, 'Chlordiazepoxide', (datetime.now() - timedelta(days=1)).date().isoformat(), '50mg QDS'),
            (25, 'Digoxin', (datetime.now() - timedelta(days=2)).date().isoformat(), '125mcg OD'),
            (26, 'IV Fluids', (datetime.now() - timedelta(days=1)).date().isoformat(), 'Hartmanns 1L'),
            (27, 'Therapeutic Enoxaparin', (datetime.now() - timedelta(days=1)).date().isoformat(), '1.5mg/kg OD'),
            (28, 'Post-op Antibiotics', datetime.now().date().isoformat(), 'Co-amoxiclav'),
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
            ('admission', 'patients', 9, 'Linda Martinez (58F) admitted to RESP Bay 6 (Asthma, Dr. Taylor)', two_days_iso),
            ('admission', 'patients', 10, 'Robert Taylor (75M) admitted to STK Bay 3 (Stroke, Dr. Ahmed)', one_week_ago),
            ('transfer', 'patients', 10, 'Robert Taylor transferred from STK to AMU for physiotherapy', (datetime.now() - timedelta(days=3)).isoformat()),
            ('treatment', 'treatments', 9, 'Linda Martinez received Nebulised Salbutamol (RESP Bay 6)', yesterday_iso),
            ('alert', 'wards', 3, 'ICU occupancy reached 90% (3 beds free)', yesterday_iso),
            ('admission', 'patients', 16, 'Steven Adams (62M) admitted to ICU Bed 2 (Sepsis, Dr. J. Khan)', yesterday_iso),
            ('treatment', 'treatments', 16, 'Steven Adams started on Noradrenaline infusion', now_iso),
            ('discharge', 'patients', 7, 'Patricia White (66F) discharged from AMU Bay 1 (COPD, LOS 7 days)', (datetime.now() - timedelta(hours=2)).isoformat()),
            ('admission', 'patients', 18, 'Charles Evans (35M) admitted to AMU Bay 3 (DKA, Dr. Morgan)', today_morning),
            ('treatment', 'treatments', 18, 'Charles Evans on Insulin infusion (DKA protocol)', now_iso),
            ('alert', 'wards', 4, 'RESP ward capacity at 88%', yesterday_iso),
            ('transfer', 'patients', 15, 'Margaret Scott transferred from Ward B to Orthopaedic Ward for rehab', (datetime.now() - timedelta(days=1)).isoformat()),
        ]
        for entry in log_entries:
            cursor.execute(
                "INSERT INTO activity_log (action_type, table_name, record_id, description, timestamp) VALUES (?, ?, ?, ?, ?)",
                entry
            )

    create_default_users(cursor)
    conn.commit()
    conn.close()
    fix_missing_team_ids()
    fix_missing_patient_doctors()

def ensure_today_sample_data():
    conn = get_db_connection()
    today = date.today().isoformat()
    row = conn.execute("SELECT COUNT(*) FROM activity_log WHERE date(timestamp) = ?", (today,)).fetchone()
    if row[0] == 0:
        now_iso = datetime.now().isoformat()
        sample_entries = [
            ('admission', 'patients', 999, f"Sample admission – John Doe (45M) admitted to AMU Bay 6", now_iso),
            ('discharge', 'patients', 999, f"Sample discharge – Jane Smith (32F) from Ward A", now_iso),
            ('alert', 'wards', 1, "AMU capacity reached 94% (critical threshold)", now_iso),
            ('treatment', 'treatments', 999, "IV Antibiotics administered – Patient in ICU", now_iso),
        ]
        for entry in sample_entries:
            conn.execute(
                "INSERT INTO activity_log (action_type, table_name, record_id, description, timestamp) VALUES (?, ?, ?, ?, ?)",
                entry
            )
        conn.commit()
    conn.close()

init_db()
ensure_today_sample_data()

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

@app.route("/login", methods=["GET"])
def login_page():
    if session.get("user_id"):
        return redirect(url_for("home"))
    return render_template("login.html")

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    email_or_user = (data.get("email") or "").strip().lower()
    password = (data.get("password") or "").strip()
    role_input = (data.get("role") or "").strip()

    if not email_or_user or not password or not role_input:
        return jsonify({"success": False, "error": "All fields are required."}), 400

    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE (LOWER(username) = ? OR LOWER(email) = ?) AND password = ?",
        (email_or_user, email_or_user, password),
    ).fetchone()
    conn.close()

    if not user:
        return jsonify({"success": False, "error": "Invalid credentials. Please try again."}), 401

    if role_input != user["role"]:
        return jsonify({"success": False, "error": f"Role mismatch. Your account role is '{user['role']}'."}), 401

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]
    return jsonify({"success": True, "role": user["role"]})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login_page"))

@app.route("/api/change-password", methods=["POST"])
@login_required
def change_password():
    data = request.get_json(silent=True) or {}
    current_pw = (data.get("currentPassword") or "").strip()
    new_pw = (data.get("newPassword") or "").strip()
    confirm_pw = (data.get("confirmPassword") or "").strip()

    if not current_pw or not new_pw or not confirm_pw:
        return jsonify({"success": False, "error": "All password fields are required."}), 400

    if new_pw != confirm_pw:
        return jsonify({"success": False, "error": "New passwords do not match."}), 400

    if len(new_pw) < 8:
        return jsonify({"success": False, "error": "New password must be at least 8 characters."}), 400

    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE id = ? AND password = ?",
        (session["user_id"], current_pw),
    ).fetchone()

    if not user:
        conn.close()
        return jsonify({"success": False, "error": "Current password is incorrect."}), 401

    conn.execute(
        "UPDATE users SET password = ? WHERE id = ?",
        (new_pw, session["user_id"]),
    )
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/get-password", methods=["GET"])
@login_required
def get_current_password():
    conn = get_db_connection()
    user = conn.execute(
        "SELECT password FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()
    conn.close()
    if user:
        return jsonify({"success": True, "password": user["password"]})
    return jsonify({"success": False, "error": "User not found"}), 404

@app.route("/")
@login_required
def home():
    stats = get_dashboard_stats()
    return render_template("index.html", stats=stats)

@app.route("/wards")
@login_required
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
@login_required
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
@login_required
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
@login_required
def teams_page():
    conn = get_db_connection()
    teams = conn.execute("SELECT * FROM teams ORDER BY created_at DESC").fetchall()
    
    teams_with_counts = []
    for team in teams:
        member_count = conn.execute(
            "SELECT COUNT(*) FROM doctors WHERE team_id = ?", (team['id'],)
        ).fetchone()[0]
        teams_with_counts.append({
            'id': team['id'],
            'name': team['name'],
            'specialty': team['specialty'],
            'lead': team['lead'],
            'members': member_count
        })
    
    consultants_count = conn.execute(
        "SELECT COUNT(*) FROM doctors WHERE grade LIKE '%Consultant%'"
    ).fetchone()[0]
    
    teams_oncall = conn.execute("""
        SELECT COUNT(DISTINCT t.id)
        FROM teams t
        JOIN doctors d ON d.team_id = t.id
        WHERE d.on_duty = 1
    """).fetchone()[0]
    
    conn.close()
    return render_template("teams.html", teams=teams_with_counts,
                           consultants_count=consultants_count,
                           teams_oncall=teams_oncall)

@app.route("/patients")
@login_required
def patients_page():
    conn = get_db_connection()
    patients = conn.execute("""
        SELECT p.*, w.name as ward_name, d.name as doctor_name 
        FROM patients p
        LEFT JOIN wards w ON p.ward_id = w.id
        LEFT JOIN doctors d ON p.doctor_id = d.id
        WHERE p.status = 'Active'
        ORDER BY p.created_at DESC
    """).fetchall()
    wards = conn.execute("SELECT id, name, gender_type FROM wards WHERE status='active'").fetchall()
    doctors = conn.execute("SELECT id, name FROM doctors WHERE on_duty=1").fetchall()
    conn.close()
    return render_template("patient.html", patients=patients, wards=wards, doctors=doctors, now=datetime.now)

@app.route("/patients/add", methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
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
        
        if ward_id:
            ward = conn.execute(
                "SELECT capacity, occupied FROM wards WHERE id = ?", (ward_id,)
            ).fetchone()
            if ward and ward['occupied'] >= ward['capacity']:
                conn.close()
                return jsonify({
                    'success': False,
                    'error': f'Ward is full (capacity {ward["capacity"]}). Cannot admit new patient.'
                }), 400
        
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
    wards = conn.execute("SELECT id, name, gender_type, capacity, occupied FROM wards WHERE status='active'").fetchall()
    doctors = conn.execute("SELECT id, name FROM doctors WHERE on_duty=1").fetchall()
    conn.close()
    return render_template("add-patient.html", wards=wards, doctors=doctors, now=datetime.now)

@app.route("/patients/<int:patient_id>")
@login_required
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
@login_required
def team_patient_page_redirect():
    return redirect(url_for("teams_page"))

@app.route("/team/<int:team_id>")
@login_required
def team_detail(team_id):
    conn = get_db_connection()
    team = conn.execute("SELECT * FROM teams WHERE id = ?", (team_id,)).fetchone()
    if not team:
        conn.close()
        return redirect(url_for("teams_page"))

    members = conn.execute("""
        SELECT id, name, grade, on_duty, pager
        FROM doctors
        WHERE team_id = ?
        ORDER BY name
    """, (team_id,)).fetchall()

    patients = conn.execute("""
        SELECT p.*, d.name as doctor_name, w.name as ward_name
        FROM patients p
        LEFT JOIN doctors d ON p.doctor_id = d.id
        LEFT JOIN wards w ON p.ward_id = w.id
        WHERE d.team_id = ?
        ORDER BY p.admission_datetime DESC
    """, (team_id,)).fetchall()

    today = date.today()
    processed_patients = []
    new_today_count = 0
    total_active_los_days = 0
    active_patient_count = 0

    for p in patients:
        admit_dt = datetime.fromisoformat(p['admission_datetime'])
        admit_date_str = admit_dt.strftime("%d %b %Y")
        if p['status'] == 'Discharged' and p['discharged_at']:
            end_dt = datetime.fromisoformat(p['discharged_at'])
            los_days = (end_dt - admit_dt).days
            los_str = f"{los_days} days" if los_days != 1 else "1 day"
        else:
            los_days = (datetime.now() - admit_dt).days
            los_str = f"{los_days} days" if los_days != 1 else "1 day"
            total_active_los_days += los_days
            active_patient_count += 1

        if admit_dt.date() == today:
            new_today_count += 1

        processed_patients.append({
            'id': p['id'],
            'name': p['name'],
            'age': p['age'],
            'gender': p['gender'],
            'ward_name': p['ward_name'] or 'Unknown',
            'bed': p['bed'],
            'diagnosis': p['diagnosis'],
            'admission_date': admit_date_str,
            'length_of_stay': los_str,
            'status': p['status']
        })

    total_patients = len(processed_patients)
    avg_los = round(total_active_los_days / active_patient_count, 1) if active_patient_count > 0 else 0

    ward_counts = {}
    for p in processed_patients:
        ward = p['ward_name']
        ward_counts[ward] = ward_counts.get(ward, 0) + 1
    primary_ward = max(ward_counts, key=ward_counts.get) if ward_counts else "Various"

    on_call_status = any(m['on_duty'] for m in members)
    team_pager = members[0]['pager'] if members and members[0]['pager'] else "Not assigned"

    lead_consultant = team['lead']
    if not lead_consultant:
        consultant = conn.execute("""
            SELECT name FROM doctors
            WHERE team_id = ? AND grade LIKE '%Consultant%'
            LIMIT 1
        """, (team_id,)).fetchone()
        lead_consultant = consultant['name'] if consultant else "TBD"

    conn.close()

    return render_template(
        "team-patients.html",
        team=team,
        members=members,
        patients=processed_patients,
        on_call_status=on_call_status,
        total_patients=total_patients,
        new_today=new_today_count,
        ready_for_discharge=0,
        avg_los=avg_los,
        primary_ward=primary_ward,
        team_pager=team_pager,
        lead_consultant=lead_consultant
    )

@app.route("/reports")
def reports_page():
    stats = get_dashboard_stats()
    return render_template("reports.html", stats=stats)

@app.route("/reports/generate")
def generate_report():
    # Admin-only check
    if session.get('role') != 'admin':
        return jsonify({"error": "Unauthorized"}), 403

    conn = get_db_connection()
    patients = conn.execute('''
        SELECT p.id, p.name, p.age, p.gender, p.diagnosis, p.status, p.admission_datetime, w.name as ward_name
        FROM patients p
        LEFT JOIN wards w ON p.ward_id = w.id
    ''').fetchall()
    conn.close()

    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Patient ID', 'Name', 'Age', 'Gender', 'Ward', 'Diagnosis', 'Status', 'Admission Date'])
    
    for p in patients:
        cw.writerow([
            f"P{p['id']:03d}", p['name'], p['age'], p['gender'], 
            p['ward_name'], p['diagnosis'], p['status'], p['admission_datetime']
        ])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename=hospital_report_{date.today()}.csv"
    output.headers["Content-type"] = "text/csv"
    
    log_activity("report_generation", "patients", None, "Admin generated a full patient CSV report")
    return output

@app.route("/notifications")
@login_required
def notifications_page():
    return render_template("notifications.html")

@app.route("/profile")
@login_required
def profile_page():
    conn = get_db_connection()
    user = conn.execute(
        "SELECT email, role FROM users WHERE id = ?", (session["user_id"],)
    ).fetchone()
    conn.close()
    return render_template("profile-security.html", email=user["email"], role=user["role"])

@app.route("/manage-doctors")
@login_required
@role_required(['admin'])
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

@app.route("/static/<path:path>")
def serve_static(path):
    return send_from_directory("static", path)

@app.route("/api/live/stats")
@login_required
def live_stats():
    conn = get_db_connection()
    today_str = date.today().isoformat()
    admissions_today = conn.execute(
        "SELECT COUNT(*) FROM activity_log WHERE action_type = 'admission' AND date(timestamp) = ?",
        (today_str,)
    ).fetchone()[0]
    discharges_today = conn.execute(
        "SELECT COUNT(*) FROM activity_log WHERE action_type = 'discharge' AND date(timestamp) = ?",
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
@login_required
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
@login_required
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
@login_required
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
@login_required
@role_required(['admin'])
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
@login_required
@role_required(['admin'])
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

@app.route("/api/doctors/<int:doctor_id>", methods=["DELETE"])
@login_required
@role_required(['admin'])
def delete_doctor(doctor_id):
    conn = get_db_connection()
    
    # Check if doctor is assigned to any active patients
    patient_count = conn.execute(
        "SELECT COUNT(*) FROM patients WHERE doctor_id = ? AND status = 'Active'",
        (doctor_id,)
    ).fetchone()[0]
    
    if patient_count > 0:
        conn.close()
        return jsonify({
            "error": f"Cannot delete doctor: they are the responsible clinician for {patient_count} active patient(s)."
        }), 400
    
    # Optional: also check for patients in any status (Discharged as well) – decide
    # We'll also prevent deletion if doctor is lead consultant of a ward? Not necessary.
    
    # Get doctor name for logging
    doctor = conn.execute("SELECT name FROM doctors WHERE id = ?", (doctor_id,)).fetchone()
    if not doctor:
        conn.close()
        return jsonify({"error": "Doctor not found"}), 404
    
    # Delete the doctor
    conn.execute("DELETE FROM doctors WHERE id = ?", (doctor_id,))
    conn.commit()
    conn.close()
    
    log_activity('delete', 'doctors', doctor_id, f"Doctor deleted: {doctor['name']}")
    return jsonify({"success": True})

@app.route("/api/teams/list")
@login_required
def list_teams():
    conn = get_db_connection()
    teams = conn.execute("SELECT id, name FROM teams ORDER BY name").fetchall()
    conn.close()
    return jsonify([dict(team) for team in teams])

@app.route("/api/wards/list")
@login_required
def list_wards():
    conn = get_db_connection()
    wards = conn.execute("SELECT id, name FROM wards WHERE status='active' ORDER BY name").fetchall()
    conn.close()
    return jsonify([dict(ward) for ward in wards])

@app.route("/api/wards", methods=["POST"])
@login_required
@role_required(['admin'])
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
@login_required
@role_required(['admin'])
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
@login_required
@role_required(['admin'])
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
@login_required
@role_required(['admin'])
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

def get_default_doctor_for_ward(ward_id):
    conn = get_db_connection()
    ward = conn.execute("SELECT lead_consultant FROM wards WHERE id = ?", (ward_id,)).fetchone()
    if ward and ward['lead_consultant']:
        doc = conn.execute(
            "SELECT id FROM doctors WHERE name LIKE ? AND ward_id = ? LIMIT 1",
            (f"%{ward['lead_consultant']}%", ward_id)
        ).fetchone()
        if doc:
            conn.close()
            return doc['id']
    doc = conn.execute(
        "SELECT id FROM doctors WHERE ward_id = ? AND on_duty = 1 LIMIT 1",
        (ward_id,)
    ).fetchone()
    conn.close()
    return doc['id'] if doc else None

@app.route("/api/patients/<int:patient_id>/discharge", methods=["POST"])
@login_required
@role_required(['admin'])
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

    log_activity('discharge', 'patients', patient_id,
                 f"{patient['name']} ({patient['age']}{patient['gender'][0]}) permanently deleted from system")

    if patient["ward_id"]:
        conn.execute("UPDATE wards SET occupied = occupied - 1 WHERE id = ?", (patient["ward_id"],))

    conn.execute("DELETE FROM treatments WHERE patient_id = ?", (patient_id,))
    conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))

    conn.commit()
    conn.close()

    return jsonify({'success': True}), 200

@app.route("/api/patients/<int:patient_id>/transfer", methods=["POST"])
@login_required
@role_required(['admin'])
def transfer_patient(patient_id):
    data = request.form
    new_ward_id = data.get("new_ward_id")
    reason = data.get("reason", "")
    
    conn = get_db_connection()
    patient = conn.execute(
        "SELECT p.name, p.age, p.gender, p.ward_id, p.bed, p.doctor_id FROM patients p WHERE p.id = ?",
        (patient_id,)
    ).fetchone()
    
    if not patient:
        conn.close()
        return jsonify({'error': 'Patient not found'}), 404
    
    target_ward = conn.execute("SELECT gender_type, name FROM wards WHERE id = ?", (new_ward_id,)).fetchone()
    if target_ward and target_ward['gender_type'] != 'Mixed' and target_ward['gender_type'] != patient['gender']:
        conn.close()
        return jsonify({'error': 'Gender mismatch: patient cannot be transferred to this ward'}), 400
    
    old_ward_id = patient["ward_id"]
    old_doctor_id = patient["doctor_id"]
    
    if old_ward_id:
        conn.execute("UPDATE wards SET occupied = occupied - 1 WHERE id = ?", (old_ward_id,))
    conn.execute("UPDATE wards SET occupied = occupied + 1 WHERE id = ?", (new_ward_id,))
    
    new_doctor_id = get_default_doctor_for_ward(new_ward_id)
    
    conn.execute(
        "UPDATE patients SET ward_id = ?, doctor_id = ? WHERE id = ?",
        (new_ward_id, new_doctor_id, patient_id)
    )
    
    new_ward_name = target_ward['name']
    old_doctor_name = conn.execute("SELECT name FROM doctors WHERE id = ?", (old_doctor_id,)).fetchone()
    old_doctor_name = old_doctor_name['name'] if old_doctor_name else "Unknown"
    new_doctor_name = conn.execute("SELECT name FROM doctors WHERE id = ?", (new_doctor_id,)).fetchone()
    new_doctor_name = new_doctor_name['name'] if new_doctor_name else "Unassigned"
    
    conn.commit()
    conn.close()
    
    description = (
        f"{patient['name']} ({patient['age']}{patient['gender'][0]}) transferred from "
        f"ward {old_ward_id or 'Unknown'} to {new_ward_name}. "
        f"Doctor changed from {old_doctor_name} to {new_doctor_name}. Reason: {reason}"
    )
    log_activity('transfer', 'patients', patient_id, description)
    
    return jsonify({'success': True, 'new_doctor_id': new_doctor_id}), 200

if __name__ == "__main__":
    app.run(debug=True, port=5000)
