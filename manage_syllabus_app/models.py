import hashlib
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON, Boolean, DateTime, Table, UniqueConstraint, \
    Enum, Float
from sqlalchemy.orm import relationship, backref
import enum
from manage_syllabus_app import db, app


# =============================================================================
# BASE MODEL (Lớp cha dùng chung)
# =============================================================================
class BaseModel(db.Model):
    __abstract__ = True
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)

    def __str__(self):
        return self.name


# =============================================================================
# ASSOCIATION MODELS (Bảng trung gian dạng Class)
# Thay thế Table bằng Model để chuẩn OOP và dễ mở rộng
# =============================================================================

class SyllabusLearningMaterial(db.Model):
    __tablename__ = 'syllabus_learning_material'
    syllabus_id = Column(Integer, ForeignKey('syllabus.id'), primary_key=True)
    learning_material_id = Column(Integer, ForeignKey('learning_material.id'), primary_key=True)


class SubSectionAttributeValue(db.Model):
    subsection_id = Column(Integer, ForeignKey('sub_section.id'), primary_key=True)
    attribute_value_id = Column(Integer, ForeignKey('attribute_value.id'), primary_key=True)


class CourseObjectiveProgrammeLearningOutcome(db.Model):
    course_objective_id = Column(Integer, ForeignKey('course_objective.id', ondelete='CASCADE'), primary_key=True)
    programme_learning_outcome_id = Column(Integer, ForeignKey('programme_learning_outcome.id', ondelete='CASCADE'),
                                           primary_key=True)


class TrainingProgramSyllabus(db.Model):
    training_program_id = Column(Integer, ForeignKey('training_program.id'), primary_key=True)
    syllabus_id = Column(Integer, ForeignKey('syllabus.id'), primary_key=True)


class MethodCourseLearningOutcome(db.Model):
    method_id = Column(Integer, ForeignKey('method.id', ondelete='CASCADE'), primary_key=True)
    clo_id = Column(Integer, ForeignKey('course_learning_outcome.id', ondelete='CASCADE'), primary_key=True)


class TeachingSessionCourseLearningOutcome(db.Model):
    teaching_session_id = Column(Integer, ForeignKey('teaching_session.id', ondelete='CASCADE'), primary_key=True)
    clo_id = Column(Integer, ForeignKey('course_learning_outcome.id', ondelete='CASCADE'), primary_key=True)

class TeachingSessionAssessment(db.Model):
    teaching_session_id = Column(Integer, ForeignKey('teaching_session.id', ondelete='CASCADE'), primary_key=True)
    assessment_id = Column(Integer, ForeignKey('assessment.id', ondelete='CASCADE'), primary_key=True)

class TeachingSessionLearningMaterial(db.Model):
    teaching_session_id = Column(Integer, ForeignKey('teaching_session.id', ondelete='CASCADE'), primary_key=True)
    learning_material_id = Column(Integer, ForeignKey('learning_material.id', ondelete='CASCADE'), primary_key=True)

# =============================================================================
# MODELS CHÍNH
# =============================================================================

class TemplateSyllabus(BaseModel):
    name = Column(String(100), nullable=False, unique=True)
    structure = Column(JSON, nullable=False)
    # Quan hệ
    syllabuses = relationship('Syllabus', backref='template', lazy=True)


class Syllabus(BaseModel):
    name = Column(String(100), unique=True)
    status = Column(String(100), nullable=True)
    created_date = Column(DateTime, default=datetime.now)
    structure_file = Column(String(100), default="syllabus_2025.json")
    # Khóa ngoại
    subject_id = Column(String(10), ForeignKey('subject.id', onupdate='CASCADE'), nullable=False)
    faculty_id = Column(Integer, ForeignKey('faculty.id'), nullable=False)
    lecturer_id = Column(Integer, ForeignKey('lecturer.id'), nullable=False)
    template_id = Column(Integer, ForeignKey('template_syllabus.id'), nullable=False)
    # Quan hệ 1-N (Main Sections)
    main_sections = relationship('MainSection', backref='syllabus', lazy=True, cascade="all, delete-orphan",
                                 order_by="MainSection.position")
    # Quan hệ N-N (Learning Materials) - Dùng secondary là tên bảng (string)
    learning_materials = relationship('LearningMaterial', secondary='syllabus_learning_material',
                                      backref='syllabuses', lazy=True)
    assessments = relationship('Assessment', backref='syllabus', lazy=True)
    teaching_sessions = relationship('TeachingSession', backref='syllabus', lazy=True,
                                     cascade="all, delete-orphan", order_by="TeachingSession.session_no")
    start_date_edition = Column(DateTime, default=datetime.now)
    end_date_edition = Column(DateTime, default=datetime.now)

    def to_structure_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'subject': self.subject.to_dict(),
            'faculty': self.faculty.to_dict(),
            'lecturer': self.lecturer.to_dict(),
            'main_sections': [ms.to_dict() for ms in self.main_sections],
            'course_objectives': [co.to_dict() for co in self.subject.course_objectives],
            'learning_materials': [lm.to_dict() for lm in self.learning_materials]
        }

