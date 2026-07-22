import os
import bcrypt
import datetime
import traceback
import uuid
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity, verify_jwt_in_request
)
from werkzeug.utils import secure_filename
from PIL import Image

# Cloudinary
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.config.from_object('config.Config')

# CORS – allow specific origins
CORS(app, origins=app.config['CORS_ORIGINS'], supports_credentials=True,
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

# Ensure upload folder exists (if you ever use local fallback)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure Cloudinary
cloudinary.config(
    cloud_name=app.config['CLOUDINARY_CLOUD_NAME'],
    api_key=app.config['CLOUDINARY_API_KEY'],
    api_secret=app.config['CLOUDINARY_API_SECRET']
)

db = SQLAlchemy(app)
jwt = JWTManager(app)

# ─── JWT Error Handlers ──────────────────────────────────
@jwt.unauthorized_loader
def unauthorized_loader(callback):
    return jsonify({'message': 'Missing or invalid token'}), 401

@jwt.invalid_token_loader
def invalid_token_loader(callback):
    return jsonify({'message': 'Invalid token'}), 401

@jwt.expired_token_loader
def expired_token_loader(jwt_header, jwt_data):
    print("💥 Token expired:", jwt_data)
    return jsonify({'message': 'Token expired'}), 401

# ─── Global Error Handler ──────────────────────────────────
@app.errorhandler(Exception)
def handle_exception(e):
    print("=" * 60)
    print("💥 GLOBAL EXCEPTION CAUGHT:")
    traceback.print_exc()
    print("=" * 60)
    return jsonify({'message': str(e)}), 500

# ─── Database Models ──────────────────────────────────────

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='customer')  # 'admin' or 'customer'
    approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'approved': self.approved,
            'createdAt': self.created_at
        }

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100))
    address = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'createdAt': self.created_at
        }

class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id', ondelete='CASCADE'), nullable=False)
    package_name = db.Column(db.String(100))
    package_price = db.Column(db.String(50))
    service_type = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, completed, cancelled
    details = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'customerId': self.customer_id,
            'packageName': self.package_name,
            'packagePrice': self.package_price,
            'serviceType': self.service_type,
            'status': self.status,
            'details': self.details,
            'createdAt': self.created_at
        }

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), default=0)
    method = db.Column(db.String(50))
    status = db.Column(db.String(20), default='unpaid')  # unpaid, paid, pending, partial
    reference = db.Column(db.String(100))
    created_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'bookingId': self.booking_id,
            'amount': float(self.amount) if self.amount else 0,
            'method': self.method,
            'status': self.status,
            'reference': self.reference,
            'createdAt': self.created_at
        }

class Gallery(db.Model):
    __tablename__ = 'gallery'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    url = db.Column(db.String(500), nullable=False)  # Cloudinary URL
    created_at = db.Column(db.TIMESTAMP, default=db.func.current_timestamp())

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'createdAt': self.created_at
        }

# ─── Custom Decorator ─────────────────────────────────────

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            user_id = int(get_jwt_identity())
            user = User.query.get(user_id)
            if not user or user.role != 'admin':
                return jsonify({'message': 'Admin access required'}), 403
            return fn(*args, **kwargs)
        except Exception as e:
            print("💥 admin_required error:", e)
            traceback.print_exc()
            return jsonify({'message': str(e)}), 500
    return wrapper

# ─── Public Test Route ──────────────────────────────────

@app.route('/api/test', methods=['GET'])
def test_db():
    try:
        customers = Customer.query.all()
        return jsonify([c.to_dict() for c in customers])
    except Exception as e:
        print("💥 test_db error:", e)
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500

# ─── Authentication Routes ────────────────────────────────

@app.route('/api/auth/register', methods=['POST', 'OPTIONS'])
def register():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Invalid JSON data'}), 400
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'customer')
        phone = data.get('phone', '')
        address = data.get('address', '')
        if not name or not email or not password:
            return jsonify({'message': 'Name, email and password required'}), 400
        if User.query.filter_by(email=email).first():
            return jsonify({'message': 'Email already registered'}), 409
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        approved = (role == 'admin')
        user = User(name=name, email=email, password=hashed.decode('utf-8'),
                    role=role, approved=approved)
        db.session.add(user)
        db.session.flush()

        if role == 'customer':
            customer = Customer(
                user_id=user.id,
                name=name,
                phone=phone,
                email=email,
                address=address
            )
            db.session.add(customer)

        db.session.commit()
        return jsonify({'message': 'Registration successful'}), 201
    except Exception as e:
        print("💥 register error:", e)
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500

