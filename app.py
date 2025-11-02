from flask import Flask, render_template, request, redirect, url_for, session, flash
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'classrep-secret-key-2024'

# Database setup
def init_db():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            port=os.getenv('DB_PORT')
        )
        cursor = conn.cursor()

        # Create tables if not exist (PostgreSQL syntax)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id SERIAL PRIMARY KEY,
                roll_number VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                class_name VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id SERIAL PRIMARY KEY,
                student_id INTEGER REFERENCES students(id),
                date DATE NOT NULL,
                status VARCHAR(50) NOT NULL,
                notes TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS behavior (
                id SERIAL PRIMARY KEY,
                student_id INTEGER REFERENCES students(id),
                date DATE NOT NULL,
                incident_type VARCHAR(255) NOT NULL,
                description TEXT NOT NULL,
                action_taken TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS academics (
                id SERIAL PRIMARY KEY,
                student_id INTEGER REFERENCES students(id),
                subject VARCHAR(255) NOT NULL,
                test_name VARCHAR(255) NOT NULL,
                marks INTEGER NOT NULL,
                total_marks INTEGER NOT NULL,
                date DATE NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id SERIAL PRIMARY KEY,
                student_id INTEGER REFERENCES students(id),
                activity_name VARCHAR(255) NOT NULL,
                participation_type VARCHAR(255) NOT NULL,
                date DATE NOT NULL,
                remarks TEXT
            )
        ''')

        # Insert sample students if none exist
        cursor.execute("SELECT COUNT(*) FROM students")
        if cursor.fetchone()[0] == 0:
            sample_students = [
                ('CR001', 'John Doe', 'Class 10A'),
                ('CR002', 'Jane Smith', 'Class 10A'),
                ('CR003', 'Mike Johnson', 'Class 10A'),
                ('CR004', 'Sarah Williams', 'Class 10A'),
                ('CR005', 'David Brown', 'Class 10A')
            ]
            cursor.executemany(
                "INSERT INTO students (roll_number, name, class_name) VALUES (%s, %s, %s)",
                sample_students
            )

        conn.commit()
        cursor.close()
        conn.close()
    except psycopg2.Error as err:
        print(f"Database initialization error: {err}")
    except Exception as e:
        print(f"Unexpected error during DB init: {e}")

# Helper function to get database connection
def get_db():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            port=os.getenv('DB_PORT')
        )
        return conn
    except psycopg2.Error as err:
        print(f"Error: {err}")
        return None

# Helper function to get a cursor with dictionary=True
def get_dict_cursor(conn):
    return conn.cursor(cursor_factory=RealDictCursor)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Hardcoded credentials for simplicity
        if username == 'classrep' and password == 'password123':
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    if conn is None:
        flash('Database connection failed!')
        return redirect(url_for('login'))

    cursor = get_dict_cursor(conn)

    # Get counts
    cursor.execute("SELECT COUNT(*) as total FROM students")
    total_students = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as total FROM attendance WHERE date = CURRENT_DATE")
    today_attendance = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as total FROM behavior WHERE date >= CURRENT_DATE - INTERVAL '7 days'")
    recent_behavior = cursor.fetchone()['total']

    cursor.close()
    conn.close()

    return render_template('dashboard.html',
                         total_students=total_students,
                         today_attendance=today_attendance,
                         recent_behavior=recent_behavior)

# Students management
@app.route('/students')
def students():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    if conn is None:
        flash('Database connection failed!')
        return redirect(url_for('login'))

    cursor = get_dict_cursor(conn)
    cursor.execute("SELECT * FROM students ORDER BY roll_number")
    students = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('students.html', students=students)

@app.route('/add_student', methods=['POST'])
def add_student():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    roll_number = request.form['roll_number']
    name = request.form['name']
    class_name = request.form['class_name']

    conn = get_db()
    if conn is None:
        flash('Database connection failed!')
        return redirect(url_for('students'))

    cursor = conn.cursor()
    cursor.execute("INSERT INTO students (roll_number, name, class_name) VALUES (%s, %s, %s)",
                   (roll_number, name, class_name))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Student added successfully!')
    return redirect(url_for('students'))

@app.route('/delete_student/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    if conn is None:
        flash('Database connection failed!')
        return redirect(url_for('students'))

    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Student deleted successfully!')
    return redirect(url_for('students'))

# Attendance
@app.route('/attendance')
def attendance():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    if conn is None:
        flash('Database connection failed!')
        return redirect(url_for('login'))

    cursor = get_dict_cursor(conn)

    # Get students and attendance records
    cursor.execute("SELECT * FROM students ORDER BY roll_number")
    students = cursor.fetchall()

    cursor.execute('''
        SELECT a.*, s.name, s.roll_number
        FROM attendance a
        JOIN students s ON a.student_id = s.id
        ORDER BY a.date DESC LIMIT 20
    ''')
    attendance_records = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('attendance.html', students=students, attendance_records=attendance_records)

@app.route('/add_attendance', methods=['POST'])
def add_attendance():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    student_id = request.form['student_id']
    date = request.form['date']
    status = request.form['status']
    notes = request.form['notes']

    conn = get_db()
    if conn is None:
        flash('Database connection failed!')
        return redirect(url_for('attendance'))

    cursor = conn.cursor()
    cursor.execute("INSERT INTO attendance (student_id, date, status, notes) VALUES (%s, %s, %s, %s)",
                   (student_id, date, status, notes))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Attendance recorded successfully!')
    return redirect(url_for('attendance'))

# Behavior
@app.route('/behavior')
def behavior():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    if conn is None:
        flash('Database connection failed!')
        return redirect(url_for('login'))

    cursor = get_dict_cursor(conn)

    cursor.execute("SELECT * FROM students ORDER BY roll_number")
    students = cursor.fetchall()

    cursor.execute('''
        SELECT b.*, s.name, s.roll_number
        FROM behavior b
        JOIN students s ON b.student_id = s.id
        ORDER BY b.date DESC LIMIT 20
    ''')
    behavior_records = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('behavior.html', students=students, behavior_records=behavior_records)

@app.route('/add_behavior', methods=['POST'])
def add_behavior():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    student_id = request.form['student_id']
    date = request.form['date']
    incident_type = request.form['incident_type']
    description = request.form['description']
    action_taken = request.form['action_taken']

    conn = get_db()
    if conn is None:
        flash('Database connection failed!')
        return redirect(url_for('behavior'))

    cursor = conn.cursor()
    cursor.execute("INSERT INTO behavior (student_id, date, incident_type, description, action_taken) VALUES (%s, %s, %s, %s, %s)",
                   (student_id, date, incident_type, description, action_taken))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Behavior incident recorded successfully!')
    return redirect(url_for('behavior'))

# Academics
@app.route('/academics')
def academics():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    if conn is None:
        flash('Database connection failed!')
        return redirect(url_for('login'))

    cursor = get_dict_cursor(conn)

    cursor.execute("SELECT * FROM students ORDER BY roll_number")
    students = cursor.fetchall()

    cursor.execute('''
        SELECT a.*, s.name, s.roll_number
        FROM academics a
        JOIN students s ON a.student_id = s.id
        ORDER BY a.date DESC LIMIT 20
    ''')
    academic_records = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('academics.html', students=students, academic_records=academic_records)

@app.route('/add_academic', methods=['POST'])
def add_academic():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    student_id = request.form['student_id']
    subject = request.form['subject']
    test_name = request.form['test_name']
    marks = request.form['marks']
    total_marks = request.form['total_marks']
    date = request.form['date']

    conn = get_db()
    if conn is None:
        flash('Database connection failed!')
        return redirect(url_for('academics'))

    cursor = conn.cursor()
    cursor.execute("INSERT INTO academics (student_id, subject, test_name, marks, total_marks, date) VALUES (%s, %s, %s, %s, %s, %s)",
                   (student_id, subject, test_name, marks, total_marks, date))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Academic record added successfully!')
    return redirect(url_for('academics'))

# Activities
@app.route('/activity')
def activity():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    if conn is None:
        flash('Database connection failed!')
        return redirect(url_for('login'))

    cursor = get_dict_cursor(conn)

    cursor.execute("SELECT * FROM students ORDER BY roll_number")
    students = cursor.fetchall()

    cursor.execute('''
        SELECT a.*, s.name, s.roll_number
        FROM activities a
        JOIN students s ON a.student_id = s.id
        ORDER BY a.date DESC LIMIT 20
    ''')
    activity_records = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('activity.html', students=students, activity_records=activity_records)

@app.route('/add_activity', methods=['POST'])
def add_activity():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    student_id = request.form['student_id']
    activity_name = request.form['activity_name']
    participation_type = request.form['participation_type']
    date = request.form['date']
    remarks = request.form['remarks']

    conn = get_db()
    if conn is None:
        flash('Database connection failed!')
        return redirect(url_for('activity'))

    cursor = conn.cursor()
    cursor.execute("INSERT INTO activities (student_id, activity_name, participation_type, date, remarks) VALUES (%s, %s, %s, %s, %s)",
                   (student_id, activity_name, participation_type, date, remarks))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Activity record added successfully!')
    return redirect(url_for('activity'))

# Initialize database on app startup
init_db()

if __name__ == '__main__':
    app.run(debug=True)
