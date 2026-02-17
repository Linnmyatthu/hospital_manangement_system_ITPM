from flask import Flask, render_template, send_from_directory, request, redirect, url_for, jsonify
import os
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Change this in production

# Ensure instance folder exists
try:
    os.makedirs(app.instance_path, exist_ok=True)
except OSError:
    pass

# Database path in instance folder
DATABASE_PATH = os.path.join(app.instance_path, 'hospital.db')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database with tables"""
    print(f"Creating database at: {DATABASE_PATH}")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables
    create_tables(cursor)
    conn.commit()
    
    # Create admin user
    create_admin_user(cursor)
    conn.commit()
    
    conn.close()
    print("Database initialized successfully!")

def create_tables(cursor):
    """Create all database tables"""
    cursor.executescript('''
        -- Wards table
        CREATE TABLE IF NOT EXISTS wards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT,
            type TEXT,
            capacity INTEGER NOT NULL,
            occupied INTEGER DEFAULT 0,
            lead_consultant TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Teams table
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialty TEXT NOT NULL,
            members INTEGER DEFAULT 0,
            lead TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Doctors table
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            specialty TEXT NOT NULL,
            on_duty BOOLEAN DEFAULT 1,
            team_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (team_id) REFERENCES teams (id)
        );
        
        -- Patients table
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            age INTEGER,
            gender TEXT,
            ward_id INTEGER,
            doctor_id INTEGER,
            admission_date DATE,
            status TEXT DEFAULT 'Admitted',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ward_id) REFERENCES wards (id),
            FOREIGN KEY (doctor_id) REFERENCES doctors (id)
        );
        
        -- Treatments table
        CREATE TABLE IF NOT EXISTS treatments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER,
            treatment TEXT NOT NULL,
            date DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients (id)
        );
        
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

def create_admin_user(cursor):
    """Create default admin user if it doesn't exist"""
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                      ('admin', 'admin123', 'admin'))
        print("Admin user created successfully!")
    else:
        print("Admin user already exists")

# Initialize database when app starts
init_db()

# Helper function to get stats for dashboard
def get_dashboard_stats():
    conn = get_db_connection()
    
    # Get counts with error handling for empty tables
    active_wards = conn.execute("SELECT COUNT(*) FROM wards WHERE status='active'").fetchone()[0]
    total_teams = conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
    treatments_today = conn.execute("SELECT COUNT(*) FROM treatments WHERE date = date('now')").fetchone()[0]
    doctors_on_duty = conn.execute("SELECT COUNT(*) FROM doctors WHERE on_duty=1").fetchone()[0]
    total_patients = conn.execute("SELECT COUNT(*) FROM patients WHERE status='Admitted'").fetchone()[0]
    
    conn.close()
    
    return {
        'active_wards': active_wards,
        'total_teams': total_teams,
        'treatments_today': treatments_today,
        'doctors_on_duty': doctors_on_duty,
        'total_patients': total_patients
    }

# Routes for rendering pages
@app.route('/')
def home():
    """Home page / Dashboard"""
    stats = get_dashboard_stats()
    return render_template('index.html', stats=stats)

@app.route('/wards')
def wards_page():
    """Wards page"""
    conn = get_db_connection()
    
    # Make sure we're selecting all fields including id
    wards = conn.execute('''
        SELECT id, name, code, type, capacity, occupied, lead_consultant, status
        FROM wards 
        ORDER BY name
    ''').fetchall()
    
    # Debug: Print ward data to console
    print("\n=== WARDS DATA ===")
    for ward in wards:
        print(f"ID: {ward['id']}, Name: {ward['name']}, Code: {ward['code']}, Type: {ward['type']}")
    print("==================\n")
    
    # Get ward stats for summary cards
    total_wards = len(wards)
    
    # Calculate average occupancy
    total_occupancy = 0
    valid_wards = 0
    critical_wards = 0
    
    for ward in wards:
        if ward['capacity'] > 0:
            occupancy = (ward['occupied'] / ward['capacity']) * 100
            total_occupancy += occupancy
            valid_wards += 1
            if occupancy >= 90:
                critical_wards += 1
    
    avg_occupancy = round(total_occupancy / valid_wards) if valid_wards > 0 else 0
    
    ward_stats = {
        'total_wards': total_wards,
        'avg_occupancy': avg_occupancy,
        'critical_wards': critical_wards
    }
    
    conn.close()
    
    return render_template('wards.html', wards=wards, stats=ward_stats)

