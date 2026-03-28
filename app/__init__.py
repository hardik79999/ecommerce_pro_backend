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

    # Blueprints ko yahan register karenge (Ye hum next step me banayenge)
    from app.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    @app.route('/')
    def index():
        return {"message": "Welcome to the Pro E-Commerce API!"}

    return app