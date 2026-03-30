from flask import request, jsonify
from app.seller import seller_bp
from app.models import Product, Category, SellerCategory, User, ProductImage
from app.utils.file_handler import save_image
from app.extensions import db
from app.utils.decorators import seller_required
from flask_jwt_extended import get_jwt_identity

@seller_bp.route('/product', methods=['POST'])
@seller_required()
def add_product():
    data = request.get_json()
    seller_public_id = get_jwt_identity() # Token se seller ki public_id mil jayegi

    # Database se seller ka asol account nikaalo
    seller = User.query.filter_by(public_id=seller_public_id).first()

    name = data.get('name')
    category_name = data.get('category_name')
    price = data.get('price')
    description = data.get('description', '')
    stock_quantity = data.get('stock_quantity', 0)

    if not all([name, category_name, price]):
        return jsonify({"error": "Name, category_name, and price are required"}), 400

    # 1. Category check karo ki DB me hai ya nahi
    category = Category.query.filter_by(name=category_name).first()
    if not category:
        return jsonify({"error": "Category not found"}), 404

    # 2. PRO LEVEL SECURITY CHECK: Kya ye seller is category me bech sakta hai?
    is_allowed = SellerCategory.query.filter_by(seller_id=seller.id, category_id=category.id).first()
    if not is_allowed:
        return jsonify({"error": f"You are not authorized to sell in the '{category_name}' category"}), 403

    # 3. Agar sab theek hai toh Product add kardo
    new_product = Product(
        seller_id=seller.id,
        category_id=category.id,
        name=name,
        description=description,
        price=price,
        stock_quantity=stock_quantity
    )
    db.session.add(new_product)
    db.session.commit()

    return jsonify({
        "message": "Product added successfully!",
        "product_id": new_product.public_id,
        "name": new_product.name
    }), 201





@seller_bp.route('/product/images', methods=['POST']) # <-- URL ab ekdum clean hai
@seller_required()
def upload_product_images():
    # 1. JSON ki jagah form-data se ID nikaalna
    product_id = request.form.get('product_id')
    
    if not product_id:
        return jsonify({"error": "product_id is required in the form data"}), 400

    # JWT token se seller ki ID nikaalo
    seller_public_id = get_jwt_identity()
    seller = User.query.filter_by(public_id=seller_public_id).first()

    # 2. Check karo ki product exist karta hai aur ISI seller ka hai
    product = Product.query.filter_by(public_id=product_id, seller_id=seller.id).first()
    if not product:
        return jsonify({"error": "Product not found or you don't own this product"}), 404

    # 3. Request se saari images nikaalo
    if 'images' not in request.files:
        return jsonify({"error": "No images provided"}), 400

    files = request.files.getlist('images')
    uploaded_urls = []

    # 4. Har image ko loop karke save karo
    for index, file in enumerate(files):
        if file.filename == '':
            continue
            
        image_url = save_image(file, folder_name="products")
        
        if image_url:
            is_primary = True if index == 0 else False
            new_image = ProductImage(
                product_id=product.id,
                image_url=image_url,
                is_primary=is_primary
            )
            db.session.add(new_image)
            uploaded_urls.append(image_url)

    if not uploaded_urls:
        return jsonify({"error": "Invalid file types. Only JPG, PNG, WEBP allowed."}), 400

    db.session.commit()

    return jsonify({
        "message": f"Successfully uploaded {len(uploaded_urls)} images",
        "image_urls": uploaded_urls
    }), 201