from flask import request, jsonify
from app.admin import admin_bp
from app.models import Category, User, Role, SellerCategory # <-- Naye imports
from app.extensions import db, bcrypt # <-- bcrypt add kiya password hash ke liye
from app.utils.decorators import admin_required


@admin_bp.route('/category', methods=['POST'])
@admin_required()  # <-- Ye hamara banaya hua security lock hai
def create_category():
    data = request.get_json()
    
    name = data.get('name')
    description = data.get('description', '')

    if not name:
        return jsonify({"error": "Category name is required"}), 400

    # Check karna ki category pehle se toh nahi hai
    existing_category = Category.query.filter_by(name=name).first()
    if existing_category:
        return jsonify({"error": "Category already exists"}), 400

    # Database me nayi category add karna
    new_category = Category(name=name, description=description)
    db.session.add(new_category)
    db.session.commit()

    return jsonify({
        "message": "Category created successfully!",
        "category_id": new_category.public_id,
        "name": new_category.name
    }), 201



# ... (Tumhara purana create_category wala code yahan upar rahega) ...

@admin_bp.route('/create-seller', methods=['POST'])
@admin_required()
def create_seller():
    data = request.get_json()
    
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    category_names = data.get('categories', []) # Categories ki list aayegi

    if not name or not email or not password:
        return jsonify({"error": "Name, email, and password are required"}), 400

    # 1. Check if user already exists
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400

    # 2. Find the 'Seller' role in database
    seller_role = Role.query.filter_by(role_name='Seller').first()
    if not seller_role:
        return jsonify({"error": "Seller role not found in DB"}), 500

    # 3. Create the Seller Account
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_seller = User(
        name=name,
        email=email,
        password_hash=hashed_password,
        role_id=seller_role.id,
        is_verified=True # Abhi ke liye true rakhte hain, OTP email aage setup karenge
    )
    db.session.add(new_seller)
    
    # PRO TIP: flush() use karne se naye seller ki ID mil jayegi bina poora save (commit) kiye
    db.session.flush() 

    # 4. Seller ko Categories assign karna (Bridge table me entry)
    for cat_name in category_names:
        category = Category.query.filter_by(name=cat_name).first()
        if category:
            new_relation = SellerCategory(seller_id=new_seller.id, category_id=category.id)
            db.session.add(new_relation)

    # 5. Sab kuch ek saath database me save kar do
    db.session.commit()

    return jsonify({
        "message": "Seller account created successfully!",
        "seller_id": new_seller.public_id,
        "email": new_seller.email,
        "assigned_categories": category_names
    }), 201