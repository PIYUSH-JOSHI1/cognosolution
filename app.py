from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import os
import csv
import json
from datetime import datetime
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = app.config.get('SECRET_KEY', 'learning-disability-support-platform-2024')

from blueprints.doctor.routes import bp_doctor
# Create necessary directories
def create_directories():
    directories = [
        'data/users',
        'data/progress',
        'data/dyslexia',
        'data/dyscalculia', 
        'data/dysgraphia',
        'data/dyspraxia',
        'data/ai_models',
        'static/uploads',
        'static/user_data'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

create_directories()

# Import all modules
from modules.auth import auth_bp
from modules.dyslexia import dyslexia_bp
from modules.dyscalculia import dyscalculia_bp
from modules.dysgraphia import dysgraphia_bp
from modules.dyspraxia import dyspraxia_bp
from modules.dashboard import dashboard_bp

# Register blueprints

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(dyslexia_bp, url_prefix='/dyslexia')
app.register_blueprint(dyscalculia_bp, url_prefix='/dyscalculia')
app.register_blueprint(dysgraphia_bp, url_prefix='/dysgraphia')
app.register_blueprint(dyspraxia_bp, url_prefix='/dyspraxia')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(bp_doctor, url_prefix='/doctor')

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard.main'))
    return render_template('index.html')

# Add the resources route here
from flask import render_template

@app.route('/resources')
def resources():
    if 'user_id' not in session:
        return redirect('/auth/login')
    return render_template('resources.html')

@app.route('/live-consultation')
def live_consultation():
    if 'user_id' not in session:
        return redirect('/auth/login')
    
    # Define consultation schedules
    consultation_schedules = {
        'morning': {
            'time': '9:00 AM - 11:00 AM',
            'slots': ['9:00 AM', '9:30 AM', '10:00 AM', '10:30 AM'],
            'available_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        },
        'afternoon': {
            'time': '2:00 PM - 4:00 PM', 
            'slots': ['2:00 PM', '2:30 PM', '3:00 PM', '3:30 PM'],
            'available_days': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        }
    }
    
    # Available doctors - Updated with real doctors
    doctors = [
        {
            'id': 1,
            'name': 'Dr. Pravin Ambekar',
            'specialization': 'Child Psychologist, MS',
            'email': 'dr.pravin.ambekar@cognosolutions.com',
            'whatsapp': '+918149491825',
            'experience': '7+ years',
            'rating': 4.9,
            'qualification': 'Dr. D. Y. Patil Medical College, Hospital & Research Centre, Pune',
            'image': url_for('static', filename='images/doctors/dr-pravin-ambekar.jpg')
        },
        {
            'id': 2,
            'name': 'Dr. Kiran Advane',
            'specialization': 'Psychologist',
            'email': 'dr.kiran.advane@cognosolutions.com',
            'whatsapp': '+917744921020',
            'experience': '5+ years',
            'rating': 4.8,
            'qualification': 'Joshi Hospital & Man Arogya Kendra, Shirdi',
            'image': url_for('static', filename='images/doctors/dr-kiran-advane.jpg')
        },
        {
            'id': 3,
            'name': 'Amruta Bansode',
            'specialization': "Master's of Psychology, P.G.Diploma in Counselling",
            'email': 'amruta.bansode@cognosolutions.com',
            'whatsapp': '+917588322214',
            'experience': '3+ years',
            'rating': 4.9,
            'qualification': 'Dr. D. Y. Patil Medical College, Hospital & Research Centre, Pune',
            'image': url_for('static', filename='images/doctors/amruta-bansode.jpg')
        }
    ]
    
    return render_template('live_consultation.html', schedules=consultation_schedules, doctors=doctors)

@app.route('/start-consultation/<slot_time>')
def start_consultation(slot_time):
    if 'user_id' not in session:
        return redirect('/auth/login')
    
    # Generate unique room ID for the consultation
    room_id = f"consultation_{session['user_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Get selected doctor from session or default
    selected_doctor = session.get('selected_doctor', {
        'name': 'Dr. Pravin Ambekar',
        'email': 'dr.pravin.ambekar@cognosolutions.com',
        'whatsapp': '+917588322212'
    })
    
    return render_template('video_consultation.html', 
                         room_id=room_id, 
                         slot_time=slot_time, 
                         doctor=selected_doctor)

@app.route('/send-consultation-invite', methods=['POST'])
def send_consultation_invite():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    try:
        data = request.json
        doctor_email = data.get('doctor_email')
        doctor_name = data.get('doctor_name')
        slot_time = data.get('slot_time')
        room_id = data.get('room_id')
        patient_name = session.get('username', 'Patient')
        
        # Email configuration (you should move these to environment variables)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = "piyushaundhekar@gmail.com"
        sender_password = "your_app_password"  # Use app password for Gmail
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = doctor_email
        msg['Subject'] = f"Video Consultation Invitation - {slot_time}"
        
        # Email body
        body = f"""
        Dear {doctor_name},
        
        You have been requested for a video consultation by patient: {patient_name}
        
        Consultation Details:
        - Time: {slot_time}
        - Patient: {patient_name}
        - Room ID: {room_id}
        
        Meeting Link: {request.url_root}start-consultation/{slot_time}?room={room_id}
        
        Please join the meeting at the scheduled time.
        
        Best regards,
        Cogno Solutions Team
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, doctor_email, text)
        server.quit()
        
        return jsonify({'success': True, 'message': 'Invitation sent successfully'})
        
    except Exception as e:
        print(f"Email error: {e}")
        return jsonify({'success': False, 'message': 'Failed to send invitation'})

@app.route('/select-doctor', methods=['POST'])
def select_doctor():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    try:
        data = request.json
        session['selected_doctor'] = {
            'id': data.get('doctor_id'),
            'name': data.get('doctor_name'),
            'email': data.get('doctor_email'),
            'whatsapp': data.get('doctor_whatsapp'),
            'specialization': data.get('doctor_specialization')
        }
        
        return jsonify({'success': True, 'message': 'Doctor selected successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': 'Failed to select doctor'})

# Add SEO and production routes
@app.route('/sitemap.xml')
def sitemap():
    """Generate sitemap for SEO"""
    from flask import Response
    
    sitemap_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>{}</loc>
        <lastmod>{}</lastmod>
        <changefreq>daily</changefreq>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>{}/auth/login</loc>
        <lastmod>{}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>{}/resources</loc>
        <lastmod>{}</lastmod>
        <changefreq>weekly</changefreq>
        <priority>0.7</priority>
    </url>
</urlset>'''.format(
        request.url_root.rstrip('/'),
        datetime.now().strftime('%Y-%m-%d'),
        request.url_root.rstrip('/'),
        datetime.now().strftime('%Y-%m-%d'),
        request.url_root.rstrip('/'),
        datetime.now().strftime('%Y-%m-%d')
    )
    
    return Response(sitemap_xml, mimetype='application/xml')

@app.route('/robots.txt')
def robots():
    """Serve robots.txt for SEO"""
    robots_txt = '''User-agent: *
Allow: /
Disallow: /data/
Disallow: /static/user_data/

Sitemap: {}/sitemap.xml'''.format(request.url_root.rstrip('/'))
    
    return Response(robots_txt, mimetype='text/plain')

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Cogno Solution'
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = app.config.get('DEBUG', False)
    app.run(debug=debug, host='0.0.0.0', port=port)