# =============================================================================
# CÁC MODEL BÀI ĐÁNH GIÁ...
# =============================================================================

class Assessment(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    syllabus_id = Column(Integer, ForeignKey(Syllabus.id), nullable=False)
    type_assessment_id = Column(Integer, ForeignKey('type_assessment.id'), nullable=False)
    assessment_methods = relationship('Method', backref='assessment', lazy=True, cascade="all, delete-orphan")
    teaching_sessions = relationship('TeachingSessionAssessment', backref='assessment', lazy=True)
    def get_total_weight(self):
        return sum(m.weight for m in self.assessment_methods if m.weight)


class TypeAssessment(BaseModel):
    assessments = relationship('Assessment', backref='type_assessment', lazy=True)

    def __str__(self):
        return self.name


class Method(BaseModel):
    assessment_id = Column(Integer, ForeignKey('assessment.id', ondelete='CASCADE'), nullable=False)
    time = Column(Text, nullable=True)
    weight = Column(Integer, nullable=True)
    course_learning_outcomes = relationship('MethodCourseLearningOutcome', backref='method', lazy=True,
                                            cascade="all, delete-orphan")

# =============================================================================
# CÁC MODEL TIỂU MỤC...
# =============================================================================

class MainSection(BaseModel):
    code = Column(String(50), nullable=False)
    position = Column(Integer, default=1, nullable=False)
    syllabus_id = Column(Integer, ForeignKey('syllabus.id'), nullable=False)
    sub_sections = relationship('SubSection', backref='main_section', lazy=True, cascade="all, delete-orphan",
                                order_by="SubSection.position")
    __table_args__ = (UniqueConstraint('code', 'syllabus_id', name='uq_code_per_syllabus'),)

    def to_dict(self):
        return {
            'name': self.name,
            'code': self.code,
            'position': self.position,
            'sub_sections': [sub.to_dict() for sub in self.sub_sections],
        }


# Kế thừa đa hình (Polymorphism)
class SubSection(BaseModel):
    position = Column(Integer, default=1, nullable=False)
    type = Column(String(50))
    code = Column(String(50), nullable=False)
    main_section_id = Column(Integer, ForeignKey('main_section.id'), nullable=False)
    __mapper_args__ = {
        'polymorphic_identity': 'sub_section',
        'polymorphic_on': type
    }

    def to_dict(self):
        data = {
            'name': self.name,
            'code': self.code,
            'position': self.position,
            'type': self.type,
        }
        return data

    @property
    def template_name(self):
        return self.type


class TextSubSection(SubSection):
    id = Column(Integer, ForeignKey('sub_section.id'), primary_key=True)
    content = Column(Text, nullable=True)
    display_mode = Column(String(50), default="input")
    place_holder = Column(String(100), nullable=True)
    __mapper_args__ = {
        'polymorphic_identity': 'text'
    }

    @property
    def template_name(self):
        return self.display_mode if self.display_mode else "input"

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'content': self.content,
            'display_mode': self.display_mode,
            'placeholder': self.place_holder,
        })
        return data


class SelectionSubSection(SubSection):
    id = Column(Integer, ForeignKey('sub_section.id'), primary_key=True)
    attribute_group_id = Column(Integer, ForeignKey('attribute_group.id'), nullable=False)
    # Quan hệ lấy các giá trị đã chọn (N-N)
    selected_values = relationship('AttributeValue', secondary='sub_section_attribute_value', lazy=True)
    # Quan hệ tới nhóm thuộc tính (N-1)
    attribute_group = relationship('AttributeGroup', backref='selection_sub_sections', lazy=True)
    __mapper_args__ = {
        'polymorphic_identity': 'selection'
    }

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'attribute_group_id': self.attribute_group_id,
            'selected_value_ids': [value.id for value in self.selected_values],
        })
        return data


class ReferenceSubSection(SubSection):
    id = Column(Integer, ForeignKey('sub_section.id'), primary_key=True)
    reference_code = Column(String(50), nullable=False)
    __mapper_args__ = {
        'polymorphic_identity': 'reference'
    }

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'reference_code': self.reference_code,
        })
        return data


