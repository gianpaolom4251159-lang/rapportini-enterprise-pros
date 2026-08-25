import os
import json
import sqlite3
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='.', template_folder='.')

UPLOAD_PDF_DIR = os.path.join('uploads', 'pdf')
UPLOAD_LOGO_DIR = os.path.join('uploads', 'logo')
os.makedirs(UPLOAD_PDF_DIR, exist_ok=True)
os.makedirs(UPLOAD_LOGO_DIR, exist_ok=True)

DB_NAME = "database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rapportini (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codice TEXT NOT NULL,
            data TEXT NOT NULL,
            operatore TEXT NOT NULL,
            cliente TEXT NOT NULL,
            note TEXT,
            prodotti TEXT,
            pdf_path TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/rapportini', methods=['GET'])
def get_rapportini():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, codice, data, operatore, cliente, note, prodotti, pdf_path FROM rapportini ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    rapportini = []
    for row in rows:
        rapportini.append({
            "id": row[0],
            "codice": row[1],
            "data": row[2],
            "operatore": row[3],
            "cliente": row[4],
            "note": row[5],
            "prodotti": json.loads(row[6]) if row[6] else [],
            "pdf_path": row[7]
        })
    return jsonify(rapportini)

@app.route('/api/rapportini', methods=['POST'])
def add_rapportino():
    data = request.form
    codice = data.get('codice')
    data_interv = data.get('data')
    operatore = data.get('operatore')
    cliente = data.get('cliente')
    note = data.get('note', '')
    prodotti = data.get('prodotti', '[]')
    
    pdf_file = request.files.get('pdf')
    pdf_path = ""
    if pdf_file and pdf_file.filename != '':
        filename = secure_filename(pdf_file.filename)
        pdf_path = os.path.join(UPLOAD_PDF_DIR, filename)
        pdf_file.save(pdf_path)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO rapportini (codice, data, operatore, cliente, note, prodotti, pdf_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (codice, data_interv, operatore, cliente, note, prodotti, pdf_path))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Rapportino salvato nel database.db!"})

@app.route('/uploads/pdf/<filename>')
def get_pdf(filename):
    return send_from_directory(UPLOAD_PDF_DIR, filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
