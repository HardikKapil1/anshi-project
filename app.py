from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# Configure from environment for production safety
app.secret_key = os.environ.get('SECRET_KEY', 'dev-insecure-change-me')
app.config['UPLOAD_FOLDER'] = os.environ.get(
    'UPLOAD_FOLDER',
    os.path.join(os.getcwd(), 'uploads')
)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db():
    db_path = os.environ.get('DATABASE_PATH', os.path.join(os.getcwd(), 'campus_hub.db'))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # Students table
    c.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT,
            password_hash TEXT NOT NULL
        )
    ''')
    
    # Items table (lost and found)
    c.execute('''
        CREATE TABLE IF NOT EXISTS items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            category TEXT,
            description TEXT,
            date TEXT,
            location TEXT,
            photo_path TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    ''')
    
    # Events table
    c.execute('''
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            venue TEXT NOT NULL,
            description TEXT,
            created_by INTEGER,
            FOREIGN KEY (created_by) REFERENCES students(student_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

@app.context_processor
def inject_events():
    """Make events available to all templates"""
    try:
        conn = get_db()
        events = conn.execute('SELECT * FROM events ORDER BY date').fetchall()
        conn.close()
        return dict(events=events)
    except Exception as e:
        print(f"Error loading events: {e}")
        return dict(events=[])

@app.route('/')
def index():
    q = request.args.get('q', '').strip()
    item_type = request.args.get('type', '').strip()
    
    conn = get_db()
    query = 'SELECT * FROM items WHERE status = "active"'
    params = []
    
    if q:
        query += ' AND (title LIKE ? OR location LIKE ? OR category LIKE ?)'
        params.extend([f'%{q}%', f'%{q}%', f'%{q}%'])
    
    if item_type:
        query += ' AND type = ?'
        params.append(item_type)
    
    query += ' ORDER BY created_at DESC'
    items = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template('index.html', items=items)

@app.route('/events')
def events():
    conn = get_db()
    events = conn.execute('SELECT * FROM events ORDER BY date').fetchall()
    conn.close()
    return render_template('events.html', events=events)

@app.route('/add-event', methods=['GET', 'POST'])
def add_event():
    if 'user_id' not in session:
        flash('Please login to add events', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        date = request.form['date']
        venue = request.form['venue']
        description = request.form.get('description', '')
        
        conn = get_db()
        conn.execute(
            'INSERT INTO events (title, date, venue, description, created_by) VALUES (?, ?, ?, ?, ?)',
            (title, date, venue, description, session['user_id'])
        )
        conn.commit()
        conn.close()
        
        flash('Event added successfully!', 'success')
        return redirect(url_for('events'))
    
    return render_template('add_event.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db()
        user = conn.execute('SELECT * FROM students WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['student_id']
            session['user_name'] = user['name']
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone = request.form.get('phone', '')
        password = request.form['password']
        
        conn = get_db()
        existing = conn.execute('SELECT * FROM students WHERE email = ?', (email,)).fetchone()
        
        if existing:
            flash('Email already registered', 'danger')
            conn.close()
            return redirect(url_for('register'))
        
        password_hash = generate_password_hash(password)
        conn.execute(
            'INSERT INTO students (name, email, phone, password_hash) VALUES (?, ?, ?, ?)',
            (name, email, phone, password_hash)
        )
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please login', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))

@app.route('/add-item', methods=['GET', 'POST'])
def add_item():
    if 'user_id' not in session:
        flash('Please login to add items', 'danger')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        item_type = request.form['type']
        title = request.form['title']
        category = request.form.get('category', '')
        description = request.form.get('description', '')
        date = request.form.get('date', '')
        location = request.form.get('location', '')
        
        photo_path = None
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename:
                filename = secure_filename(photo.filename)
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                photo.save(photo_path)
        
        conn = get_db()
        conn.execute(
            '''INSERT INTO items (student_id, type, title, category, description, date, location, photo_path)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
            (session['user_id'], item_type, title, category, description, date, location, photo_path)
        )
        conn.commit()
        conn.close()
        
        flash('Item added successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add_item.html')

@app.route('/item/<int:item_id>')
def item_detail(item_id):
    conn = get_db()
    item = conn.execute('SELECT * FROM items WHERE item_id = ?', (item_id,)).fetchone()
    conn.close()
    
    if not item:
        flash('Item not found', 'danger')
        return redirect(url_for('index'))
    
    return render_template('item_detail.html', item=item)

@app.route('/item/<int:item_id>/change-status', methods=['POST'])
def change_status(item_id):
    if 'user_id' not in session:
        flash('Please login', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db()
    item = conn.execute('SELECT * FROM items WHERE item_id = ?', (item_id,)).fetchone()
    
    if item and item['student_id'] == session['user_id']:
        conn.execute('UPDATE items SET status = "resolved" WHERE item_id = ?', (item_id,))
        conn.commit()
        flash('Item marked as resolved', 'success')
    
    conn.close()
    return redirect(url_for('index'))

@app.route('/contact', methods=['POST'])
def contact():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'})
    
    data = request.get_json()
    item_id = data.get('item_id')
    message = data.get('message')
    
    # In a real app, you would send email/SMS here
    # For now, just return success
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
