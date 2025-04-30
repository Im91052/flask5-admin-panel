from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from werkzeug.utils import secure_filename
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def init_db():
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS admin (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        password TEXT NOT NULL
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT,
                        email TEXT,
                        status TEXT DEFAULT 'active'
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        amount REAL,
                        type TEXT,
                        status TEXT,
                        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        logo TEXT,
                        headline TEXT,
                        bio TEXT
                    )''')
        conn.commit()

@app.route('/')
def index():
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT logo, headline, bio FROM settings ORDER BY id DESC LIMIT 1")
        settings = c.fetchone()
    return render_template('index.html', settings=settings)

@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect('database.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM admin WHERE username = ? AND password = ?", (username, password))
            admin = c.fetchone()
            if admin:
                session['admin'] = username
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid credentials')
    return render_template('login.html')

@app.route('/admin/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM users")
        users = c.fetchall()
        c.execute("SELECT * FROM transactions ORDER BY date DESC")
        transactions = c.fetchall()
    return render_template('dashboard.html', users=users, transactions=transactions)

@app.route('/admin/block_user/<int:user_id>')
def block_user(user_id):
    if 'admin' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET status='blocked' WHERE id=?", (user_id,))
        conn.commit()
    return redirect(url_for('dashboard'))

@app.route('/admin/update_settings', methods=['POST'])
def update_settings():
    if 'admin' not in session:
        return redirect(url_for('login'))
    logo_file = request.files['logo']
    headline = request.form['headline']
    bio = request.form['bio']
    logo_path = None
    if logo_file:
        filename = secure_filename(logo_file.filename)
        logo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        logo_file.save(logo_path)
    with sqlite3.connect('database.db') as conn:
        c = conn.cursor()
        c.execute("INSERT INTO settings (logo, headline, bio) VALUES (?, ?, ?)", (logo_path, headline, bio))
        conn.commit()
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