@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Invalid JSON data'}), 400
        email = data.get('email')
        password = data.get('password')
        if not email or not password:
            return jsonify({'message': 'Email and password required'}), 400
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'message': 'Invalid credentials'}), 401
        try:
            if not bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
                return jsonify({'message': 'Invalid credentials'}), 401
        except ValueError:
            return jsonify({'message': 'Invalid password format'}), 400
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={'name': user.name, 'email': user.email, 'role': user.role}
        )
        return jsonify({
            'token': access_token,
            'user': user.to_dict()
        })
    except Exception as e:
        print("💥 login error:", e)
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500

# ─── Admin: User Management ──────────────────────────────

@app.route('/api/users', methods=['GET'])
@jwt_required()
@admin_required
def get_users():
    try:
        users = User.query.all()
        return jsonify([u.to_dict() for u in users])
    except Exception as e:
        print("💥 get_users error:", e)
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500

@app.route('/api/users/<int:id>/approve', methods=['PUT'])
@jwt_required()
@admin_required
def approve_user(id):
    try:
        data = request.get_json()
        approved = data.get('approved', False)
        user = User.query.get_or_404(id)
        user.approved = approved
        db.session.commit()
        return jsonify({'message': 'User approval updated'})
    except Exception as e:
        print("💥 approve_user error:", e)
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500

# ─── Customers CRUD ──────────────────────────────────────

@app.route('/api/customers', methods=['GET'])
@jwt_required()
def get_customers():
    try:
        customers = Customer.query.order_by(Customer.created_at.desc()).all()
        return jsonify([c.to_dict() for c in customers])
    except Exception as e:
        print("💥 get_customers error:", e)
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500

@app.route('/api/customers', methods=['POST'])
@jwt_required()
def create_customer():
    try:
        data = request.get_json()
        customer = Customer(
            name=data.get('name'),
            phone=data.get('phone'),
            email=data.get('email'),
            address=data.get('address')
        )
        db.session.add(customer)
        db.session.commit()
        return jsonify(customer.to_dict()), 201
    except Exception as e:
        print("💥 create_customer error:", e)
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500

@app.route('/api/customers/<int:id>', methods=['PUT'])
@jwt_required()
def update_customer(id):
    try:
        customer = Customer.query.get_or_404(id)
        data = request.get_json()
        customer.name = data.get('name', customer.name)
        customer.phone = data.get('phone', customer.phone)
        customer.email = data.get('email', customer.email)
        customer.address = data.get('address', customer.address)
        db.session.commit()
        return jsonify(customer.to_dict())
    except Exception as e:
        print("💥 update_customer error:", e)
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500

