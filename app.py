from flask import Flask, request, jsonify, render_template
import sqlite3
import os

app = Flask(__name__, static_folder='.', static_url_path='')

DB_FILE = 'database.db'

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Tabella Utenti centralizzata
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS utenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            ruolo TEXT NOT NULL
        )
    ''')
    # Creazione utente admin predefinito se non esiste
    cursor.execute("SELECT * FROM utenti WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO utenti (username, password, ruolo) VALUES ('admin', 'admin123', 'admin')")
    
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return app.send_static_file('index.html')

# API Login Centralizzato
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT username, ruolo FROM utenti WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return jsonify({"success": True, "username": user[0], "ruolo": user[1]})
    return jsonify({"success": False, "message": "Credenziali non valide"}), 401

# API Ottieni tutti gli utenti (Admin)
@app.route('/api/utenti', methods=['GET'])
def get_utenti():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT username, ruolo FROM utenti")
    utenti = [{"username": row[0], "ruolo": row[1]} for row in cursor.fetchall()]
    conn.close()
    return jsonify({"success": True, "utenti": utenti})

# API Crea/Aggiorna Utente sul DB Online (Admin)
@app.route('/api/utenti/salva', methods=['POST'])
def salva_utente():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    ruolo = data.get('ruolo', 'operatore')
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Verifica se l'utente esiste già
    cursor.execute("SELECT id FROM utenti WHERE username = ?", (username,))
    exists = cursor.fetchone()
    
    if exists:
        # Aggiorna password e ruolo
        if password:
            cursor.execute("UPDATE utenti SET password = ?, ruolo = ? WHERE username = ?", (password, ruolo, username))
        else:
            cursor.execute("UPDATE utenti SET ruolo = ? WHERE username = ?", (ruolo, username))
    else:
        # Inserisci nuovo utente
        cursor.execute("INSERT INTO utenti (username, password, ruolo) VALUES (?, ?, ?)", (username, password, ruolo))
        
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Utente {username} salvato correttamente nel Database Online!"})

# API Elimina Utente (Admin)
@app.route('/api/utenti/elimina', methods=['POST'])
def elimina_utente():
    data = request.json
    username = data.get('username')
    if username == 'admin':
        return jsonify({"success": False, "message": "Non puoi eliminare l'amministratore principale"}), 400
        
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM utenti WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": "Utente eliminato!"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
