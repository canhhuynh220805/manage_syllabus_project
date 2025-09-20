# seed_database.py

import json
from pathlib import Path

from manage_syllabus_app import app, db
from manage_syllabus_app.models import AttributeGroup, AttributeValue, Syllabus, Faculty, Lecturer, Subject, Credit, \
    TypeRequirement, RequirementSubject, TypeLearningMaterial, LearningMaterial, MainSection, SubSection, \
    TextSubSection, SelectionSubSection, ReferenceSubSection, ProgrammeLearningOutcome, CourseLearningOutcome, \
    CourseObjective, CloPloAssociation


def seed_data():
    """Hàm chứa logic đọc file JSON và lưu vào database."""
    json_path = Path(__file__).parent / 'data' / 'attribute_groups.json'

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print("Bắt đầu gieo dữ liệu...")
    for item in data['attribute_groups']:
        name_group_from_json = item['name_group']

        exists = db.session.query(AttributeGroup).filter_by(name_group=name_group_from_json).first()
        if not exists:
            values_from_json = item['values']
            list_of_value_objects = [AttributeValue(id=val['id'], name_value=val['name_value']) for val in values_from_json]

            # SỬA Ở ĐÂY: Thay `name` bằng `name_group` để khớp với model
            new_group = AttributeGroup(
                name_group=name_group_from_json,
                attribute_values=list_of_value_objects
            )

            db.session.add(new_group)
            print(f"  -> Đã thêm nhóm: {name_group_from_json} với {len(list_of_value_objects)} giá trị.")

        else:
            print(f"  -> Bỏ qua, nhóm đã tồn tại: {name_group_from_json}")

    try:
        db.session.commit()
        print("✅ Gieo dữ liệu thành công!")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Đã xảy ra lỗi: {e}")

def seed_data_2():
    """Hàm chứa logic đọc file JSON và lưu vào database."""
    json_path = Path(__file__).parent / 'data' / 'plo.json'

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    cnt = 0;
    print("Bắt đầu gieo dữ liệu...")
    for item in data['programme_learning_outcomes']:
        id_plo = item['id']
        description = item['description']

        plo = ProgrammeLearningOutcome(id=id_plo, description=description)
        db.session.add(plo)
        cnt += 1
    try:
        db.session.commit()
        print(f"✅ Gieo dữ liệu thành công!  {cnt}")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Đã xảy ra lỗi: {e}")


