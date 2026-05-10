"""
Smart Task Management System
Author: Allibad Pujitha
Stack: Flask + PostgreSQL + WebSockets + Pandas/NumPy
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_socketio import SocketIO, emit
from flask_bcrypt import Bcrypt
import psycopg2
import psycopg2.extras
import pandas as pd
import numpy as np
from datetime import datetime
import os
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY',os.urandom(24))

# AI-ASSISTED: SocketIO enables WebSocket support for real-time notifications
socketio = SocketIO(app, cors_allowed_origins="*")
bcrypt = Bcrypt(app)

# ─────────────────────────────────────────────
# DATABASE CONNECTION
# ─────────────────────────────────────────────

def get_db():
    """Connect to PostgreSQL database"""
    return psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        database=os.environ.get('DB_NAME', 'taskmanager'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'password'),
        port=os.environ.get('DB_PORT', '5432')
    )

def init_db():
    """Create tables if they don't exist"""
    conn = get_db()
    cur = conn.cursor()
    
    # Users table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            email VARCHAR(200) UNIQUE NOT NULL,
            password VARCHAR(200) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tasks table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            priority VARCHAR(20) DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high')),
            status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'in_progress', 'completed')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()

# ─────────────────────────────────────────────
# HELPER: Login required decorator
# ─────────────────────────────────────────────

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Please login first'}), 401
        return f(*args, **kwargs)
    return decorated

# ─────────────────────────────────────────────
# AUTHENTICATION ROUTES
# ─────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login_page'))
    return render_template('dashboard.html', username=session.get('username'))