@app.route('/api/customers/<int:id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_customer(id):
    try:
        customer = Customer.query.get_or_404(id)
        db.session.delete(customer)
        db.session.commit()
        return jsonify({'message': 'Customer deleted'})
    except Exception as e:
        print("💥 delete_customer error:", e)
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500

# ─── Bookings CRUD ──────────────────────────────────────

@app.route('/api/bookings', methods=['GET'])
@jwt_required()
def get_bookings():
    try:
        user_id = int(get_jwt_identity())
        current_user = User.query.get(user_id)
        if current_user.role == 'admin':
            bookings = Booking.query.order_by(Booking.created_at.desc()).all()
        else:
            customer = Customer.query.filter_by(user_id=user_id).first()
            if customer:
                bookings = Booking.query.filter_by(customer_id=customer.id).order_by(Booking.created_at.desc()).all()
            else:
                bookings = []
        return jsonify([b.to_dict() for b in bookings])
    except Exception as e:
        print("💥 get_bookings error:", e)
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500

@app.route('/api/bookings', methods=['POST'])
@jwt_required()
def create_booking():
    try:
        data = request.get_json()
        customer = None
        if 'customerId' in data:
            customer = Customer.query.get(data['customerId'])
        elif 'customer' in data:
            cust_data = data['customer']
            customer = Customer.query.filter_by(phone=cust_data.get('phone')).first()
            if not customer:
                customer = Customer(
                    name=cust_data.get('name'),
                    phone=cust_data.get('phone'),
                    email=cust_data.get('email'),
                    address=cust_data.get('address')
                )
                db.session.add(customer)
                db.session.flush()
        if not customer:
            return jsonify({'message': 'Customer not found'}), 404
        booking = Booking(
            customer_id=customer.id,
            package_name=data.get('packageName', 'Custom Request'),
            package_price=data.get('packagePrice', 'Quote on Request'),
            service_type=data.get('serviceType', 'solar'),
            status=data.get('status', 'pending'),
            details=data.get('details', '')
        )
        db.session.add(booking)
        db.session.commit()
        return jsonify(booking.to_dict()), 201
    except Exception as e:
        print("💥 create_booking error:", e)
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500

@app.route('/api/bookings/<int:id>', methods=['PUT'])
@jwt_required()
def update_booking(id):
    try:
        booking = Booking.query.get_or_404(id)
        data = request.get_json()
        booking.customer_id = data.get('customerId', booking.customer_id)
        booking.package_name = data.get('packageName', booking.package_name)
        booking.package_price = data.get('packagePrice', booking.package_price)
        booking.service_type = data.get('serviceType', booking.service_type)
        booking.status = data.get('status', booking.status)
        booking.details = data.get('details', booking.details)
        db.session.commit()
        return jsonify(booking.to_dict())
    except Exception as e:
        print("💥 update_booking error:", e)
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500

@app.route('/api/bookings/<int:id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_booking(id):
    try:
        booking = Booking.query.get_or_404(id)
        db.session.delete(booking)
        db.session.commit()
        return jsonify({'message': 'Booking deleted'})
    except Exception as e:
        print("💥 delete_booking error:", e)
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500

# ─── Payments CRUD ──────────────────────────────────────

@app.route('/api/payments', methods=['GET'])
@jwt_required()
def get_payments():
    try:
        payments = Payment.query.order_by(Payment.created_at.desc()).all()
        return jsonify([p.to_dict() for p in payments])
    except Exception as e:
        print("💥 get_payments error:", e)
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500

@app.route('/api/payments', methods=['POST'])
@jwt_required()
def create_payment():
    try:
        data = request.get_json()
        payment = Payment(
            booking_id=data.get('bookingId'),
            amount=data.get('amount', 0),
            method=data.get('method', 'Pending'),
            status=data.get('status', 'unpaid'),
            reference=data.get('reference', f"REF-{uuid.uuid4().hex[:6].upper()}")
        )
        db.session.add(payment)
        db.session.commit()
        return jsonify(payment.to_dict()), 201
    except Exception as e:
        print("💥 create_payment error:", e)
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500

@app.route('/api/payments/<int:id>', methods=['PUT'])
@jwt_required()
def update_payment(id):
    try:
        payment = Payment.query.get_or_404(id)
        data = request.get_json()
        payment.amount = data.get('amount', payment.amount)
        payment.method = data.get('method', payment.method)
        payment.status = data.get('status', payment.status)
        payment.reference = data.get('reference', payment.reference)
        db.session.commit()
        return jsonify(payment.to_dict())
    except Exception as e:
        print("💥 update_payment error:", e)
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500

@app.route('/api/payments/<int:id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_payment(id):
    try:
        payment = Payment.query.get_or_404(id)
        db.session.delete(payment)
        db.session.commit()
        return jsonify({'message': 'Payment deleted'})
    except Exception as e:
        print("💥 delete_payment error:", e)
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500

# ─── Gallery ─────────────────────────────────────────────

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/api/gallery', methods=['GET'])
@jwt_required()
def get_gallery():
    try:
        images = Gallery.query.order_by(Gallery.created_at.desc()).all()
        return jsonify([img.to_dict() for img in images])
    except Exception as e:
        print("💥 get_gallery error:", e)
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500

@app.route('/api/gallery/upload', methods=['POST'])
@jwt_required()
def upload_gallery_images():
    try:
        if 'images' not in request.files:
            return jsonify({'message': 'No images provided'}), 400
        files = request.files.getlist('images')
        if not files or files[0].filename == '':
            return jsonify({'message': 'No images selected'}), 400

        inserted = []
        for file in files:
            if not allowed_file(file.filename):
                continue

            # Upload to Cloudinary
            result = cloudinary.uploader.upload(file, folder='iskhumba_gallery')
            url = result['secure_url']

            gallery_item = Gallery(title=file.filename, url=url)
            db.session.add(gallery_item)
            db.session.flush()
            inserted.append(gallery_item.to_dict())

        db.session.commit()
        return jsonify(inserted), 201
    except Exception as e:
        print("💥 upload_gallery error:", e)
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500

@app.route('/api/gallery/<int:id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_gallery_image(id):
    try:
        image = Gallery.query.get_or_404(id)
        # Optionally delete from Cloudinary using public_id if you store it
        # For now we just remove the database record
        db.session.delete(image)
        db.session.commit()
        return jsonify({'message': 'Image deleted'})
    except Exception as e:
        print("💥 delete_gallery_image error:", e)
        traceback.print_exc()
        return jsonify({'message': str(e)}), 500

# ─── Start Server and Create Tables ─────────────────────

# IMPORTANT: This ensures tables are created when the app starts (e.g., with Gunicorn)
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
