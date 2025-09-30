import os
from dotenv import load_dotenv
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy


# Tải các biến môi trường từ file .env
load_dotenv()

app = Flask(__name__)

db_user = os.getenv("DB_USERNAME")
db_pass = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")
db_uri = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}?charset=utf8mb4"
app.config["SECRET_KEY"] = "d4e2a8c1b9f0e1d3c5a7b6f8e9d0c1b2"
app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.jinja_env.add_extension('jinja2.ext.do')

login = LoginManager(app=app)
db = SQLAlchemy(app=app)

from manage_syllabus_app import commands
from manage_syllabus_app.models import User
@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


