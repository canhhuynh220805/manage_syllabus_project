from sqlalchemy import cast, Integer
import hashlib
from manage_syllabus_app import db, app
from manage_syllabus_app.models import User, Syllabus, Faculty, Lecturer, Subject, TypeRequirement, \
    LearningMaterial, TypeLearningMaterial, CourseObjective, CourseLearningOutcome, CloPloAssociation, \
    RequirementSubject, Credit, SubSection, ProgrammeLearningOutcome, TrainingProgram, TemplateSyllabus, TextSubSection, \
    AttributeGroup, AttributeValue, SubSectionAttributeValue, SelectionSubSection, \
    CourseObjectiveProgrammeLearningOutcome, UserRole, Major
from werkzeug.security import generate_password_hash, check_password_hash


# =========== CÁC HÀM LIÊN QUAN ĐẾN USER ===========
def get_user_by_id(user_id):
    return User.query.get(int(user_id))


def get_user_by_username(username):
    return User.query.filter_by(username=username).first()


def auth_user(username, password):
    password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    return User.query.filter(User.username == username.strip(),
                             User.password == password).first()


def add_user(name, email, username, password, role, avatar):
    hashed_password = str(hashlib.md5(password.strip().encode('utf-8')).hexdigest())
    lec = Lecturer.query.filter_by(email=email).first()
    if not lec:
        lec = Lecturer(name=name, email=email)
    new_user = User(name=name, username=username, password=hashed_password, avatar=avatar, role=role, lecturer=lec)
    db.session.add(new_user)
    db.session.commit()
    return new_user


def get_all_user(page=None):
    query = User.query
    if page:
        start = (page - 1) * app.config['PAGE_SIZE']
        query = query.slice(start, start + app.config['PAGE_SIZE'])
    return query.all()


def count_users():
    return User.query.count()


def get_all_roles():
    roles = [role.name for role in UserRole]
    return roles


def change_user_role(user, role_name):
    try:
        role = UserRole[role_name]
        user.user_role = role
        db.session.commit()
        return True
    except Exception as e:
        print(e)
        db.session.rollback()
        return False


# =========== CÁC HÀM LIÊN QUAN ĐẾN SYLLABUS ===========
def get_all_syllabuses(page=None, page_size=None, key=None, year=None, program=None, template=None):
    """Lấy danh sách đề cương (có phân trang thủ công)."""
    query = Syllabus.query
    if key:
        query = query.filter(Syllabus.name.contains(key.strip()))
    if year:
        query = query.join(Syllabus.training_programs).filter(TrainingProgram.academic_year == year)
    if program:
        query = query.filter(Syllabus.training_programs.any(TrainingProgram.name == program))
    if template:
        query = query.filter(Syllabus.structure_file == template)
    if page and page_size:
        start = (page - 1) * page_size
        return query.offset(start).limit(page_size).all()
    return query.all()


def get_syllabuses_by_lecturer_id(lecturer_id, page=None, page_size=None):
    """Lấy danh sách đề cương của giảng viên (có phân trang thủ công)."""
    query = Syllabus.query.filter_by(lecturer_id=lecturer_id)
    if page and page_size:
        start = (page - 1) * page_size
        return query.offset(start).limit(page_size).all()
    return query.all()


def get_syllabus_by_id(syllabus_id):
    """Lấy đề cương theo ID."""
    return Syllabus.query.get_or_404(syllabus_id)


def get_all_faculties():
    """Lấy tất cả các khoa."""
    return Faculty.query.all()


def get_lecturers(lecturer_id=None):
    lecturers = Lecturer.query
    if lecturer_id:
        lecturers = lecturers.filter_by(id=lecturer_id)
    return lecturers.all()


def get_subjects():
    subjects = Subject.query
    return subjects.all()

def count_subjects():
    return Subject.query.count()

def get_subject_by_id(subject_id):
    return Subject.query.filter_by(id=subject_id).first()


def create_subject(id, name, number_theory, number_practice, hour_self_study):
    try:
        subject = Subject(id=id, name=name)
        credit = Credit(numberTheory=number_theory, numberPractice=number_practice, hourSelfStudy=hour_self_study)
        subject.credit = credit
        db.session.add(subject)
        db.session.commit()
        return subject
    except Exception as e:
        print(e)
        db.session.rollback()
        return None


def get_credit_by_id(credit_id):
    return Credit.query.filter_by(id=credit_id).first()


# def get_subsection_by_id(type, id):
#     return type.query.filter_by(id=id).first()

def get_all_type_subjects():
    return TypeRequirement.query.all()


