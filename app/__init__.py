from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    load_dotenv()  # load .env

    # BASIC CONFIG
    app.config['SECRET_KEY'] = 'supersecretkey'  # change later if you want
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///timetable.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    app.config['LLM_API_KEY'] = os.getenv("LLM_API_KEY")
    app.config['LLM_API_URL'] = os.getenv("LLM_API_URL")
    app.config['LLM_MODEL'] = os.getenv("LLM_MODEL", "gpt-4.1-mini")

    print("Loaded LLM_API_KEY:", os.getenv("LLM_API_KEY"))

    # INIT EXTENSIONS
    db.init_app(app)
    login_manager.init_app(app)

    # Where to redirect if user is not logged in
    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'warning'

    # Import and register routes
    from .routes import main
    app.register_blueprint(main)

    return app