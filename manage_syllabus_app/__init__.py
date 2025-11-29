import os
from dotenv import load_dotenv
from flask import Flask, Blueprint
from flask_login import LoginManager
from flask_migrate import Migrate
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
app.config["PAGE_SIZE"] = 7

login = LoginManager(app=app)
db = SQLAlchemy(app=app)
migrate = Migrate(app, db)
login.login_view = 'user_login'

try:
    from .controllers import api as api_blueprint
    #Đăng ký Blueprint với ứng dụng Flask
    app.register_blueprint(api_blueprint)
except ImportError as e:
    print(f"Cảnh báo: Không thể import hoặc đăng ký api_blueprint. Lỗi: {e}")
from manage_syllabus_app import controllers, commands, admin



