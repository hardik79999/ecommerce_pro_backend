from flask import jsonify
from app.user import user_bp
from app.models import Product

@user_bp.route('/products', methods=['GET'])
def get_all_products():
    # Sirf wo products dikhao jo active hain
    products = Product.query.filter_by(is_active=True).all()
    
    result = []
    for p in products:
        # Product ki 'is_primary=True' wali image dhundo
        primary_img = next((img.image_url for img in p.images if img.is_primary), None)
        
        result.append({
            "product_id": p.public_id,
            "name": p.name,
            "price": float(p.price),
            "category": p.category.name,
            "stock": p.stock_quantity,
            "image": primary_img # Ye wahi URL hoga jo abhi tumne upload kiya tha!
        })

    return jsonify({
        "total_products": len(result),
        "products": result
    }), 200







from flask import request
from app.models import CartItem, User, Order, OrderItem, OrderStatus, OTPAction, OTP, Product
from app.extensions import db
from app.utils.decorators import customer_required
from app.utils.email_service import send_verification_email, send_sms_otp
from flask_jwt_extended import get_jwt_identity
import random
import datetime as dt
from itsdangerous import URLSafeTimedSerializer
from flask import url_for, current_app



@user_bp.route('/cart', methods=['POST'])
@customer_required()
def add_to_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 1) # Agar quantity nahi di toh default 1 manenge

    if not product_id:
        return jsonify({"error": "product_id is required"}), 400

    # Token se asol User nikaalo
    user_public_id = get_jwt_identity()
    user = User.query.filter_by(public_id=user_public_id).first()

    # Product verify karo
    product = Product.query.filter_by(public_id=product_id, is_active=True).first()
    if not product:
        return jsonify({"error": "Product not found"}), 404
        
    # Stock check karo
    if product.stock_quantity < quantity:
        return jsonify({"error": f"Only {product.stock_quantity} items left in stock"}), 400

    # Check karo kya ye product already cart me hai
    existing_item = CartItem.query.filter_by(user_id=user.id, product_id=product.id).first()
    
    if existing_item:
        existing_item.quantity += quantity
    else:
        new_cart_item = CartItem(user_id=user.id, product_id=product.id, quantity=quantity)
        db.session.add(new_cart_item)

    db.session.commit()

    return jsonify({"message": "Product added to cart successfully!"}), 200





@user_bp.route('/checkout', methods=['POST'])
@customer_required()
def checkout():
    user_public_id = get_jwt_identity()
    user = User.query.filter_by(public_id=user_public_id).first()

    # 1. User ka cart nikalo
    cart_items = CartItem.query.filter_by(user_id=user.id).all()
    if not cart_items:
        return jsonify({"error": "Your cart is empty"}), 400

    total_amount = 0
    order_items_data = []

    # 2. Total amount calculate karo aur stock check karo
    for item in cart_items:
        product = Product.query.get(item.product_id)
        
        if product.stock_quantity < item.quantity:
            return jsonify({"error": f"Not enough stock for {product.name}"}), 400

        item_total = product.price * item.quantity
        total_amount += item_total

        order_items_data.append({
            "product_id": product.id,
            "quantity": item.quantity,
            "price_at_purchase": product.price,
            "product_obj": product
        })

    # 3. Naya Order Banao (Status: Pending)
    new_order = Order(
        user_id=user.id,
        total_amount=total_amount,
        status=OrderStatus.pending
    )
    db.session.add(new_order)
    db.session.flush() # Naye order ki ID lene ke liye

    # 4. Order Items save karo aur Stock kam karo
    for data in order_items_data:
        order_item = OrderItem(
            order_id=new_order.id,
            product_id=data['product_id'],
            quantity=data['quantity'],
            price_at_purchase=data['price_at_purchase']
        )
        db.session.add(order_item)
        
        # Product ka stock update (kam) karna
        data['product_obj'].stock_quantity -= data['quantity']

    # 5. Cart ko khali (clear) kar do
    for item in cart_items:
        db.session.delete(item)

    # 6. OTP Generate aur Send karo (Email + SMS)
    order_otp = str(random.randint(100000, 999999))
    
    # OTP Database me save karo
    otp_record = OTP(
        user_id=user.id,
        otp_code=order_otp,
        action=OTPAction.order_confirm,
        expires_at=dt.datetime.utcnow() + dt.timedelta(minutes=10),
        is_used=False
    )
    db.session.add(otp_record)
    db.session.commit()
    
    # Email me send karo
    send_verification_email(user.email, order_otp, "")
    # SMS me send karo
    send_sms_otp(user.phone_number, order_otp)

    return jsonify({
        "message": "Order placed successfully! Check your email/SMS for OTP to confirm.",
        "order_id": new_order.public_id,
        "total_amount": float(total_amount),
        "status": new_order.status.name
    }), 201








from datetime import datetime
from app.models import OTP # <-- Ensure ye imported ho

# ... (Tumhara checkout code yahan upar rahega) ...

@user_bp.route('/verify-order', methods=['POST'])
@customer_required()
def verify_order_otp():
    data = request.get_json()
    
    order_id = data.get('order_id')
    otp_code = data.get('otp_code')

    if not order_id or not otp_code:
        return jsonify({"error": "order_id and otp_code are required"}), 400

    # Token se user nikalo
    user_public_id = get_jwt_identity()
    user = User.query.filter_by(public_id=user_public_id).first()

    # 1. Order check karo
    order = Order.query.filter_by(public_id=order_id, user_id=user.id).first()
    if not order:
        return jsonify({"error": "Order not found"}), 404

    if order.is_otp_verified:
        return jsonify({"error": "Order is already verified"}), 400

    # 2. OTP Database me dhoondho (Jo used na ho aur expire na hua ho)
    otp_record = OTP.query.filter_by(
        user_id=user.id,
        otp_code=otp_code,
        action=OTPAction.order_confirm,
        is_used=False
    ).order_by(OTP.created_at.desc()).first()

    if not otp_record:
        return jsonify({"error": "Invalid OTP. Please check the code."}), 400

    if otp_record.expires_at < datetime.utcnow():
        return jsonify({"error": "OTP has expired. Please request a new one."}), 400

    # 3. OTP aur Order ko Update karo!
    otp_record.is_used = True
    order.is_otp_verified = True
    order.status = OrderStatus.processing  # Status Update!

    db.session.commit()

    return jsonify({
        "message": "OTP Verified! Your order is now confirmed and processing.",
        "order_id": order.public_id,
        "status": order.status.name
    }), 200