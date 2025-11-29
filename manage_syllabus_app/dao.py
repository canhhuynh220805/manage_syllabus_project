from sqlalchemy import cast, Integer

from manage_syllabus_app import db
from manage_syllabus_app.models import User, Syllabus, Faculty, Lecturer, Subject, TypeRequirement, \
    LearningMaterial, TypeLearningMaterial, CourseObjective, CourseLearningOutcome, CloPloAssociation, \
    RequirementSubject, Credit, SubSection, ProgrammeLearningOutcome, TrainingProgram
from werkzeug.security import generate_password_hash, check_password_hash


# =========== CÁC HÀM LIÊN QUAN ĐẾN USER ===========
def get_user_by_id(user_id):
    return User.query.get(int(user_id))

def get_user_by_username(username):
    """Lấy người dùng theo username."""
    return User.query.filter_by(username=username.strip()).first()


def check_password(user, password):
    """Kiểm tra mật khẩu người dùng."""
    if user:
        return check_password_hash(user.password, password)
    return False


def add_user(name, username, password, avatar=None, role='2'):
    """Thêm người dùng mới."""
    hashed_password = generate_password_hash(password)
    new_user = User(name=name, username=username, password=hashed_password, avatar=avatar, role=role)
    db.session.add(new_user)
    db.session.commit()
    return new_user


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
        query = query.filter(Syllabus.structure_file==template)
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

def get_subject_by_id(subject_id):
    return Subject.query.filter_by(id=subject_id).first()

def get_credit_by_id(credit_id):
    return Credit.query.filter_by(id=credit_id).first()

# def get_subsection_by_id(type, id):
#     return type.query.filter_by(id=id).first()

def get_all_type_subjects():
    """Lấy tất cả các loại môn học điều kiện."""
    return TypeRequirement.query.all()


def get_all_learning_material_types():
    """Lấy tất cả các loại tài liệu học tập."""
    return TypeLearningMaterial.query.all()


def get_available_require_subjects(current_subject_id):
    subquery = (
        db.session.query(RequirementSubject.require_subject_id).filter(
            RequirementSubject.subject_id == current_subject_id
        )
    )
    #lấy tất cả các môn ko nằm trong môn đã chọn và ko phải chính môn đó
    available_subjects = db.session.query(Subject).filter(Subject.id != current_subject_id).filter(Subject.id.notin_(subquery)).all()
    return available_subjects


def get_all_plos(plo_ids=None):
    plos = ProgrammeLearningOutcome.query
    if plo_ids:
        plos = plos.filter_by(id=plo_ids)
    return plos.all()

def get_all_cos():
    cos = CourseObjective.query
    return cos.all()

def find_learning_material(name=None, id=None):
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

    plos = db.session.query(ProgrammeLearningOutcome)\
        .join(ProgrammeLearningOutcome.course_objectives)\
        .join(CourseObjective.subject)\
        .join(Subject.syllabuses)\
        .filter(Syllabus.id == syllabus_id)\
        .distinct() \
        .order_by(cast(ProgrammeLearningOutcome.id, Integer))\
        .all()

    return plos

def count_syllabuses(lecturer_id=None):
    """Đếm tổng số đề cương (có thể lọc theo giảng viên)."""
    query = Syllabus.query
    if lecturer_id:
        query = query.filter_by(lecturer_id=lecturer_id)
    return query.count()
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