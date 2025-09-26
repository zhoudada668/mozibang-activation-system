from flask import Flask, request, jsonify
import pymysql
import os
import uuid
from datetime import datetime, timedelta

app = Flask(__name__)

# Database configuration
app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST', 'localhost')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER', 'root')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD', 'Sn730080')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB', 'mozibang')

def get_db_connection():
    return pymysql.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB'],
        cursorclass=pymysql.cursors.DictCursor
    )

@app.route('/')
def home():
    return "License Key Backend is running!"

@app.route('/generate_license', methods=['POST'])
def generate_license():
    try:
        data = request.get_json()
        expires_in_days = data.get('expires_in_days', 365) # Default to 1 year

        license_key = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(days=expires_in_days)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO licenses (license_key, expires_at) VALUES (%s, %s)",
            (license_key, expires_at)
        )
        conn.commit()
        conn.close()

        return jsonify({'license_key': license_key, 'expires_at': expires_at.isoformat()}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/verify_license', methods=['POST'])
def verify_license():
    try:
        data = request.get_json()
        license_key = data.get('license_key')

        if not license_key:
            return jsonify({'valid': False, 'message': 'License key is required.'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM licenses WHERE license_key = %s AND is_active = TRUE",
            (license_key,)
        )
        license_data = cursor.fetchone()
        conn.close()

        if license_data:
            expires_at = license_data['expires_at']
            if expires_at and expires_at < datetime.now():
                return jsonify({'valid': False, 'message': 'License key has expired.'}), 403
            else:
                return jsonify({'valid': True, 'expires_at': expires_at.isoformat() if expires_at else None}), 200
        else:
            return jsonify({'valid': False, 'message': 'Invalid or inactive license key.'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)