@app.route('/api/register', methods=['POST'])
def register():
    """User Registration API"""
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not username or not email or not password:
        return jsonify({'error': 'All fields are required'}), 400

    # Hash password before storing — never store plain text
    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')

    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, email, password) VALUES (%s, %s, %s) RETURNING id",
            (username, email, hashed_pw)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Registration successful', 'user_id': user_id}), 201
    except psycopg2.errors.UniqueViolation:
        return jsonify({'error': 'Username or email already exists'}), 409
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """User Login API"""
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and bcrypt.check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return jsonify({'message': 'Login successful', 'username': user['username']}), 200
        return jsonify({'error': 'Invalid email or password'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout — clears session"""
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

# ─────────────────────────────────────────────
# TASK REST APIs
# ─────────────────────────────────────────────

@app.route('/api/tasks', methods=['GET'])
@login_required
def get_tasks():
    """Get all tasks for logged-in user"""
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            "SELECT * FROM tasks WHERE user_id = %s ORDER BY created_at DESC",
            (session['user_id'],)
        )
        tasks = cur.fetchall()
        cur.close()
        conn.close()
        # Convert datetime to string for JSON serialization
        task_list = []
        for task in tasks:
            t = dict(task)
            t['created_at'] = t['created_at'].strftime('%Y-%m-%d %H:%M')
            t['updated_at'] = t['updated_at'].strftime('%Y-%m-%d %H:%M')
            task_list.append(t)
        return jsonify(task_list), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks', methods=['POST'])
@login_required
def add_task():
    """Add a new task"""
    data = request.get_json()
    title = data.get('title', '').strip()
    description = data.get('description', '').strip()
    priority = data.get('priority', 'medium')
    status = data.get('status', 'pending')

    if not title:
        return jsonify({'error': 'Title is required'}), 400

    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(
            """INSERT INTO tasks (user_id, title, description, priority, status)
               VALUES (%s, %s, %s, %s, %s) RETURNING *""",
            (session['user_id'], title, description, priority, status)
        )
        task = dict(cur.fetchone())
        conn.commit()
        cur.close()
        conn.close()

        task['created_at'] = task['created_at'].strftime('%Y-%m-%d %H:%M')
        task['updated_at'] = task['updated_at'].strftime('%Y-%m-%d %H:%M')

        # AI-ASSISTED: Emit WebSocket event so all connected browsers update instantly
        socketio.emit('task_added', {'task': task, 'message': f'New task added: {title}'})

        return jsonify(task), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    """Update an existing task"""
    data = request.get_json()

    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

        # Make sure this task belongs to the logged-in user
        cur.execute("SELECT * FROM tasks WHERE id = %s AND user_id = %s", (task_id, session['user_id']))
        task = cur.fetchone()
        if not task:
            return jsonify({'error': 'Task not found'}), 404

        # Update only provided fields
        title = data.get('title', task['title'])
        description = data.get('description', task['description'])
        priority = data.get('priority', task['priority'])
        status = data.get('status', task['status'])

        cur.execute(
            """UPDATE tasks SET title=%s, description=%s, priority=%s, status=%s,
               updated_at=CURRENT_TIMESTAMP WHERE id=%s AND user_id=%s RETURNING *""",
            (title, description, priority, status, task_id, session['user_id'])
        )
        updated = dict(cur.fetchone())
        conn.commit()
        cur.close()
        conn.close()

        updated['created_at'] = updated['created_at'].strftime('%Y-%m-%d %H:%M')
        updated['updated_at'] = updated['updated_at'].strftime('%Y-%m-%d %H:%M')

        # AI-ASSISTED: Notify all clients via WebSocket about the update
        socketio.emit('task_updated', {'task': updated, 'message': f'Task updated: {title}'})

        return jsonify(updated), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    """Delete a task"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id FROM tasks WHERE id = %s AND user_id = %s", (task_id, session['user_id']))
        if not cur.fetchone():
            return jsonify({'error': 'Task not found'}), 404

        cur.execute("DELETE FROM tasks WHERE id = %s AND user_id = %s", (task_id, session['user_id']))
        conn.commit()
        cur.close()
        conn.close()

        # AI-ASSISTED: Broadcast deletion to all connected clients via WebSocket
        socketio.emit('task_deleted', {'task_id': task_id, 'message': 'Task deleted'})

        return jsonify({'message': 'Task deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────────
# ANALYTICS API — uses Pandas & NumPy
# ─────────────────────────────────────────────

@app.route('/api/analytics', methods=['GET'])
@login_required
def get_analytics():
    """
    AI-ASSISTED: Uses Pandas to load task data into a DataFrame,
    then NumPy to compute statistics like completion percentage.
    This is how data analysts work — load data, analyze, return results.
    """
    try:
        conn = get_db()
        # Load tasks directly into a Pandas DataFrame
        df = pd.read_sql(
            "SELECT * FROM tasks WHERE user_id = %s",
            conn, params=(session['user_id'],)
        )
        conn.close()

        if df.empty:
            return jsonify({
                'total_tasks': 0, 'completed': 0,
                'pending': 0, 'in_progress': 0,
                'completion_percentage': 0,
                'high_priority': 0, 'priority_breakdown': {}
            }), 200

        # NumPy and Pandas calculations
        total = len(df)
        completed = int(np.sum(df['status'] == 'completed'))      # NumPy sum
        pending = int(np.sum(df['status'] == 'pending'))          # NumPy sum
        in_progress = int(np.sum(df['status'] == 'in_progress'))  # NumPy sum
        completion_pct = round(float(np.mean(df['status'] == 'completed')) * 100, 1)  # NumPy mean
        high_priority = int(np.sum(df['priority'] == 'high'))

        # Pandas value_counts for priority breakdown
        priority_breakdown = df['priority'].value_counts().to_dict()

        return jsonify({
            'total_tasks': total,
            'completed': completed,
            'pending': pending,
            'in_progress': in_progress,
            'completion_percentage': completion_pct,
            'high_priority': high_priority,
            'priority_breakdown': priority_breakdown
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ─────────────────────────────────────────────
# WEBSOCKET EVENTS
# ─────────────────────────────────────────────

@socketio.on('connect')
def on_connect():
    # AI-ASSISTED: Called automatically when a browser opens the page
    emit('connected', {'message': 'Connected to real-time updates!'})

@socketio.on('disconnect')
def on_disconnect():
    print('Client disconnected')

# ─────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────

if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
