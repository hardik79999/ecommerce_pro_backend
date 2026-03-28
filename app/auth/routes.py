from flask import request, jsonify
from app.auth import auth_bp
from app.models import User
from app.extensions import bcrypt
from flask_jwt_extended import create_access_token
import datetime

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    # 1. Check if email and password are provided
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({"error": "Email and password are required"}), 400


    email = data.get('email')
    password = data.get('password')


    # 2. Find user in database
    user = User.query.filter_by(email=email).first()

    # 3. Check if user exists and password is correct
    if user and bcrypt.check_password_hash(user.password_hash, password):
        
        # 4. Check if user is blocked by admin
        if not user.is_active:
            return jsonify({"error": "Your account has been blocked."}), 403

        # 5. Generate JWT Token (Token me sirf public_id aur role daalenge security ke liye)
        access_token = create_access_token(
            identity={'public_id': user.public_id, 'role': user.role.role_name},
            expires_delta=datetime.timedelta(days=1) # Token 1 din tak chalega
        )
        
        return jsonify({
            "message": "Login successful",
            "access_token": access_token,
            "role": user.role.role_name,
            "user_id": user.public_id
        }), 200
        
    else:
        return jsonify({"error": "Invalid email or password"}), 401