def seed_data_3():
    json_path = Path(__file__).parent / 'data' / 'data.json'
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for item in data['syllabuses']:
        # --- Faculty ---
        faculty_name = item['faculty']['name']
        faculty = db.session.query(Faculty).filter_by(name=faculty_name).first()
        if not faculty:
            faculty = Faculty(name=faculty_name)
            db.session.add(faculty)

        # --- Lecturer ---
        lecturer_name = item['lecturer']['name']
        lecturer = db.session.query(Lecturer).filter_by(name=lecturer_name).first()
        if not lecturer:
            lecturer = Lecturer(name=lecturer_name, faculty=faculty)
            db.session.add(lecturer)

        # --- Credit ---
        credit_data = item['subject']['credit']
        credit = db.session.query(Credit).filter_by(
            numberTheory=credit_data['number_theory'],
            numberPractice=credit_data['number_practice']
        ).first()
        if not credit:
            credit = Credit(
                numberTheory=credit_data['number_theory'],
                numberPractice=credit_data['number_practice'],
                hourSelfStudy=credit_data['hour_self_study']
            )
            db.session.add(credit)

        # --- Subject ---
        subject_id = item['subject']['id']
        subject = db.session.query(Subject).filter_by(id=subject_id).first()
        if not subject:
            subject = Subject(id=subject_id, name=item['subject']['name'], credit=credit)
            db.session.add(subject)

        # --- RequirementSubject ---
        require_subject_data = item['subject'].get('required_subjects', [])
        for temp in require_subject_data:
            require_subject_id = temp['require_subject_id']

            # SỬA LỖI 1: Dùng một biến duy nhất 'require_subject'
            require_subject = db.session.query(Subject).filter_by(id=require_subject_id).first()
            if not require_subject:
                # Tìm credit cho môn học tiên quyết, nếu không có thì dùng credit của môn chính
                # (Trong thực tế bạn sẽ cần logic phức tạp hơn)
                prereq_credit = Credit.query.first()  # Lấy tạm một credit
                require_subject = Subject(
                    id=require_subject_id,
                    name=temp['require_subject_name'],
                    credit=prereq_credit
                )
                db.session.add(require_subject)

            type_require_name = temp['type_requirement']
            type_requirement = db.session.query(TypeRequirement).filter_by(name=type_require_name).first()
            if not type_requirement:
                type_requirement = TypeRequirement(name=type_require_name)
                db.session.add(type_requirement)

            new_requirement_subject = RequirementSubject(
                subject=subject,
                require_subject=require_subject,  # Sử dụng biến đã được hợp nhất
                type_requirement=type_requirement,
            )
            db.session.add(new_requirement_subject)

        # --- Syllabus ---
        syllabus_name = item['name']
        syllabus = db.session.query(Syllabus).filter_by(name=syllabus_name).first()
        if not syllabus:
            syllabus = Syllabus(
                name=syllabus_name,
                subject=subject,
                lecturer=lecturer,
                faculty=faculty
            )
            db.session.add(syllabus)

        # --- MainSection & SubSection ---
        for main_section_data in item['main_sections']:
            new_section = MainSection(
                name=main_section_data['name'],
                code=main_section_data['code'],
                position=main_section_data['position'],
                syllabus=syllabus
            )
            db.session.add(new_section)

            for sub_section_data in main_section_data['sub_sections']:
                new_sub_section = None
                if sub_section_data['type'] == 'text':
                    new_sub_section = TextSubSection(
                        name=sub_section_data['name'],
                        content=sub_section_data['content'],
                        position=sub_section_data['position']
                    )

                elif sub_section_data['type'] == 'selection':
                    group_id = sub_section_data['attribute_group_id']
                    selected_ids = sub_section_data['selected_value_ids']
                    print(selected_ids)
                    attribute_group = AttributeGroup.query.get(group_id)
                    selected_values = AttributeValue.query.filter(AttributeValue.id.in_(selected_ids)).all()
                    print(selected_values)
                    new_sub_section = SelectionSubSection(
                        name=sub_section_data['name'],
                        position=sub_section_data['position'],
                        attribute_group=attribute_group,
                        selected_values=selected_values
                    )
                elif sub_section_data['type'] == 'reference':
                    new_sub_section = ReferenceSubSection(
                        name=sub_section_data['name'],
                        position=sub_section_data['position'],
                        reference_code=sub_section_data['reference_code']
                    )

                if new_sub_section:
                    # Gán SubSection vào MainSection cha
                    new_section.sub_sections.append(new_sub_section)
                    db.session.add(new_sub_section)
        # --- Course Objective
        for co in item.get('course_objectives', []):
            name_co = co['name']
            description_co = co['description']
            new_co = CourseObjective(name=name_co, content=description_co, subject=subject)

            for plo_id in co["plos"]:
                plo = db.session.query(ProgrammeLearningOutcome).filter_by(id=plo_id).first()
                new_co.programme_learning_outcomes.append(plo)

            for clo_data in co["clos"]:
                new_clo = CourseLearningOutcome(content=clo_data['description'], course_objective=new_co)
                new_co.course_learning_outcomes.append(new_clo)
                db.session.add(new_clo)

                for rating in clo_data.get('ratings', []):
                    plo_id = rating['plo_id']
                    level = rating['level']

                    plo_obj = db.session.query(ProgrammeLearningOutcome).filter_by(id=plo_id).first()
                    if plo_obj:
                        association = CloPloAssociation(
                            clo=new_clo,
                            plo=plo_obj,
                            rating=level
                        )
                        db.session.add(association)

            db.session.add(new_co)


        # --- Learning Materials ---
        for lm_data in item.get('learning_materials', []):
            type_name = lm_data['type_material']['name']
            lm_type_obj = db.session.query(TypeLearningMaterial).filter_by(name=type_name).first()
            if not lm_type_obj:
                lm_type_obj = TypeLearningMaterial(name=type_name)
                db.session.add(lm_type_obj)

            lm_name = lm_data['name']
            lm_obj = db.session.query(LearningMaterial).filter_by(name=lm_name).first()
            if not lm_obj:
                lm_obj = LearningMaterial(name=lm_name, type_material=lm_type_obj)
                db.session.add(lm_obj)

            if lm_obj not in syllabus.learning_materials:
                syllabus.learning_materials.append(lm_obj)

    try:
        db.session.commit()
        print("✅ Gieo dữ liệu thành công!")
    except Exception as e:
        db.session.rollback()
        print(f"❌ Đã xảy ra lỗi khi commit: {e}")
if __name__ == "__main__":
    with app.app_context():
         seed_data()
         seed_data_2()
         seed_data_3()