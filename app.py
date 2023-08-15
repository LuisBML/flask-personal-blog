from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
import os

# Configure Flask-Login
login_manager = LoginManager()

db = SQLAlchemy()
bcrypt = Bcrypt()


def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = os.getenv("FLASK_KEY")
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        "DB_URI", "sqlite:///blog.db")

    login_manager.init_app(app)
    db.init_app(app)
    bcrypt.init_app(app)
    Bootstrap5(app)
    CKEditor(app)
    return app
