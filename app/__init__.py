from flask import Flask
from config import Config
from app.extensions import db, migrate, jwt, bcrypt, mail

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Saare extensions ko app ke sath connect karna
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)

    # Database models ko import karna zaroori hai taaki Migrate unhe detect kar sake
    from app import models

    # Blueprints register karna
    from app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from app.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    from app.seller import seller_bp
    app.register_blueprint(seller_bp, url_prefix='/api/seller')

    from app.user import user_bp
    app.register_blueprint(user_bp, url_prefix='/api/user')

    @app.route('/')
    def home():
        return {"message": "E-Commerce API is Running!"}

    # BAS YE EK LINE ADD KARNI HAI (Indentation ka dhyan rakhna)
    return app