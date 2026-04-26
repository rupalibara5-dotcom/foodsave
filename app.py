"""
FoodSave - Food Waste Management Web App
Backend: Python Flask + SQLite
"""

from flask import Flask, request, jsonify, render_template
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# ===== DATABASE SETUP =====
DB_PATH = os.path.join(os.path.dirname(__file__), 'foodsave.db')


def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Return rows as dicts
    return conn


def init_db():
    """Initialize the database with tables and seed data."""
    conn = get_db()
    cursor = conn.cursor()

    # Food donations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS donations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donor_name TEXT NOT NULL,
            donor_phone TEXT NOT NULL,
            food_item TEXT NOT NULL,
            quantity TEXT NOT NULL,
            category TEXT NOT NULL,
            best_before_hours INTEGER NOT NULL,
            location TEXT NOT NULL,
            notes TEXT,
            claimed INTEGER DEFAULT 0,
            claimer_name TEXT,
            claimer_phone TEXT,
            claimer_org TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Contact messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Seed with sample data if empty
    cursor.execute('SELECT COUNT(*) FROM donations')
    count = cursor.fetchone()[0]

    if count == 0:
        sample_data = [
            ('Priya Restaurant', '9876543210', 'Biryani & Dal', '15 kg', 'Cooked Meal', 4, 'Koramangala, Bangalore', 'Freshly cooked, no onion/garlic'),
            ('Amit Sharma', '9123456789', 'Mixed Vegetables', '8 kg', 'Raw Vegetables', 24, 'Indiranagar, Bangalore', 'Tomatoes, potatoes, onions'),
            ('City Bakery', '9988776655', 'Bread & Pastries', '30 pieces', 'Bakery Items', 6, 'MG Road, Bangalore', 'End of day surplus'),
            ('Sunita Devi', '9765432100', 'Apples & Bananas', '5 kg', 'Fruits', 48, 'Whitefield, Bangalore', 'Slightly overripe but good'),
            ('Hotel Grand', '9654321098', 'Paneer Curry & Rice', '25 servings', 'Cooked Meal', 3, 'Brigade Road, Bangalore', 'Wedding leftovers - very fresh'),
            ('Organic Farm', '9543210987', 'Spinach & Carrots', '10 kg', 'Raw Vegetables', 36, 'Electronic City, Bangalore', 'Organic, pesticide-free'),
        ]
        cursor.executemany('''
            INSERT INTO donations (donor_name, donor_phone, food_item, quantity, category, best_before_hours, location, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', sample_data)

    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")


# ===== ROUTES =====

@app.route('/')
def index():
    """Serve the main HTML page."""
    return render_template('index.html')


@app.route('/api/donate', methods=['POST'])
def donate():
    """Handle food donation submissions."""
    try:
        data = request.get_json()

        # Validate required fields
        required = ['donor_name', 'donor_phone', 'food_item', 'quantity', 'category', 'best_before_hours', 'location']
        for field in required:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400

        # Validate best_before_hours
        hours = int(data['best_before_hours'])
        if hours < 1 or hours > 72:
            return jsonify({'success': False, 'error': 'Best before hours must be between 1 and 72'}), 400

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO donations (donor_name, donor_phone, food_item, quantity, category, best_before_hours, location, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['donor_name'].strip(),
            data['donor_phone'].strip(),
            data['food_item'].strip(),
            data['quantity'].strip(),
            data['category'].strip(),
            hours,
            data['location'].strip(),
            data.get('notes', '').strip()
        ))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()

        return jsonify({'success': True, 'id': new_id, 'message': 'Donation listed successfully!'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/listings', methods=['GET'])
def get_listings():
    """Get all active (unclaimed) food listings."""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, donor_name, food_item, quantity, category,
                   best_before_hours, location, notes, claimed, created_at
            FROM donations
            ORDER BY claimed ASC, created_at DESC
        ''')
        rows = cursor.fetchall()
        conn.close()

        listings = [dict(row) for row in rows]
        return jsonify({'success': True, 'listings': listings})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/claim', methods=['POST'])
def claim_food():
    """Handle food claim requests."""
    try:
        data = request.get_json()

        required = ['food_id', 'claimer_name', 'claimer_phone']
        for field in required:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400

        conn = get_db()
        cursor = conn.cursor()

        # Check if already claimed
        cursor.execute('SELECT claimed FROM donations WHERE id = ?', (data['food_id'],))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return jsonify({'success': False, 'error': 'Food listing not found'}), 404

        if row['claimed']:
            conn.close()
            return jsonify({'success': False, 'error': 'This food has already been claimed'}), 409

        # Mark as claimed
        cursor.execute('''
            UPDATE donations
            SET claimed = 1, claimer_name = ?, claimer_phone = ?, claimer_org = ?
            WHERE id = ?
        ''', (
            data['claimer_name'].strip(),
            data['claimer_phone'].strip(),
            data.get('organization', '').strip(),
            data['food_id']
        ))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Food claimed successfully!'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get platform impact statistics."""
    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) as total FROM donations')
        total_donations = cursor.fetchone()['total']

        cursor.execute('SELECT COUNT(*) as claimed FROM donations WHERE claimed = 1')
        total_claimed = cursor.fetchone()['claimed']

        conn.close()

        # Estimate impact (rough calculations for demo)
        total_kg = total_donations * 4          # avg 4 kg per donation
        total_people_fed = total_donations * 8  # avg 8 people per donation
        co2_prevented = total_kg * 2            # ~2 kg CO2 per kg food saved

        return jsonify({
            'success': True,
            'total_donations': total_donations,
            'total_claimed': total_claimed,
            'total_kg': total_kg,
            'total_people_fed': total_people_fed,
            'co2_prevented': co2_prevented
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/contact', methods=['POST'])
def contact():
    """Handle contact form submissions."""
    try:
        data = request.get_json()

        required = ['name', 'email', 'message']
        for field in required:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO contacts (name, email, message)
            VALUES (?, ?, ?)
        ''', (data['name'].strip(), data['email'].strip(), data['message'].strip()))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Message received!'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ===== MAIN =====
# Initialize DB on startup always
init_db()

if __name__ == '__main__':
    print("🌿 FoodSave server starting...")
    print("🌐 Open http://localhost:5000 in your browser")
    app.run(debug=False, host='0.0.0.0', port=5000)
