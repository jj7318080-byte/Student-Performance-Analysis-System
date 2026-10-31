from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.getenv("DB_PASSWORD"),
        database="student_performance"
    )

@app.route('/')
def home():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    # Dashboard counts
    cursor.execute("SELECT COUNT(*) AS total FROM students")
    total_students = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM subjects")
    total_subjects = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM marks")
    total_marks = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM attendance")
    total_attendance = cursor.fetchone()['total']

    cursor.execute("SELECT ROUND(AVG(total_marks), 2) AS average FROM marks")
    overall_average = cursor.fetchone()['average'] or 0

    # Subject-wise average marks
    cursor.execute("""
        SELECT sub.subject_name,
               ROUND(AVG(m.total_marks), 2) AS average_marks
        FROM subjects sub
        LEFT JOIN marks m ON sub.subject_id = m.subject_id
        GROUP BY sub.subject_id, sub.subject_name
        ORDER BY sub.subject_name
    """)
    subject_chart = cursor.fetchall()

    # Student-wise average marks
    cursor.execute("""
        SELECT s.name,
               ROUND(AVG(m.total_marks), 2) AS average_marks
        FROM students s
        LEFT JOIN marks m ON s.student_id = m.student_id
        GROUP BY s.student_id, s.name
        ORDER BY s.name
    """)
    student_chart = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'index.html',
        total_students=total_students,
        total_subjects=total_subjects,
        total_marks=total_marks,
        total_attendance=total_attendance,
        overall_average=overall_average,
        subject_chart=subject_chart,
        student_chart=student_chart
    )


# STUDENTS
@app.route('/students')
def students():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM students")
    student_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('students.html', students=student_list)


@app.route('/students/add', methods=['POST'])
def add_student():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO students
        (name, roll_number, department, year, email)
        VALUES (%s, %s, %s, %s, %s)
    """, (
        request.form['name'],
        request.form['roll_number'],
        request.form['department'],
        request.form['year'],
        request.form['email']
    ))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('students'))


# SUBJECTS
@app.route('/subjects')
def subjects():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM subjects")
    subject_list = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('subjects.html', subjects=subject_list)


@app.route('/subjects/add', methods=['POST'])
def add_subject():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO subjects
        (subject_name, subject_code, department, year)
        VALUES (%s, %s, %s, %s)
    """, (
        request.form['subject_name'],
        request.form['subject_code'],
        request.form['department'],
        request.form['year']
    ))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('subjects'))


# MARKS ENTRY
@app.route('/marks')
def marks():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT student_id, name, roll_number
        FROM students ORDER BY name
    """)
    student_list = cursor.fetchall()

    cursor.execute("""
        SELECT subject_id, subject_name, subject_code
        FROM subjects ORDER BY subject_name
    """)
    subject_list = cursor.fetchall()

    cursor.execute("""
        SELECT m.mark_id, s.name, s.roll_number, sub.subject_name,
               m.internal_marks, m.external_marks,
               m.total_marks, m.grade
        FROM marks m
        JOIN students s ON m.student_id = s.student_id
        JOIN subjects sub ON m.subject_id = sub.subject_id
        ORDER BY m.mark_id DESC
    """)
    mark_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'marks.html',
        students=student_list,
        subjects=subject_list,
        marks=mark_list
    )


@app.route('/marks/add', methods=['POST'])
def add_marks():
    student_id = request.form['student_id']
    subject_id = request.form['subject_id']
    internal_marks = int(request.form['internal_marks'])
    external_marks = int(request.form['external_marks'])

    total_marks = internal_marks + external_marks

    if total_marks >= 90:
        grade = 'A+'
    elif total_marks >= 80:
        grade = 'A'
    elif total_marks >= 70:
        grade = 'B'
    elif total_marks >= 60:
        grade = 'C'
    elif total_marks >= 50:
        grade = 'D'
    else:
        grade = 'F'

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO marks
        (student_id, subject_id, internal_marks,
         external_marks, total_marks, grade)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        student_id,
        subject_id,
        internal_marks,
        external_marks,
        total_marks,
        grade
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('marks'))
# ATTENDANCE
@app.route('/attendance')
def attendance():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT student_id, name, roll_number
        FROM students ORDER BY name
    """)
    student_list = cursor.fetchall()

    cursor.execute("""
        SELECT a.attendance_id, s.name, s.roll_number,
               a.attendance_date, a.status
        FROM attendance a
        JOIN students s ON a.student_id = s.student_id
        ORDER BY a.attendance_date DESC
    """)
    attendance_list = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'attendance.html',
        students=student_list,
        attendance=attendance_list
    )


@app.route('/attendance/add', methods=['POST'])
def add_attendance():
    student_id = request.form['student_id']
    attendance_date = request.form['attendance_date']
    status = request.form['status']

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO attendance
        (student_id, attendance_date, status)
        VALUES (%s, %s, %s)
    """, (student_id, attendance_date, status))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('attendance'))
# PERFORMANCE ANALYSIS
# PERFORMANCE ANALYSIS
@app.route('/performance')
def performance():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            s.student_id,
            s.name,
            s.roll_number,
            COUNT(m.mark_id) AS subject_count,
            SUM(m.total_marks) AS total_marks,
            ROUND(AVG(m.total_marks), 2) AS average_marks
        FROM students s
        LEFT JOIN marks m ON s.student_id = m.student_id
        GROUP BY s.student_id, s.name, s.roll_number
        ORDER BY average_marks DESC
    """)

    performance_data = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'performance.html',
        performance=performance_data
    )
# REPORTS PAGE
@app.route('/reports')
def reports():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            s.name,
            s.roll_number,
            COUNT(DISTINCT m.mark_id) AS subject_count,
            COALESCE(SUM(m.total_marks), 0) AS total_marks,
            ROUND(AVG(m.total_marks), 2) AS average_marks
        FROM students s
        LEFT JOIN marks m ON s.student_id = m.student_id
        GROUP BY s.student_id, s.name, s.roll_number
        ORDER BY s.name
    """)

    report_data = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'reports.html',
        reports=report_data
    )
# RECOMMENDATIONS PAGE
@app.route('/recommendations')
def recommendations():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            s.student_id,
            s.name,
            s.roll_number,
            COUNT(m.mark_id) AS subject_count,
            ROUND(AVG(m.total_marks), 2) AS average_marks
        FROM students s
        LEFT JOIN marks m ON s.student_id = m.student_id
        GROUP BY s.student_id, s.name, s.roll_number
        ORDER BY s.name
    """)

    recommendation_data = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        'recommendations.html',
        recommendations=recommendation_data
    )
# SETTINGS PAGE
@app.route('/settings')
def settings():
    return render_template('settings.html')


if __name__ == '__main__':
    app.run(debug=True)