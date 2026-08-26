from flask import Flask, request, jsonify, send_from_directory
import sqlite3
import os

app = Flask(__name__, static_folder='.', static_url_path='')

DB_FILE = 'database.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Tabella Utenti Centralizzata per tutti i dispositivi
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS utenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            ruolo TEXT NOT NULL
        )
    ''')
    # Creazione Admin predefinito se non esiste
    cursor.execute("SELECT * FROM utenti WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO utenti (username, password, ruolo) VALUES ('admin', 'admin123', 'admin')")
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# API Login Online
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT username, ruolo FROM utenti WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return jsonify({"success": True, "username": user[0], "ruolo": user[1]})
    return jsonify({"success": False, "message": "Credenziali errate"}), 401

# API Ottieni Elenco Utenti per Amministratore
@app.route('/api/utenti', methods=['GET'])
def get_utenti():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT username, ruolo FROM utenti")
    utenti = [{"username": row[0], "ruolo": row[1]} for row in cursor.fetchall()]
    conn.close()
    return jsonify({"success": True, "utenti": utenti})

# API Crea/Modifica Password Utente su DB Online
@app.route('/api/utenti/salva', methods=['POST'])
def salva_utente():
    data = request.json or {}
    username = data.get('username')
    password = data.get('password')
    ruolo = data.get('ruolo', 'operatore')
    
    if not username or not password:
        return jsonify({"success": False, "message": "Username e Password richiesti"}), 400

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM utenti WHERE username = ?", (username,))
    exists = cursor.fetchone()
    
    if exists:
        cursor.execute("UPDATE utenti SET password = ?, ruolo = ? WHERE username = ?", (password, ruolo, username))
        msg = f"Password dell'utente '{username}' aggiornata sul Database Online!"
    else:
        cursor.execute("INSERT INTO utenti (username, password, ruolo) VALUES (?, ?, ?)", (username, password, ruolo))
        msg = f"Utente '{username}' creato con successo sul Database Online!"
        
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": msg})

# API Elimina Utente
@app.route('/api/utenti/elimina', methods=['POST'])
def elimina_utente():
    data = request.json or {}
    username = data.get('username')
    if username == 'admin':
        return jsonify({"success": False, "message": "Impossibile eliminare l'Admin principale"}), 400
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM utenti WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Utente rimosso dal DB Online!"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
