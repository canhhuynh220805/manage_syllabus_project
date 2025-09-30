from manage_syllabus_app import db
from manage_syllabus_app.models import User, Syllabus, Faculty, Lecturer, Subject, TypeRequirement, \
    LearningMaterial, TypeLearningMaterial, CourseObjective, CourseLearningOutcome, CloPloAssociation, RequirementSubject
from werkzeug.security import generate_password_hash, check_password_hash


# =========== CÁC HÀM LIÊN QUAN ĐẾN USER ===========
def get_user_by_username(username):
    """Lấy người dùng theo username."""
    return User.query.filter_by(username=username).first()


def check_password(user, password):
    """Kiểm tra mật khẩu người dùng."""
    if user:
        return check_password_hash(user.password, password)
    return False


def add_user(name, username, password, avatar=None, role='LECTURER'):
    """Thêm người dùng mới."""
    hashed_password = generate_password_hash(password)
    new_user = User(name=name, username=username, password=hashed_password, avatar=avatar, role=role)
    db.session.add(new_user)
    db.session.commit()
    return new_user


# =========== CÁC HÀM LIÊN QUAN ĐẾN SYLLABUS ===========
def get_all_syllabuses():
    """Lấy tất cả đề cương."""
    return Syllabus.query.all()


def get_syllabus_by_id(syllabus_id):
    """Lấy đề cương theo ID."""
    return Syllabus.query.get_or_404(syllabus_id)


def get_all_faculties():
    """Lấy tất cả các khoa."""
    return Faculty.query.all()


def get_all_lecturers():
    """Lấy tất cả giảng viên."""
    return Lecturer.query.all()


def get_all_subjects():
    """Lấy tất cả môn học."""
    return Subject.query.all()


def get_all_type_subjects():
    """Lấy tất cả các loại môn học điều kiện."""
    return TypeRequirement.query.all()


def get_all_learning_material_types():
    """Lấy tất cả các loại tài liệu học tập."""
    return TypeLearningMaterial.query.all()

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