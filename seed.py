from app import create_app
from app.extensions import db, bcrypt
from app.models import Role, User

app = create_app()

with app.app_context():
    # 1. Database me Roles daalna
    role_names = ['Admin', 'Seller', 'User']
    for role_name in role_names:
        # Check karna ki role pehle se toh nahi hai
        existing_role = Role.query.filter_by(role_name=role_name).first()
        if not existing_role:
            new_role = Role(role_name=role_name)
            db.session.add(new_role)
    db.session.commit()
    print("✅ Roles successfully added: Admin, Seller, User")

    # 2. Pehla Super Admin account banana
    admin_role = Role.query.filter_by(role_name='Admin').first()
    if admin_role:
        existing_admin = User.query.filter_by(email='admin@ecommerce.com').first()
        if not existing_admin:
            # Password ko secure (hash) karna
            hashed_password = bcrypt.generate_password_hash('7899').decode('utf-8')
            admin_user = User(
                name='Super Admin', 
                email='hardik@admin.com', 
                password_hash=hashed_password, 
                role_id=admin_role.id, 
                is_verified=True # Admin ko OTP verify karne ki zaroorat nahi
            )
            db.session.add(admin_user)
            db.session.commit()
            print(f"✅ {User}")
        else:
            print("⚠️ Admin account already exists.")