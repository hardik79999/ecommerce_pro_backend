from flask import Blueprint, request, jsonify, url_for, current_app
from app.extensions import db, bcrypt
from app.models import User, Role
from app.utils.email_service import send_verification_email, send_sms_otp
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature
from flask_jwt_extended import create_access_token
from app.auth import auth_bp
import random
import datetime

# --- LOGIN ROUTE ---
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400

    user = User.query.filter_by(email=data.get('email')).first()

    if user and bcrypt.check_password_hash(user.password_hash, data.get('password')):
        if not user.is_active:
            return jsonify({"error": "Your account has been blocked."}), 403
        
        # Industry Rule: Check if user is verified before login
        if not user.is_email_verified or not user.is_phone_verified:
            return jsonify({"error": "Please verify your email and phone first."}), 401

        access_token = create_access_token(
            identity=str(user.public_id),
            additional_claims={'role': user.role.role_name},
            expires_delta=datetime.timedelta(days=1)
        )
        
        return jsonify({
            "message": "Login successful",
            "access_token": access_token,   
            "role": user.role.role_name,
            "user_id": user.public_id
        }), 200
    
    return jsonify({"error": "Invalid email or password"}), 401


# --- REGISTER ROUTE (MERGED & REAL) ---
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone_number')  # Format: +91XXXXXXXXXX or 91XXXXXXXXXX

    if not all([name, email, password, phone]):
        return jsonify({"error": "All fields (name, email, password, phone) are required"}), 400

    # Format phone number - ensure it starts with +
    phone = phone.strip()
    if not phone.startswith('+'):
        if phone.startswith('0'):
            phone = '+91' + phone[1:]  # Remove leading 0 and add +91
        elif phone.startswith('91'):
            phone = '+' + phone
        else:
            phone = '+91' + phone

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email is already registered"}), 400

    # 1. OTPs aur Token generate karo
    email_otp = str(random.randint(100000, 999999))
    phone_otp = str(random.randint(100000, 999999))
    
    # 2. Assign 'User' role
    user_role = Role.query.filter_by(role_name='User').first()

    # 3. Create User
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(
        name=name,
        email=email,
        phone_number=phone,
        password_hash=hashed_password,
        role_id=user_role.id,
        email_otp=email_otp,
        phone_otp=phone_otp,
        is_email_verified=False,
        is_phone_verified=False
    )
    
    db.session.add(new_user)
    db.session.commit()

    # 4. Generate 10-Min Email Link
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token = serializer.dumps(email, salt='email-confirm')
    confirm_link = url_for('auth.verify_email_link', token=token, _external=True)

    # 5. Send Email and SMS
    send_verification_email(email, email_otp, confirm_link)
    send_sms_otp(phone, phone_otp)

    return jsonify({
        "message": "User registered! Please check email/phone for verification.",
        "user_id": new_user.public_id
    }), 201


# --- VERIFICATION ROUTES ---

@auth_bp.route('/verify-email/<token>')
def verify_email_link(token):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='email-confirm', max_age=600)
    except SignatureExpired:
        return jsonify({"error": "Verification link expired (10 min limit)!"}), 400
    except BadTimeSignature:
        return jsonify({"error": "Invalid token!"}), 400
        
    user = User.query.filter_by(email=email).first()
    if user:
        user.is_email_verified = True
        user.email_otp = None 
        db.session.commit()
        return "<h1>Email Verified Successfully!</h1><p>You can now close this tab and login.</p>"
    return jsonify({"error": "User not found"}), 404


@auth_bp.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.json
    user = User.query.filter_by(email=data.get('email')).first()
    
    if not user:
        return jsonify({"error": "User not found"}), 404
        
    if 'email_otp' in data and user.email_otp == data.get('email_otp'):
        user.is_email_verified = True
        user.email_otp = None
        
    if 'phone_otp' in data and user.phone_otp == data.get('phone_otp'):
        user.is_phone_verified = True
        user.phone_otp = None
        
    db.session.commit()
    
    if user.is_email_verified and user.is_phone_verified:
        return jsonify({"message": "Both Email and Phone verified! You can login now."}), 200
    return jsonify({"message": "One verification done, other pending."}), 400