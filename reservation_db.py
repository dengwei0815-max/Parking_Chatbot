import sqlite3

DB_PATH = "reservations.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reservations
                 (id TEXT PRIMARY KEY, name TEXT, car_number TEXT, period TEXT, status TEXT)''')
    conn.commit()
    conn.close()


def save_reservation(res_id, name, car_number, period, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        'INSERT OR REPLACE INTO reservations VALUES (?, ?, ?, ?, ?)',
        (res_id, name, car_number, period, status),
    )
    conn.commit()
    conn.close()


def get_reservation(res_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM reservations WHERE id=?', (res_id,))
    row = c.fetchone()
    conn.close()
    return row


def get_all_reservations():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM reservations ORDER BY rowid DESC')
    rows = c.fetchall()
    conn.close()
    return rows
