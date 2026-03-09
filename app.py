import csv
import io
from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "nuvehire_secret_key"

# ---------- DATABASE ----------
def get_db():
    conn = sqlite3.connect("nuvehire.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------- INIT DB ----------
def init_db():
    db = get_db()
    cur = db.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT,
        option_a TEXT,
        option_b TEXT,
        option_c TEXT,
        option_d TEXT,
        correct TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        question_id INTEGER,
        selected TEXT
    )""")

    db.commit()
    db.close()

# ---------- LOGIN ----------
@app.route('/', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM users WHERE email=?", (request.form['email'],))
        user = cur.fetchone()
        db.close()

        if user and check_password_hash(user['password'], request.form['password']):
            session['user_id'] = user['id']
            session['q_index'] = 0
            return redirect('/dashboard')

    return render_template('login.html')

# ---------- REGISTER ----------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        db = get_db()
        cur = db.cursor()
        cur.execute(
            "INSERT INTO users(name,email,password) VALUES(?,?,?)",
            (
                request.form['name'],
                request.form['email'],
                generate_password_hash(request.form['password'])
            )
        )
        db.commit()
        db.close()
        return redirect('/')

    return render_template('register.html')

# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# ---------- TEST ----------
@app.route('/test', methods=['GET','POST'])
def test():
    if 'user_id' not in session:
        return redirect('/')

    db = get_db()
    cur = db.cursor()
    questions = cur.execute("SELECT * FROM questions").fetchall()

    index = session.get('q_index', 0)

    if request.method == 'POST':
        selected = request.form.get('option')
        cur.execute(
            "INSERT INTO answers(user_id,question_id,selected) VALUES(?,?,?)",
            (session['user_id'], questions[index]['id'], selected)
        )
        db.commit()
        index += 1
        session['q_index'] = index

    if index >= len(questions):
        db.close()
        return redirect('/result')

    question = questions[index]
    db.close()

    return render_template('test.html', q=question, index=index+1, total=len(questions))

# ---------- RESULT ----------
@app.route('/result')
def result():
    db = get_db()
    cur = db.cursor()
    score = cur.execute("""
        SELECT COUNT(*)
        FROM answers a
        JOIN questions q ON a.question_id=q.id
        WHERE a.selected=q.correct
        AND a.user_id=?
    """, (session['user_id'],)).fetchone()[0]

    db.close()
    return render_template('result.html', score=score)

ADMIN_EMAIL = "rishav.kumar7557@gmail.com"

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if 'user_id' not in session:
        return redirect('/')

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT email FROM users WHERE id=?", (session['user_id'],))
    user = cur.fetchone()
    db.close()

    if not user or user['email'] != ADMIN_EMAIL:
        return "Access Denied", 403

    # ---------- CSV UPLOAD ----------
    if request.method == 'POST' and 'upload_csv' in request.form:
        if 'csv_file' not in request.files:
            return "No file part in request", 400

        file = request.files['csv_file']

        if file.filename == '':
            return "No file selected", 400

        if not file.filename.endswith('.csv'):
            return "Invalid file format", 400

        import csv, io
        stream = io.StringIO(file.stream.read().decode("UTF8"))
        reader = csv.DictReader(stream)

        db = get_db()
        cur = db.cursor()

        count = 0
        for row in reader:
            cur.execute("""
                INSERT INTO questions
                (question, option_a, option_b, option_c, option_d, correct)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                row['question'],
                row['option_a'],
                row['option_b'],
                row['option_c'],
                row['option_d'],
                row['correct'].strip().upper()
            ))
            count += 1

        db.commit()
        db.close()

        return f"{count} questions uploaded successfully"

    # ---------- MANUAL ADD ----------
    if request.method == 'POST' and 'add_manual' in request.form:
        db = get_db()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO questions
            (question, option_a, option_b, option_c, option_d, correct)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            request.form['question'],
            request.form['a'],
            request.form['b'],
            request.form['c'],
            request.form['d'],
            request.form['correct'].strip().upper()
        ))
        db.commit()
        db.close()

    return render_template('admin.html')


    # ---- CSV UPLOAD ----
    if request.method == 'POST' and 'csv_file' in request.files:
        file = request.files['csv_file']
        if file.filename.endswith('.csv'):
            stream = io.StringIO(file.stream.read().decode("UTF8"))
            reader = csv.DictReader(stream)

            db = get_db()
            cur = db.cursor()

            for row in reader:
                cur.execute("""
                    INSERT INTO questions
                    (question,option_a,option_b,option_c,option_d,correct)
                    VALUES (?,?,?,?,?,?)
                """, (
                    row['question'],
                    row['option_a'],
                    row['option_b'],
                    row['option_c'],
                    row['option_d'],
                    row['correct'].strip().upper()
                ))

            db.commit()
            db.close()

    # ---- MANUAL ADD ----
    elif request.method == 'POST':
        db = get_db()
        cur = db.cursor()
        cur.execute("""
            INSERT INTO questions
            (question,option_a,option_b,option_c,option_d,correct)
            VALUES (?,?,?,?,?,?)
        """, (
            request.form['question'],
            request.form['a'],
            request.form['b'],
            request.form['c'],
            request.form['d'],
            request.form['correct'].strip().upper()
        ))
        db.commit()
        db.close()

    return render_template('admin.html')


# ---------- START ----------
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
