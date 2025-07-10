import os

import click
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Tải các biến môi trường từ file .env
load_dotenv()

app = Flask(__name__)

db_user = os.getenv("DB_USERNAME")
db_pass = os.getenv("DB_PASSWORD")
db_host = os.getenv("DB_HOST")
db_name = os.getenv("DB_NAME")
db_uri = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}?charset=utf8mb4"

app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


@app.cli.command("init-db")
def init_db_command():
    """Tạo các bảng trong database."""
    with app.app_context():
        from . import models
        db.create_all()
    click.echo("Đã khởi tạo database thành công.")
