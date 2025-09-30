from manage_syllabus_app import app, db
from manage_syllabus_app.seed_database import seed_data, seed_data_2, seed_data_3

@app.cli.command("create-db")
def create_db():
    """Tạo tất cả các bảng trong cơ sở dữ liệu."""
    with app.app_context():
        db.create_all()
        print("Đã tạo cơ sở dữ liệu thành công!")

@app.cli.command("seed-db")
def seed_db():
    """Thêm dữ liệu mẫu vào cơ sở dữ liệu."""
    with app.app_context():
        seed_data()
        seed_data_2()
        seed_data_3()
        print("Đã thêm dữ liệu mẫu thành công!")

'''
(.venv) PS D:\PythonProject> $env:FLASK_APP="manage_syllabus_app.main"
(.venv) PS D:\PythonProject> flask create-db                          
Đã tạo cơ sở dữ liệu thành công!
(.venv) PS D:\PythonProject> flask seed-db
'''