class TableSubSection(SubSection):
    id = Column(Integer, ForeignKey('sub_section.id'), primary_key=True)
    data = Column(JSON, nullable=False)
    __mapper_args__ = {
        'polymorphic_identity': 'table'
    }

    def to_dict(self):
        data = super().to_dict()
        data.update({
            'data': self.data,
        })
        return data


# =============================================================================
# CÁC MODEL MÔN HỌC, KHOA, GIẢNG VIÊN...
# =============================================================================

class Subject(db.Model):
    id = Column(String(10), primary_key=True)
    name = Column(String(100), unique=True)
    credit_id = Column(Integer, ForeignKey('credit.id'), nullable=False, unique=True)
    # Quan hệ
    syllabuses = relationship('Syllabus', backref='subject', lazy=True)
    course_objectives = relationship('CourseObjective', backref='subject', lazy=True, cascade="all, delete-orphan")
    # Quan hệ đệ quy (Môn tiên quyết)
    required_by_relation = relationship('RequirementSubject',
                                        foreign_keys='RequirementSubject.subject_id',
                                        backref='subject', cascade="all, delete-orphan")
    required_relation = relationship('RequirementSubject',
                                     foreign_keys='RequirementSubject.require_subject_id',
                                     backref='require_subject', cascade="all, delete-orphan")

    def __str__(self):
        return self.name

    def to_dict(self):
        required_subjects = []
        for req in self.required_relation:
            required_subjects.append({
                "require_subject_id": req.require_subject.id,
                "require_subject_name": req.require_subject.name,
                "type_requirement": req.type_requirement.name
            })
        return {
            'id': self.id,
            'name': self.name,
            'credit': self.credit.to_dict(),
            'required_subjects': required_subjects,
        }


class Faculty(BaseModel):
    name = Column(String(100), unique=True)
    syllabuses = relationship('Syllabus', backref='faculty', lazy=True)
    lecturers = relationship('Lecturer', backref='faculty', lazy=True)
    majors = relationship('Major', backref='faculty', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
        }


class Lecturer(BaseModel):
    name = Column(String(100), unique=True)
    email = Column(String(100), nullable=True)
    room = Column(String(200), nullable=True)
    faculty_id = Column(Integer, ForeignKey('faculty.id'), nullable=False)
    syllabuses = relationship('Syllabus', backref='lecturer', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'room': self.room,
        }


class LearningMaterial(BaseModel):
    name = Column(String(100), unique=True)
    type_material_id = Column(Integer, ForeignKey('type_learning_material.id'), nullable=False)
    teaching_sessions = relationship('TeachingSessionLearningMaterial', backref='learning_material', lazy=True)
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type_material": self.type_material.to_dict(),
        }


class TypeLearningMaterial(BaseModel):
    name = Column(String(100), unique=True)
    learning_materials = relationship('LearningMaterial', backref='type_material', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
        }


