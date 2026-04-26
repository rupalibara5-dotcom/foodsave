
from flask import Flask, request, jsonify, render_template
import sqlite3, os

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'foodsave.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db(); c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS donations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        donor_name TEXT, donor_phone TEXT, food_item TEXT,
        quantity TEXT, category TEXT, best_before_hours INTEGER,
        location TEXT, notes TEXT, claimed INTEGER DEFAULT 0,
        claimer_name TEXT, claimer_phone TEXT, claimer_org TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, email TEXT, message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('SELECT COUNT(*) FROM donations')
    if c.fetchone()[0] == 0:
        c.executemany('INSERT INTO donations (donor_name,donor_phone,food_item,quantity,category,best_before_hours,location,notes) VALUES (?,?,?,?,?,?,?,?)', [
            ('Priya Restaurant','9876543210','Biryani & Dal','15 kg','Cooked Meal',4,'Koramangala, Bangalore','Freshly cooked'),
            ('Amit Sharma','9123456789','Mixed Vegetables','8 kg','Raw Vegetables',24,'Indiranagar, Bangalore','Tomatoes, potatoes'),
            ('City Bakery','9988776655','Bread & Pastries','30 pieces','Bakery Items',6,'MG Road, Bangalore','End of day surplus'),
            ('Hotel Grand','9654321098','Paneer Curry & Rice','25 servings','Cooked Meal',3,'Brigade Road, Bangalore','Wedding leftovers'),
            ('Sunita Devi','9765432100','Apples & Bananas','5 kg','Fruits',48,'Whitefield, Bangalore','Slightly overripe'),
            ('Organic Farm','9543210987','Spinach & Carrots','10 kg','Raw Vegetables',36,'Electronic City, Bangalore','Organic'),
        ])
    conn.commit(); conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/donate', methods=['POST'])
def donate():
    try:
        d = request.get_json()
        conn = get_db(); c = conn.cursor()
        c.execute('INSERT INTO donations (donor_name,donor_phone,food_item,quantity,category,best_before_hours,location,notes) VALUES (?,?,?,?,?,?,?,?)',
            (d['donor_name'],d['donor_phone'],d['food_item'],d['quantity'],d['category'],int(d['best_before_hours']),d['location'],d.get('notes','')))
        conn.commit(); nid = c.lastrowid; conn.close()
        return jsonify({'success': True, 'id': nid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/listings')
def listings():
    try:
        conn = get_db(); c = conn.cursor()
        c.execute('SELECT * FROM donations ORDER BY claimed ASC, created_at DESC')
        rows = [dict(r) for r in c.fetchall()]; conn.close()
        return jsonify({'success': True, 'listings': rows})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/claim', methods=['POST'])
def claim():
    try:
        d = request.get_json()
        conn = get_db(); c = conn.cursor()
        c.execute('SELECT claimed FROM donations WHERE id=?', (d['food_id'],))
        row = c.fetchone()
        if not row: conn.close(); return jsonify({'success': False, 'error': 'Not found'}), 404
        if row['claimed']: conn.close(); return jsonify({'success': False, 'error': 'Already claimed'}), 409
        c.execute('UPDATE donations SET claimed=1,claimer_name=?,claimer_phone=?,claimer_org=? WHERE id=?',
            (d['claimer_name'],d['claimer_phone'],d.get('organization',''),d['food_id']))
        conn.commit(); conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats')
def stats():
    try:
        conn = get_db(); c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM donations'); total = c.fetchone()[0]
        conn.close()
        return jsonify({'success': True, 'total_donations': total,
            'total_kg': total*4, 'total_people_fed': total*8, 'co2_prevented': total*8})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/contact', methods=['POST'])
def contact():
    try:
        d = request.get_json()
        conn = get_db(); c = conn.cursor()
        c.execute('INSERT INTO contacts (name,email,message) VALUES (?,?,?)', (d['name'],d['email'],d['message']))
        conn.commit(); conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    print('Database ready')
    print('Open http://localhost:5000')
    app.run(debug=True, host='0.0.0.0', port=5000)
