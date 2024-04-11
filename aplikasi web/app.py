from flask import Flask, render_template, request, jsonify, send_from_directory, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_migrate import Migrate
from alembic import op
from flask import redirect, url_for
import sqlalchemy as sa
import secrets
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///devices.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.config['UPLOAD_FOLDER'] = 'media'
app.config['ALLOWED_EXTENSIONS'] = {'bin'}

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mac_address = db.Column(db.String(17), unique=True, nullable=False)
    label = db.Column(db.String(100))

class FirmwareHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('device.id'), nullable=False)
    firmware_version = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    device = db.relationship('Device', backref=db.backref('firmware_history', lazy=True))

media_dir = 'media'
if not os.path.exists(media_dir):
    os.makedirs(media_dir)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register_device():
    mac_address = request.form.get('mac_address')
    label = request.form.get('label')

    if mac_address:
        new_device = Device(mac_address=mac_address, label=label)
        db.session.add(new_device)
        db.session.commit()
        return f"Device with MAC address {mac_address} registered with label '{label}'"
    else:
        return "Invalid request"

@app.route('/update', methods=['GET'])
def update_firmware():
    if len(request.args) > 1 or 'mac_address' not in request.args:
        return jsonify({'error': 'Invalid request parameters'}), 400

    mac_address_param = request.args.get('mac_address')

    if mac_address_param:
        device = Device.query.filter_by(mac_address=mac_address_param).first()

        if device:
            latest_firmware_entry = FirmwareHistory.query.filter_by(device_id=device.id).order_by(FirmwareHistory.timestamp.desc()).first()

            if latest_firmware_entry:
                sanitized_mac_address = device.mac_address.replace(':', '_')
                filename = f"{sanitized_mac_address}_{latest_firmware_entry.firmware_version}"
                firmware_url = url_for('uploaded_file', filename=filename, _external=True)

                response = {'version': latest_firmware_entry.firmware_version, 'url': firmware_url}
                return jsonify(response)
            else:
                return jsonify('No firmware history available'), 404
        else:
            return jsonify({'error': 'Unauthorized Device'}), 401
    else:
        return jsonify({'error': 'Invalid request'}), 400

@app.route('/devices')
def list_devices():
    devices = Device.query.all()
    return render_template('devices.html', devices=devices)

@app.route('/delete', methods=['POST'])
def delete_device():
    mac_address = request.form.get('mac_address')

    if mac_address:
        device_to_delete = Device.query.filter_by(mac_address=mac_address).first()

        if device_to_delete:
            db.session.delete(device_to_delete)
            db.session.commit()
            return redirect(url_for('list_devices'))
        else:
            return "Device not found"
    else:
        return "Invalid request"

@app.route('/upload', methods=['POST'])
def upload_firmware():
    mac_address = request.form.get('mac_address')

    if 'firmware' in request.files:
        firmware_file = request.files['firmware']

        if firmware_file.filename != '':
            version = extract_version_from_filename(firmware_file.filename)

            if version is not None:
                device = Device.query.filter_by(mac_address=mac_address).first()

                if device:
                    history_entry = FirmwareHistory(device_id=device.id, firmware_version=firmware_file.filename)
                    db.session.add(history_entry)
                    db.session.commit()

                    sanitized_mac_address = mac_address.replace(':', '_')
                    firmware_file.save(os.path.join(app.config['UPLOAD_FOLDER'], f'{sanitized_mac_address}_{firmware_file.filename}'))

                    return f"Firmware uploaded for device with MAC address {mac_address} and version {version}"
                else:
                    return "Device not found"
            else:
                return "Invalid firmware version in filename"
        else:
            return "No firmware file uploaded"
    else:
        return "Invalid request"

def extract_version_from_filename(filename):
    start_index = filename.find('_') + 1
    end_index = filename.find('.bin')
    version_str = filename[start_index:end_index]

    try:
        version = int(version_str)
        return version
    except ValueError:
        return None

@app.route('/history', methods=['GET', 'POST'])
def firmware_history():
    mac_address = request.form.get('mac_address') or request.args.get('mac_address')

    if mac_address:
        device = Device.query.filter_by(mac_address=mac_address).first()

        if device:
            # Mengurutkan entri firmware berdasarkan timestamp secara descending
            history_entries = FirmwareHistory.query.filter_by(device_id=device.id).order_by(FirmwareHistory.timestamp.desc()).all()
            return render_template('history.html', device=device, history_entries=history_entries, extract_version_from_filename=extract_version_from_filename)
        else:
            return "Device not registered"
    else:
        return "Invalid request"

@app.route('/delete_history', methods=['POST'])
def delete_history_entry():
    entry_id = request.form.get('entry_id')
    mac_address = request.form.get('mac_address')

    if entry_id and mac_address:
        history_entry = FirmwareHistory.query.get(entry_id)

        if history_entry:
            sanitized_mac_address = mac_address.replace(':', '_')
            filename = f"{sanitized_mac_address}_{history_entry.firmware_version}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            if os.path.exists(file_path):
                os.remove(file_path)

            db.session.delete(history_entry)
            db.session.commit()
        else:
            return "History entry not found"

    return redirect(url_for('firmware_history', mac_address=mac_address))

@app.route('/media/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(host='0.0.0.0', port=5000, debug=True)