def get_all_learning_material_types():
    return TypeLearningMaterial.query.all()


def get_available_require_subjects(current_subject_id):
    subquery = (
        db.session.query(RequirementSubject.require_subject_id).filter(
            RequirementSubject.subject_id == current_subject_id
        )
    )
    available_subjects = db.session.query(Subject).filter(Subject.id != current_subject_id).filter(
        Subject.id.notin_(subquery)).all()
    return available_subjects


def get_all_plos(plo_ids=None):
    plos = ProgrammeLearningOutcome.query
    if plo_ids:
        plos = plos.filter_by(id=plo_ids)
    return plos.all()


def get_all_cos():
    cos = CourseObjective.query
    return cos.all()


def get_co_by_id(co_id):
    return CourseObjective.query.filter_by(id=co_id).first()


def get_clo_by_id(clo_id):
    return CourseLearningOutcome.query.filter_by(id=clo_id).first()


def get_plo_by_id(plo_id):
    return ProgrammeLearningOutcome.query.filter_by(id=plo_id).first()


def get_learning_material(name=None, id=None):
    lm = LearningMaterial.query
    if name:
        lm = lm.filter_by(name=name)
    if id:
        lm = lm.filter_by(id=id)
    return lm.first()


def get_sorted_plos_for_syllabus(syllabus_id):
    # Xây dựng câu truy vấn:
    # Từ bảng PLO -> Join sang CO -> Join sang Subject -> Join sang Syllabus
    # Lọc theo syllabus_id
    # Sắp xếp theo ID (đã ép kiểu Integer)

    plos = db.session.query(ProgrammeLearningOutcome) \
        .join(ProgrammeLearningOutcome.course_objectives) \
        .join(CourseObjective.subject) \
        .join(Subject.syllabuses) \
        .filter(Syllabus.id == syllabus_id) \
        .distinct() \
        .order_by(cast(ProgrammeLearningOutcome.id, Integer)) \
        .all()

    return plos


def count_syllabuses(lecturer_id=None):
    """Đếm tổng số đề cương (có thể lọc theo giảng viên)."""
    query = Syllabus.query
    if lecturer_id:
        query = query.filter_by(lecturer_id=lecturer_id)
    return query.count()


def get_all_template():
    return TemplateSyllabus.query.all()


def get_template_by_id(template_id):
    return TemplateSyllabus.query.get(template_id)


def get_latest_template():
    return TemplateSyllabus.query.order_by(TemplateSyllabus.id.desc()).first()


def get_all_attribute_groups():
    return AttributeGroup.query.all()


def get_attribute_group_values(group_id, subsection_id):
    subquery = db.session.query(SubSectionAttributeValue.attribute_value_id).filter(
        SubSectionAttributeValue.subsection_id == subsection_id,
    )

    available_values = AttributeValue.query.filter(AttributeValue.attribute_group_id == group_id,
                                                   AttributeValue.id.notin_(subquery)).all()
    return available_values


def get_type_subject(type_id):
    return TypeRequirement.query.get(type_id)

def get_all_majors():
    return Major.query.all()

def get_major_by_id(major_id):
    return Major.query.get(major_id)

def create_major(name, code, faculty_id):
    try:
        major = Major(name=name, code=code, faculty_id=faculty_id)
        db.session.add(major)
        db.session.commit()
        return major
    except Exception as e:
        print(e)


def count_majors():
    return Major.query.count()

def get_all_training_program():
    return TrainingProgram.query.all()

def count_training_programs():
    return TrainingProgram.query.count()

def get_training_program_by_id(training_program_id):
    return TrainingProgram.query.get(training_program_id)

def create_training_program(name, academic_year, major_id, old_program_id):
    try:
        old_program = TrainingProgram.query.get(old_program_id)
        training_program = TrainingProgram(
            name=name,
            academic_year=academic_year,
            major_id=major_id
        )
        training_program.syllabuses = old_program.syllabuses
        db.session.add(training_program)
        db.session.commit()
        return training_program
    except Exception as e:
        print(e)
        db.session.rollback()

def get_years():
    query = db.session.query(TrainingProgram.academic_year).distinct().all()
    return [t.academic_year for t in query]
# =================================================================
# CÁC HÀM CẬP NHẬT VÀ XÓA (UPDATE/DELETE)
# =================================================================
def delete_course_objective_by_id(co_id):
    """Xóa một mục tiêu môn học theo ID."""
    co = db.session.get(CourseObjective, co_id)
    if co:
        db.session.delete(co)
        db.session.commit()
        return True
    return False


def update_text_sub_section(content, subsection=None):
    if content:
        subsection.content = content
        db.session.commit()
        return True
    return False


