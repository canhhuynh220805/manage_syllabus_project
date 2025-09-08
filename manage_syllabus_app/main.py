from flask import render_template
from manage_syllabus_app import app
from pathlib import Path
from manage_syllabus_app import db
import json, os

from manage_syllabus_app.models import Faculty, Lecturer, Credit, Subject, Syllabus, RequirementSubject, \
    TypeRequirement, MainSection, LearningMaterial, TypeLearningMaterial, AttributeGroup


@app.route('/')
def index():
    faculty = Faculty.query.all()
    syllabuses = Syllabus.query.all()

    return render_template('index.html', syllabuses=syllabuses, faculty=faculty)


@app.route('/editor')
def editor():
    return render_template('editor.html')

@app.route('/de-cuong/<int:syllabus_id>/')
def syllabus_detail(syllabus_id):
    syllabus = Syllabus.query.get_or_404(syllabus_id)
    return render_template('syllabus_detail.html', syllabus=syllabus)


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
        faculty_name = syllabus_data['faculty']['name']
        faculty = db.session.query(Faculty).filter_by(name=faculty_name).first()
        if not faculty:
            faculty = Faculty(name=faculty_name)
            db.session.add(faculty)
            print(f"Đã tạo khoa: {faculty_name}")

        # Lấy hoặc tạo GIẢNG VIÊN (Lecturer)
        lecturer = syllabus_data['lecturer']
        lecturer_temp = db.session.query(Lecturer).filter_by(name=lecturer['name']).first()
        lecturer_faculty = db.session.query(Faculty).filter_by(name=lecturer['faculty']['faculty_name']).first()
        if not lecturer_faculty:
            faculty = Faculty(name=lecturer.faculty.name)
            db.session.add(faculty)
            print(f"Đã tạo khoa: {lecturer.faculty.name}")
        if not lecturer_temp:
            # Chắc chắn rằng lecturer được gán vào khoa đã tồn tại hoặc vừa được tạo
            lecturer = Lecturer(name=lecturer['name'], faculty=faculty)

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

        # Lấy hoặc tạo môn học điều kiện
        require_subject_data = syllabus_data['subject'].get('required_subjects', [])
        for temp in require_subject_data:
            require_subject_id = temp['require_subject_id']
            require_subject = db.session.query(Subject).filter_by(id=require_subject_id).first()
            type_require_name = temp['type_requirement']
            type_requirement = db.session.query(TypeRequirement).filter_by(name=type_require_name).first()
            #kiểm tra loại điều kiện có hay chưa
            if not type_requirement:
                type_requirement = TypeRequirement(name=type_require_name)
                db.session.add(type_requirement)
                print(f"đã tạo loại điều kiện: {type_require_name}")
            #kiểm tra môn học đã có hay chưa
            if not require_subject:
                subject_requirement = Subject(
                    id=require_subject_id,
                    name=temp['require_subject_name'],
                    credit = credit
                )
                db.session.add(subject_requirement)
                print(f"Đã tạo môn học: {temp['require_subject_name']}")
            new_requirement_subject = RequirementSubject(
                subject = subject,
                require_subject = subject_requirement,
                type_requirement = type_requirement,
            )
            db.session.add(new_requirement_subject)
            print(f"✅ Đã thêm '{subject_requirement.name}' làm môn điều kiện cho '{subject.name}' thành công!")
        #lấy hoặc tạo ĐỀ CƯƠNG (Syllabus)
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

        # tạo phần đề cương
        main_parts = syllabus_data['main_parts']
        for temp in main_parts:
            main_part = MainSection(name=temp['name'], syllabus=syllabus)
            db.session.add(main_part)
        learning_materials = syllabus_data['learning_materials']
        for temp in learning_materials:
            type_name = temp['type_material']['name']
            lm_type_obj = db.session.query(TypeLearningMaterial).filter_by(name=type_name).first()
            if not lm_type_obj:
                lm_type_obj = TypeLearningMaterial(name=type_name)
                db.session.add(lm_type_obj)
                print(f"Đã tạo loại học liệu mới: {type_name}")
            lm_name = temp['name']
            # 3. Tìm học liệu bằng TÊN
            lm_obj = db.session.query(LearningMaterial).filter_by(name=lm_name).first()

            # 4. Nếu không tìm thấy, tạo mới
            if not lm_obj:
                # Gán đối tượng lm_type_obj đã tìm thấy hoặc vừa tạo ở trên
                lm_obj = LearningMaterial(
                    name=lm_name,
                    type_material=lm_type_obj
                )
                db.session.add(lm_obj)
                print(f"Đã tạo học liệu mới: {lm_name}")

            # --- Liên kết học liệu với đề cương ---
            if lm_obj not in syllabus.learning_materials:
                syllabus.learning_materials.append(lm_obj)

    # 3. Commit tất cả thay đổi vào database
    try:
        db.session.commit()
        print("✅ Gieo dữ liệu thành công!")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Đã xảy ra lỗi: {e}")


@app.cli.command("db-seed-2")
def db_seed_2():
    """Đọc file JSON và lưu dữ liệu vào database."""

    # 1. Đọc file data.json
    json_path = Path(__file__).parent / 'data' / 'attribute_groups.json'
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for item in data['attribute_groups']:
        name_group = item['name_group']
        group_attribute = db.session.query(AttributeGroup).filter_by(name=name_group).first()
        if not group_attribute:
            attribute_values = item['attribute_values']

            group_attribute = Faculty(name_group=name_group,attribute_values=attribute_values)
            db.session.add(group_attribute)
            print(f"Đã tạo nhóm thuộc tính: {name_group}")

    # 3. Commit tất cả thay đổi vào database
    try:
        db.session.commit()
        print("✅ Gieo dữ liệu thành công!")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Đã xảy ra lỗi: {e}")

if __name__ == '__main__':
    app.run(debug=True)


