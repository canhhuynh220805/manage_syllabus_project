from flask import render_template
from manage_syllabus_app import app
from pathlib import Path
from manage_syllabus_app import db
import json, os

from manage_syllabus_app.models import Faculty, Lecturer, Credit, Subject, Syllabus


@app.route('/')
def index():
    syllabuses = Syllabus.query.all()

    return render_template('index.html', syllabuses=syllabuses)

@app.cli.command("db-seed")
def db_seed():
    """Đọc file JSON và lưu dữ liệu vào database."""

    # 1. Đọc file data.json
    json_path = Path(__file__).parent / 'data' / 'data.json'
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 2. Duyệt qua từng đề cương trong file json
    for syllabus_data in data['syllabuses']:
        # Lấy hoặc tạo KHOA (Faculty)
        faculty_name = syllabus_data['faculty']['faculty_name']
        faculty = db.session.query(Faculty).filter_by(name=faculty_name).first()
        if not faculty:
            faculty = Faculty(name=faculty_name)
            db.session.add(faculty)
            print(f"Đã tạo khoa: {faculty_name}")

        # Lấy hoặc tạo GIẢNG VIÊN (Lecturer)
        lecturer_name = syllabus_data['lecturer']['name']
        lecturer = db.session.query(Lecturer).filter_by(name=lecturer_name).first()
        if not lecturer:
            # Chắc chắn rằng lecturer được gán vào khoa đã tồn tại hoặc vừa được tạo
            lecturer = Lecturer(name=lecturer_name, faculty=faculty)
            db.session.add(lecturer)
            print(f"Đã tạo giảng viên: {lecturer_name}")

        # Lấy hoặc tạo TÍN CHỈ (Credit)
        credit_data = syllabus_data['subject']['credit']
        credit = db.session.query(Credit).filter_by(
            numberTheory=credit_data['number theory'],
            numberPractice=credit_data['number practice']
        ).first()
        if not credit:
            credit = Credit(
                numberTheory=credit_data['number theory'],
                numberPractice=credit_data['number practice'],
                hourSelfStudy=credit_data['hour self study']
            )
            db.session.add(credit)
            print("Đã tạo tín chỉ mới.")

        # Lấy hoặc tạo MÔN HỌC (Subject)
        subject_data = syllabus_data['subject']
        subject_id = subject_data['id']
        subject = db.session.query(Subject).filter_by(id=subject_id).first()
        if not subject:
            subject = Subject(
                id=subject_id,
                name=subject_data['name'],
                credit=credit
            )
            db.session.add(subject)
            print(f"Đã tạo môn học: {subject_data['name']}")

        # Cuối cùng, lấy hoặc tạo ĐỀ CƯƠNG (Syllabus)
        syllabus_name = syllabus_data['name']
        syllabus = db.session.query(Syllabus).filter_by(name=syllabus_name).first()
        if not syllabus:
            syllabus = Syllabus(
                name=syllabus_name,
                subject=subject,
                lecturer=lecturer,
                faculty=faculty
            )
            db.session.add(syllabus)
            print(f"Đã tạo đề cương: {syllabus_name}")

    # 3. Commit tất cả thay đổi vào database
    try:
        db.session.commit()
        print("✅ Gieo dữ liệu thành công!")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Đã xảy ra lỗi: {e}")

if __name__ == '__main__':
    app.run(debug=True)