def update_co(content, co):
    if content:
        co.content = content
        db.session.commit()
        return True
    return False


def update_clo(content, clo):
    if content:
        clo.content = content
        db.session.commit()
        return True
    return False


def update_learning_material(name, material):
    if name:
        material.name = name
        db.session.commit()
        return True
    return False


def add_learning_material(name, type_id, syllabus):
    try:
        type = TypeLearningMaterial.query.get(type_id)
        lm = LearningMaterial.query.filter_by(name=name).first()
        if lm:
            syllabus.learning_materials.append(lm)
        else:
            l = LearningMaterial(name=name, type_material=type)
            db.session.add(l)
            syllabus.learning_materials.append(l)
        db.session.commit()
        return True
    except Exception as e:
        print(e)
        db.session.rollback()
        return False


def remove_learning_material(material, syllabus):
    try:
        syllabus.learning_materials.remove(material)
        db.session.commit()
        return True
    except Exception as e:
        print(e)
        db.session.rollback()
        return False


def add_attribute(subsection_id, attribute_id):
    try:
        new_relation = SubSectionAttributeValue(
            subsection_id=subsection_id,
            attribute_value_id=attribute_id
        )
        db.session.add(new_relation)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        return False


def del_attribute(subsection_id, attribute_id):
    try:
        relation = SubSectionAttributeValue.query.filter_by(subsection_id=subsection_id,
                                                            attribute_value_id=attribute_id).first()
        if relation:
            db.session.delete(relation)
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        return False


def update_credit(credit_id, theory, practice, self_study):
    try:
        credit = Credit.query.get(credit_id)
        if not credit:
            return False
        credit.numberTheory = theory
        credit.numberPractice = practice
        credit.hourSelfStudy = self_study
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        return False


def add_requirement_subject(syllabus, subject_id, type_id):
    try:
        subject_require = Subject.query.get(subject_id)
        type = TypeRequirement.query.get(type_id)
        if not subject_require or not type:
            return False

        res = RequirementSubject(
            subject=syllabus.subject,
            require_subject=subject_require,
            type_requirement=type
        )
        db.session.add(res)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(e)
        return False


def delete_requirement_subject(syllabus, subject_id):
    try:
        require = RequirementSubject.query.filter_by(subject_id=syllabus.subject.id,
                                                     require_subject_id=subject_id).first()
        if require:
            db.session.delete(require)
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        print(e)
        return False


def add_plo_for_co(co, plo):
    try:
        co.programme_learning_outcomes.append(plo)
        clos = co.course_learning_outcomes
        for clo in clos:
            existing_rating = CloPloAssociation.query.filter_by(
                clo_id=clo.id,
                plo_id=plo.id
            ).first()
            if existing_rating:
                return False
            relation = CloPloAssociation(
                clo_id=clo.id,
                plo_id=plo.id,
                rating=0
            )
            db.session.add(relation)
        db.session.commit()
        return True
    except Exception as e:
        print(e)
        return False


def delete_plo_for_co(co, plo):
    try:
        co.programme_learning_outcomes.remove(plo)
        db.session.commit()
        return True
    except Exception as e:
        print(e)
        return False


def get_plos(plo_ids):
    return ProgrammeLearningOutcome.query.filter(
        ProgrammeLearningOutcome.id.in_(plo_ids)
    ).all()


def add_clo_for_co(co, clo):
    try:
        co.course_learning_outcomes.append(clo)
        plos = co.programme_learning_outcomes
        for plo in plos:
            existing_rating = CloPloAssociation.query.filter_by(
                clo_id=clo.id,
                plo_id=plo.id
            ).first()
            if existing_rating:
                continue
            relation = CloPloAssociation(
                clo_id=clo.id,
                plo_id=plo.id,
                rating=0
            )
            db.session.add(relation)
        db.session.commit()
        return True
    except Exception as e:
        print(e)
        return False


def delete_clo_for_co(co, clo):
    try:
        co.course_learning_outcomes.remove(clo)
        db.session.commit()
        return True
    except Exception as e:
        print(e)
        return False


def update_rating(clo_id, plo_id, rating):
    try:
        relation = CloPloAssociation.query.filter_by(
            clo_id=clo_id,
            plo_id=plo_id,
        ).first()
        if relation:
            relation.rating = rating
            db.session.commit()
            return True
        return False
    except Exception as e:
        db.session.rollback()
        print(e)
        return False

# if __name__ == '__main__':
#     with app.app_context():
#         u = User.query.get(2)
#         print(u.lecturer.email)