class Credit(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    numberTheory = Column(Integer, nullable=False)
    numberPractice = Column(Integer, nullable=False)
    hourSelfStudy = Column(Integer, nullable=False)
    subject = relationship('Subject', backref=backref('credit', uselist=False), uselist=False)

    def getTotalCredit(self):
        return self.numberTheory + self.numberPractice

    def __str__(self):
        return f"TC: {self.getTotalCredit()} (LT: {self.numberTheory} - TH: {self.numberPractice})"

    def to_dict(self):
        return {
            'number_theory': self.numberTheory,
            'number_practice': self.numberPractice,
            'hour_self_study': self.hourSelfStudy,
        }


class Major(BaseModel):
    name = Column(String(150), nullable=False, unique=True)
    code = Column(String(50), nullable=False, unique=True)
    faculty_id = Column(Integer, ForeignKey('faculty.id'))
    training_programs = relationship('TrainingProgram', backref='major', lazy=True)


class TrainingProgram(BaseModel):
    name = Column(String(150), nullable=False)
    academic_year = Column(Integer, nullable=False)
    major_id = Column(Integer, ForeignKey('major.id'))
    # Quan hệ N-N với Syllabus thông qua bảng trung gian (class model)
    syllabuses = relationship('Syllabus', secondary='training_program_syllabus', backref='training_programs',
                              lazy=True)


# =============================================================================
# CÁC LỚP PHỤ TRỢ (Attribute, PLO, CLO, Requirement)
# =============================================================================

class AttributeGroup(BaseModel):
    attribute_values = relationship('AttributeValue', backref='attribute_group', lazy=True)


class AttributeValue(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name_value = Column(String(50), nullable=False)
    attribute_group_id = Column(Integer, ForeignKey('attribute_group.id'), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "name_value": self.name_value,
        }


class RequirementSubject(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(String(10), ForeignKey('subject.id', onupdate='CASCADE'))
    require_subject_id = Column(String(10), ForeignKey('subject.id', onupdate='CASCADE'))
    type_requirement_id = Column(Integer, ForeignKey("requirement_type.id"), nullable=False)


class TypeRequirement(BaseModel):
    __tablename__ = 'requirement_type'
    name = Column(String(30), unique=True)
    requirement_subjects = relationship('RequirementSubject', backref='type_requirement', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
        }


class CourseObjective(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    subject_id = Column(String(10), ForeignKey('subject.id', onupdate="CASCADE"))
    course_learning_outcomes = relationship('CourseLearningOutcome', backref='course_objective', lazy=True,
                                            cascade="all, delete-orphan")
    # Quan hệ N-N với PLO
    programme_learning_outcomes = relationship('ProgrammeLearningOutcome',
                                               secondary='course_objective_programme_learning_outcome',
                                               backref='course_objectives', lazy=True, passive_deletes=True)

    def to_dict(self):
        return {
            "id": self.id,
            "description": self.content,
            'plos': [plo.id for plo in self.programme_learning_outcomes],
            'clos': [clo.to_dict() for clo in self.course_learning_outcomes],
        }


class CourseLearningOutcome(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    course_objective_id = Column(Integer, ForeignKey('course_objective.id'))
    # Quan hệ custom association (CLO - PLO - Rating)
    plo_association = relationship('CloPloAssociation', backref='clo', lazy=True, cascade="all, delete-orphan")
    methods = relationship('MethodCourseLearningOutcome', backref="course_learning_outcome")
    teaching_sessions = relationship('TeachingSessionCourseLearningOutcome', backref='course_learning_outcome')
    def to_dict(self):
        rating = []
        for asso in self.plo_association:
            rating.append({
                'plo_id': asso.plo_id,
                'level': asso.rating
            })
        return {
            'description': self.content,
            'ratings': rating,
        }


class ProgrammeLearningOutcome(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(Text, nullable=False)
    clo_association = relationship('CloPloAssociation', backref='plo', lazy=True)


# Bảng liên kết CLO-PLO có thêm cột rating (Association Object)
class CloPloAssociation(db.Model):
    clo_id = Column(Integer, ForeignKey('course_learning_outcome.id', ondelete='CASCADE'), primary_key=True)
    plo_id = Column(Integer, ForeignKey('programme_learning_outcome.id', ondelete='CASCADE'), primary_key=True)
    rating = Column(Integer, nullable=False)


# =============================================================================
# CÁC MODEL KẾ HOẠCH GIẢNG DẠY...
# =============================================================================

class ScheduleGroup(BaseModel):
    teaching_sessions = relationship('TeachingSession', backref='schedule_group', lazy=True)
    def get_total_hours(self):
        return sum([s.offline_hours + s.online_hours + s.self_study_hours for s in self.teaching_sessions])

class TeachingSession(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    syllabus_id = Column(Integer, ForeignKey('syllabus.id', ondelete='CASCADE'), nullable=False)
    schedule_group_id = Column(Integer, ForeignKey('schedule_group.id', ondelete='CASCADE'), nullable=False)
    session_no = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)

    offline_activity = Column(Text, nullable=True)
    offline_hours = Column(Float, default=0)

    online_activity = Column(Text, nullable=True)
    online_hours = Column(Float, default=0)

    self_study_activity = Column(Text, nullable=True)
    self_study_hours = Column(Float, default=0)

    course_learning_outcomes = relationship('TeachingSessionCourseLearningOutcome', backref='teaching_session', lazy=True, cascade="all, delete-orphan")
    assessments = relationship('TeachingSessionAssessment', backref='teaching_session', lazy=True, cascade="all, delete-orphan")
    learning_materials = relationship('TeachingSessionLearningMaterial', backref='teaching_session', lazy=True, cascade="all, delete-orphan")

# =============================================================================
# USER & ROLE
# =============================================================================

class UserRole(enum.Enum):
    ADMIN = 1
    USER = 2
    SPECIALIST = 3


class User(BaseModel, UserMixin):
    username = Column(String(50), nullable=False, unique=True)
    password = Column(Text, nullable=False)
    active = Column(Boolean, default=True)
    joined_date = Column(DateTime, default=datetime.now)
    avatar = Column(String(100), nullable=True)
    user_role = Column(Enum(UserRole), default=UserRole.USER)
    lecturer_id = Column(Integer, ForeignKey('lecturer.id'), nullable=True)
    lecturer = relationship('Lecturer', backref=backref('user', uselist=False), lazy=True)

    def __str__(self):
        return self.username


if __name__ == "__main__":
    with app.app_context():
        t = TemplateSyllabus.query.first()
        print(t.structure)
