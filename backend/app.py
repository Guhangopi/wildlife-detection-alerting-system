from flask import Flask, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
import datetime
from datetime import timezone, timedelta
from dotenv import load_dotenv

load_dotenv(override=True)

app = Flask(__name__)
CORS(app)

# Database Configuration
# START: Database Config
database_url = os.environ.get('DATABASE_URL')
if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Replace with your actual database credentials
    DB_USER = "postgres"
    DB_PASS = "Guhan@123" # Default password, user might need to change this
    DB_HOST = "localhost"
    DB_PORT = "5432"
    DB_NAME = "animal_detection_db"
    
    from urllib.parse import quote_plus
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{DB_USER}:{quote_plus(DB_PASS)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# END: Database Config

# Configure IST Timezone
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

def get_ist_now():
    return datetime.datetime.now(IST)

db = SQLAlchemy(app)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    mobile_number = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='user') # user, admin

    def __init__(self, name, mobile_number, password, role='user'):
        self.name = name
        self.mobile_number = mobile_number
        self.password = password
        self.role = role

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'mobile_number': self.mobile_number,
            'role': self.role
        }

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    image_url = db.Column(db.String(200)) # Path to image
    species = db.Column(db.String(50))
    distance = db.Column(db.Float)
    alert_level = db.Column(db.String(20), default='Info') # Info, Warning, Emergency
    timestamp = db.Column(db.DateTime, default=get_ist_now)

    def __init__(self, location, description, image_url=None, species=None, distance=None, alert_level='Info'):
        self.location = location
        self.description = description
        self.image_url = image_url
        self.species = species
        self.distance = distance
        self.alert_level = alert_level

    def to_dict(self):
        return {
            'id': self.id,
            'location': self.location,
            'description': self.description,
            'image_url': self.image_url,
            'species': self.species,
            'distance': self.distance,
            'alert_level': self.alert_level,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

# Routes
@app.route('/')
def hello():
    return jsonify({"message": "Animal Detection API is running!"})

@app.route('/init-db')
def init_db():
    try:
        db.drop_all()
        db.create_all()
        return jsonify({"message": "Database tables dropped and recreated successfully!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/uploads/<filename>')
def serve_image(filename):
    return send_from_directory('uploads', filename)

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    mobile = data.get('mobile_number')
    password = data.get('password')
    # SECURITY FIX: Force all public registrations to be 'user' only.
    # Admin accounts cannot be created via this public API.
    role = 'user' 

    if not name or not mobile or not password:
        return jsonify({"error": "Name, Mobile Number, and Password are required"}), 400

    existing_user = User.query.filter_by(mobile_number=mobile).first()
    if existing_user:
        return jsonify({"error": "User already exists with this mobile number"}), 400

    new_user = User(name=name, mobile_number=mobile, password=password, role=role)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Registration successful", "user": new_user.to_dict()}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    mobile = data.get('mobile_number', '').strip()
    password = data.get('password', '').strip()
    role = data.get('role', 'user').strip()

    if not mobile or not password:
        return jsonify({"error": "Mobile number and password are required"}), 400
    
    user = User.query.filter_by(mobile_number=mobile).first()
    
    if not user or user.password != password or user.role != role:
        return jsonify({"error": "Invalid mobile number, password, or role selector"}), 401
    
    return jsonify({"message": "Logged in", "user": user.to_dict()}), 200

@app.route('/api/alerts', methods=['GET', 'POST'])
def handle_alerts():
    if request.method == 'POST':
        data = request.json
        location = data.get('location')
        description = data.get('description')
        image_url = data.get('image_url') # Optional

        if not location or not description:
             return jsonify({"error": "Location and description are required"}), 400
        
        image_data = data.get('image_data')
        image_url = data.get('image_url')

        if image_data:
            try:
                # Save base64 image
                import base64
                import uuid
                
                # Create uploads folder if not exists
                if not os.path.exists('uploads'):
                    os.makedirs('uploads')

                filename = f"{uuid.uuid4()}.jpg"
                filepath = os.path.join('uploads', filename)
                
                with open(filepath, "wb") as fh:
                    fh.write(base64.b64decode(image_data))
                
                # URL to access the image (needs a route to serve static files)
                image_url = f"{request.host_url}uploads/{filename}"
            except Exception as e:
                print(f"Error saving image: {e}")

        new_alert = Alert(location=location, description=description, image_url=image_url)
        db.session.add(new_alert)
        db.session.commit()

        # Simulate sending notifications
        users = User.query.all()
        print(f"--- NOTIFICATION SYSTEM ---")
        print(f"Alert: {description} at {location}")
        for user in users:
            print(f"Sending SMS to {user.name} ({user.mobile_number}): 'URGENT: Wild animal detected at {location}. Stay safe!'")
        print(f"---------------------------")

        return jsonify({"message": "Alert created and notifications sent", "alert": new_alert.to_dict()}), 201

    alerts = Alert.query.order_by(Alert.timestamp.desc()).all()
    return jsonify([alert.to_dict() for alert in alerts])

@app.route('/api/alerts/<int:alert_id>', methods=['PUT', 'DELETE'])
def update_delete_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    
    if request.method == 'DELETE':
        db.session.delete(alert)
        db.session.commit()
        return jsonify({"message": "Alert deleted successfully"})
        
    if request.method == 'PUT':
        data = request.json
        if 'description' in data:
            alert.description = data['description']
        if 'location' in data:
            alert.location = data['location']
        if 'alert_level' in data:
            alert.alert_level = data['alert_level']
        if 'species' in data:
            alert.species = data['species']
            
        db.session.commit()
        return jsonify({"message": "Alert updated successfully", "alert": alert.to_dict()})

    return jsonify({"error": "Method not allowed"}), 405

@app.route('/api/iot/alert', methods=['POST'])
def handle_iot_alert():
    data = request.json
    location = data.get('location')
    description = data.get('description')
    species = data.get('species')
    distance = data.get('distance', 0)
    image_data = data.get('image_data')

    if not location or not description:
        return jsonify({"error": "Location and description are required"}), 400
    
    # Calculate Alert Level based on Geofencing (Distance)
    if distance <= 50:
        alert_level = "Emergency"
    elif distance <= 200:
        alert_level = "Warning"
    else:
        alert_level = "Info"

    image_url = None
    if image_data:
        try:
            import base64
            import uuid
            
            if not os.path.exists('uploads'):
                os.makedirs('uploads')

            filename = f"iot_{uuid.uuid4()}.jpg"
            filepath = os.path.join('uploads', filename)
            
            with open(filepath, "wb") as fh:
                fh.write(base64.b64decode(image_data))
            
            image_url = f"{request.host_url}uploads/{filename}"
        except Exception as e:
            print(f"Error saving image: {e}")

    new_alert = Alert(
        location=location, 
        description=description, 
        image_url=image_url,
        species=species,
        distance=distance,
        alert_level=alert_level
    )
    db.session.add(new_alert)
    db.session.commit()

    # Communication Layer: Real Twilio SMS Integration
    users = User.query.all()
    
    # Telegram Credentials
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

    # Twilio WhatsApp Credentials
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_WHATSAPP_NUMBER = os.environ.get('TWILIO_WHATSAPP_NUMBER')
    
    message_body = f"🚨 {alert_level.upper()} ALERT 🚨\nSpecies: {species}\nLocation: {location}\nDistance: approx {distance}m\nStay safe!"

    print(f"\n--- 🔴 LIVE ALERT SYSTEM TRIGGERED ---")
    print(f"[{alert_level.upper()}] {species} detected at {location} ({distance}m away)")
    if alert_level == "Emergency":
        print(">>>>> TRIGGERING LOCAL SIREN/STROBE LIGHT <<<<<")
        
    # Send to Telegram (Optional Image fallback)
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        try:
            import requests as req
            if image_data:
                import base64
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
                img_bytes = base64.b64decode(image_data)
                files = {'photo': ('alert.jpg', img_bytes, 'image/jpeg')}
                data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': message_body}
                response = req.post(url, data=data, files=files)
            else:
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                response = req.post(url, json={'chat_id': TELEGRAM_CHAT_ID, 'text': message_body})
            
            if response.status_code == 200:
                print(f"✅ Telegram Alert Sent successfully!")
            else:
                print(f"❌ Failed to send Telegram Alert. Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            print(f"❌ Failed to send Telegram Alert (Exception): {e}")
    else:
        print(f"⚠️ TELEGRAM CREDENTIALS NOT SET! To enable, set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        
    # Send to Twilio WhatsApp
    if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_WHATSAPP_NUMBER:
        try:
            from twilio.rest import Client
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            for user in users:
                # Basic formatting: ensure +91 prefix for Indian numbers
                user_phone = user.mobile_number if user.mobile_number.startswith("+") else "+91" + user.mobile_number
                
                # Format for WhatsApp
                from_whatsapp = f"whatsapp:{TWILIO_WHATSAPP_NUMBER}"
                to_whatsapp = f"whatsapp:{user_phone}"
                
                message = client.messages.create(
                    body=message_body,
                    from_=from_whatsapp,
                    to=to_whatsapp
                )
                print(f"✅ WhatsApp Alert Sent to {user.name} ({to_whatsapp}), SID: {message.sid}")
        except Exception as e:
            print(f"❌ Failed to send Twilio WhatsApp message: {e}")
    else:
        print(f"⚠️ TWILIO CREDENTIALS NOT SET! Skipping WhatsApp dispatch.")

    # Simulation fallback
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID) and not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN):
        for user in users:
            print(f"Simulated Push Notification to {user.name} ({user.mobile_number}): '{message_body}'")
            
    print(f"--------------------------------------------------\n")

    return jsonify({"message": "IoT Alert processed and notifications sent", "alert": new_alert.to_dict()}), 201

@app.route('/api/hotzones', methods=['GET'])
def get_hotzones():
    from sqlalchemy import func
    # Group by location and get count
    hotzones_data = db.session.query(
        getattr(Alert, 'location'), 
        func.count(getattr(Alert, 'id')).label('incident_count')
    ).group_by(getattr(Alert, 'location')).order_by(func.count(getattr(Alert, 'id')).desc()).limit(10).all()
    
    result = [{"location": loc, "incident_count": count} for loc, count in hotzones_data]
    return jsonify(result)

@app.route('/api/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@app.route('/api/users/<int:user_id>', methods=['PUT', 'DELETE'])
def handle_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'DELETE':
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": "User deleted successfully"}), 200
        
    if request.method == 'PUT':
        data = request.json
        if 'name' in data:
            user.name = data['name']
        if 'password' in data and data['password']:
            user.password = data['password']
            
        db.session.commit()
        return jsonify({"message": "User updated successfully", "user": user.to_dict()}), 200

    return jsonify({"error": "Method not allowed"}), 405

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    mobile = data.get('mobile_number')
    new_password = data.get('new_password')
    
    if not mobile or not new_password:
        return jsonify({"error": "Mobile number and new password are required"}), 400
        
    user = User.query.filter_by(mobile_number=mobile).first()
    if not user:
        return jsonify({"error": "No account found with this mobile number"}), 404
        
    user.password = new_password
    db.session.commit()
    return jsonify({"message": "Password reset successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
