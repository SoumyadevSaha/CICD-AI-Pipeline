from flask import Flask, request, jsonify, abort
from functools import wraps
from datetime import datetime
import sqlite3
import os
from cryptography.fernet import Fernet

app = Flask(__name__)

# Hardcoded users for demo (in production, use proper user management)
USERS = {
    "admin": "secret",
    "user1": "password1"
}

# SQLite configuration
DATABASE = os.path.join(os.getcwd(), 'keys_db.sqlite')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Decorator for basic authentication
def check_auth(username, password):
    return USERS.get(username) == password

def authenticate():
    message = {'message': "Authentication required."}
    resp = jsonify(message)
    resp.status_code = 401
    return resp

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def store_key(username, key):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_keys (
                username TEXT PRIMARY KEY,
                symm_key TEXT,
                timestamp DATETIME
            )
        """)
        # Insert or update key
        cursor.execute("""
            INSERT INTO user_keys (username, symm_key, timestamp)
            VALUES (?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET symm_key = excluded.symm_key, timestamp = excluded.timestamp
        """, (username, key, datetime.utcnow()))
        conn.commit()
    except Exception as e:
        print("DB error:", e)
    finally:
        cursor.close()
        conn.close()

@app.route("/get-key", methods=["GET"])
@requires_auth
def get_key():
    auth = request.authorization
    # For demo, generate a symmetric key using Fernet.
    key = Fernet.generate_key().decode()
    # Store the key in the database corresponding to the username
    store_key(auth.username, key)
    return jsonify({"key": key})

@app.route("/upload-model", methods=["POST"])
@requires_auth
def upload_model():
    # Accepts an encrypted file and saves it to a local folder 'uploads'
    if 'file' not in request.files:
        abort(400, "No file part in the request")
    file = request.files['file']
    if file.filename == '':
        abort(400, "No file selected")
    uploads_dir = os.path.join(os.getcwd(), 'uploads')
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)
    save_path = os.path.join(uploads_dir, file.filename)
    file.save(save_path)
    return jsonify({"message": f"File saved to {save_path}"}), 200

@app.route("/decrypt", methods=["POST"])
@requires_auth
def decrypt_model():
    # This endpoint expects an encrypted file and returns the decrypted content.
    file_data = request.files.get("file")
    if not file_data:
        abort(400, "No file uploaded")
    auth = request.authorization
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT symm_key FROM user_keys WHERE username = ?", (auth.username,))
        row = cursor.fetchone()
        if not row:
            abort(400, "No key stored for this user")
        key = row["symm_key"]
    finally:
        cursor.close()
        conn.close()

    fernet = Fernet(key.encode())
    encrypted_data = file_data.read()
    try:
        decrypted = fernet.decrypt(encrypted_data)
    except Exception as e:
        abort(400, f"Decryption failed: {str(e)}")
    return decrypted

@app.route("/", methods=["GET"])
def server_status():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM user_keys")
        count = cursor.fetchone()[0]
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
    
    return jsonify({"status": "running", "entries": count}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5051, debug=True)