@app.route('/ward')
def ward_overview_page():
    """Ward overview page (default view)"""
    return render_template('ward.html')

@app.route('/ward/<int:ward_id>')
def ward_detail_page(ward_id):
    """Individual ward detail page"""
    conn = get_db_connection()
    ward = conn.execute("SELECT * FROM wards WHERE id = ?", (ward_id,)).fetchone()
    
    # If ward doesn't exist, redirect to wards list
    if ward is None:
        conn.close()
        return redirect(url_for('wards_page'))
    
    patients = conn.execute("SELECT * FROM patients WHERE ward_id = ?", (ward_id,)).fetchall()
    conn.close()
    return render_template('ward.html', ward=ward, patients=patients)

@app.route('/teams')
def teams_page():
    """Teams page"""
    conn = get_db_connection()
    teams = conn.execute("SELECT * FROM teams ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template('teams.html', teams=teams)

@app.route('/patients')
def patients_page():
    """Patients page"""
    conn = get_db_connection()
    patients = conn.execute('''
        SELECT p.*, w.name as ward_name, d.name as doctor_name 
        FROM patients p
        LEFT JOIN wards w ON p.ward_id = w.id
        LEFT JOIN doctors d ON p.doctor_id = d.id
        ORDER BY p.created_at DESC
    ''').fetchall()
    conn.close()
    return render_template('patient.html', patients=patients)

@app.route('/patients-detail')
def patients_detail_page():
    """Patients page"""
    return render_template('patient-detail.html')

@app.route('/team-patients')
def team_patient_page():
    return render_template('team-patients.html')

@app.route('/treatments')
def treatments_page():
    """Treatments page"""
    conn = get_db_connection()
    treatments = conn.execute('''
        SELECT t.*, p.name as patient_name 
        FROM treatments t
        LEFT JOIN patients p ON t.patient_id = p.id
        ORDER BY t.date DESC
    ''').fetchall()
    patients = conn.execute("SELECT id, name FROM patients WHERE status='Admitted'").fetchall()
    conn.close()
    return render_template('record-treatment.html', treatments=treatments, patients=patients)

@app.route('/reports')
def reports_page():
    """Reports page"""
    stats = get_dashboard_stats()
    return render_template('reports.html', stats=stats)

@app.route('/notifications')
def notifications_page():
    """Notifications page"""
    return render_template('notifications.html')

@app.route('/profile')
def profile_page():
    """Profile page"""
    return render_template('profile-security.html')

@app.route('/manage-doctors')
def doctors_page():
    """Doctors page"""
    return render_template('manage-doctors.html')

@app.route('/live')
def live_page():
    """Live activity page"""
    return render_template('live-activity.html')

# API Routes for data operations
@app.route('/api/wards', methods=['POST'])
def add_ward():
    """Add new ward"""
    data = request.form
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO wards (name, code, type, capacity, occupied, lead_consultant, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (data['name'], data.get('code', ''), data.get('type', 'General'), 
         data['capacity'], data.get('occupied', 0), data.get('lead_consultant', ''), 
         data.get('status', 'active'))
    )
    conn.commit()
    conn.close()
    return redirect(url_for('wards_page'))

@app.route('/api/wards/<int:ward_id>', methods=['POST'])
def update_ward(ward_id):
    """Update ward"""
    data = request.form
    conn = get_db_connection()
    conn.execute(
        "UPDATE wards SET name=?, code=?, type=?, capacity=?, occupied=?, lead_consultant=?, status=? WHERE id=?",
        (data['name'], data.get('code', ''), data.get('type', 'General'), 
         data['capacity'], data['occupied'], data.get('lead_consultant', ''), 
         data.get('status', 'active'), ward_id)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('wards_page'))

@app.route('/api/wards/<int:ward_id>/delete', methods=['POST'])
def delete_ward(ward_id):
    """Delete ward"""
    conn = get_db_connection()
    conn.execute("DELETE FROM wards WHERE id=?", (ward_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('wards_page'))

@app.route('/api/teams', methods=['POST'])
def add_team():
    """Add new team"""
    data = request.form
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO teams (name, specialty, members, lead) VALUES (?, ?, ?, ?)",
        (data['name'], data['specialty'], data.get('members', 0), data.get('lead', ''))
    )
    conn.commit()
    conn.close()
    return redirect(url_for('teams_page'))

@app.route('/api/patients', methods=['POST'])
def add_patient():
    """Add new patient"""
    data = request.form
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Insert patient
    cursor.execute(
        """INSERT INTO patients (name, age, gender, ward_id, doctor_id, admission_date, status) 
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (data['name'], data['age'], data['gender'], data.get('ward_id'), 
         data.get('doctor_id'), data.get('admission_date', datetime.now().strftime('%Y-%m-%d')), 
         data.get('status', 'Admitted'))
    )
    
    # Update ward occupancy
    if data.get('ward_id'):
        cursor.execute("UPDATE wards SET occupied = occupied + 1 WHERE id = ?", (data['ward_id'],))
    
    conn.commit()
    conn.close()
    return redirect(url_for('patients_page'))

@app.route('/api/treatments', methods=['POST'])
def add_treatment():
    """Add new treatment"""
    data = request.form
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO treatments (patient_id, treatment, date, notes) VALUES (?, ?, ?, ?)",
        (data['patient_id'], data['treatment'], data.get('date', datetime.now().strftime('%Y-%m-%d')), 
         data.get('notes', ''))
    )
    conn.commit()
    conn.close()
    return redirect(url_for('treatments_page'))

@app.route('/api/doctors', methods=['POST'])
def add_doctor():
    """Add new doctor"""
    data = request.form
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO doctors (name, specialty, on_duty, team_id) VALUES (?, ?, ?, ?)",
        (data['name'], data['specialty'], data.get('on_duty', 1), data.get('team_id'))
    )
    conn.commit()
    conn.close()
    return redirect(url_for('doctors_page'))

@app.route('/api/doctors/<int:doctor_id>/toggle-duty', methods=['POST'])
def toggle_doctor_duty(doctor_id):
    """Toggle doctor on/off duty"""
    conn = get_db_connection()
    doctor = conn.execute("SELECT on_duty FROM doctors WHERE id=?", (doctor_id,)).fetchone()
    new_status = 0 if doctor['on_duty'] == 1 else 1
    conn.execute("UPDATE doctors SET on_duty=? WHERE id=?", (new_status, doctor_id))
    conn.commit()
    conn.close()
    return redirect(url_for('doctors_page'))

@app.route('/api/patients/<int:patient_id>/discharge', methods=['POST'])
def discharge_patient(patient_id):
    """Discharge patient"""
    conn = get_db_connection()
    
    # Get patient's ward before discharge
    patient = conn.execute("SELECT ward_id FROM patients WHERE id=?", (patient_id,)).fetchone()
    
    # Update patient status
    conn.execute("UPDATE patients SET status='Discharged' WHERE id=?", (patient_id,))
    
    # Update ward occupancy
    if patient and patient['ward_id']:
        conn.execute("UPDATE wards SET occupied = occupied - 1 WHERE id = ?", (patient['ward_id'],))
    
    conn.commit()
    conn.close()
    return redirect(url_for('patients_page'))

@app.route('/api/patients/<int:patient_id>/transfer', methods=['POST'])
def transfer_patient(patient_id):
    """Transfer patient to another ward"""
    data = request.form
    new_ward_id = data.get('new_ward_id')
    
    conn = get_db_connection()
    
    # Get current ward
    patient = conn.execute("SELECT ward_id FROM patients WHERE id=?", (patient_id,)).fetchone()
    
    if patient and patient['ward_id']:
        # Decrease old ward occupancy
        conn.execute("UPDATE wards SET occupied = occupied - 1 WHERE id = ?", (patient['ward_id'],))
    
    # Update patient's ward
    conn.execute("UPDATE patients SET ward_id=? WHERE id=?", (new_ward_id, patient_id))
    
    # Increase new ward occupancy
    conn.execute("UPDATE wards SET occupied = occupied + 1 WHERE id = ?", (new_ward_id,))
    
    conn.commit()
    conn.close()
    return redirect(url_for('patients_page'))

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True, port=5000)