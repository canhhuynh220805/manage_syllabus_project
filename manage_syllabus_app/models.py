import hashlib
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON, Boolean, DateTime, Table, UniqueConstraint, Enum
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
    syllabus_id = Column(Integer, ForeignKey('syllabus.id'), primary_key=True)
    learning_material_id = Column(Integer, ForeignKey('learning_material.id'), primary_key=True)


class SubSectionAttributeValue(db.Model):
    subsection_id = Column(Integer, ForeignKey('sub_section.id'), primary_key=True)
    attribute_value_id = Column(Integer, ForeignKey('attribute_value.id'), primary_key=True)


class CourseObjectiveProgrammeLearningOutcome(db.Model):
    course_objective_id = Column(Integer, ForeignKey('course_objective.id'), primary_key=True)
    programme_learning_outcome_id = Column(Integer, ForeignKey('programme_learning_outcome.id'),
                                           primary_key=True)


class TrainingProgramSyllabus(db.Model):
    training_program_id = Column(Integer, ForeignKey('training_program.id'), primary_key=True)
    syllabus_id = Column(Integer, ForeignKey('syllabus.id'), primary_key=True)


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


class MainSection(BaseModel):
    code = Column(String(50), nullable=False)
    position = Column(Integer, default=1, nullable=False)
    syllabus_id = Column(Integer, ForeignKey('syllabus.id'), nullable=False)
    sub_sections = relationship('SubSection', backref='main_section', lazy=True, cascade="all, delete-orphan",
                                order_by="SubSection.position")
    __table_args__ = (UniqueConstraint('code', 'syllabus_id', name='uq_code_per_syllabus'),)


# Kế thừa đa hình (Polymorphism)
class SubSection(BaseModel):
    position = Column(Integer, default=1, nullable=False)
    type = Column(String(50))  # Cột phân loại
    main_section_id = Column(Integer, ForeignKey('main_section.id'), nullable=False)
    __mapper_args__ = {
        'polymorphic_identity': 'sub_section',
        'polymorphic_on': type
    }


class TextSubSection(SubSection):
    id = Column(Integer, ForeignKey('sub_section.id'), primary_key=True)
    content = Column(Text, nullable=True)
    __mapper_args__ = {
        'polymorphic_identity': 'text'
    }


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


class ReferenceSubSection(SubSection):
    id = Column(Integer, ForeignKey('sub_section.id'), primary_key=True)
    reference_code = Column(String(50), nullable=False)
    __mapper_args__ = {
        'polymorphic_identity': 'reference'
    }


# =============================================================================
# CÁC MODEL MÔN HỌC, KHOA, GIẢNG VIÊN...
# =============================================================================

class Subject(db.Model):
    id = Column(String(10), primary_key=True)
    name = Column(String(100), unique=True)
    credit_id = Column(Integer, ForeignKey('credit.id'), nullable=False)
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


class Faculty(BaseModel):
    name = Column(String(100), unique=True)
    syllabuses = relationship('Syllabus', backref='faculty', lazy=True)
    lecturers = relationship('Lecturer', backref='faculty', lazy=True)
    majors = relationship('Major', backref='faculty', lazy=True)


class Lecturer(BaseModel):
    name = Column(String(100), unique=True)
    email = Column(String(100), nullable=True)
    room = Column(String(200), nullable=True)
    faculty_id = Column(Integer, ForeignKey('faculty.id'), nullable=False)
    syllabuses = relationship('Syllabus', backref='lecturer', lazy=True)


class LearningMaterial(BaseModel):
    name = Column(String(100), unique=True)
    type_material_id = Column(Integer, ForeignKey('type_learning_material.id'), nullable=False)


class TypeLearningMaterial(BaseModel):
    name = Column(String(100), unique=True)
    learning_materials = relationship('LearningMaterial', backref='type_material', lazy=True)


class Credit(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    numberTheory = Column(Integer, nullable=False)
    numberPractice = Column(Integer, nullable=False)
    hourSelfStudy = Column(Integer, nullable=False)
    subjects = relationship('Subject', backref='credit', lazy=True)

    def getTotalCredit(self):
        return self.numberTheory + self.numberPractice

    def __str__(self):
        return f"TC: {self.getTotalCredit()} (LT: {self.numberTheory} - TH: {self.numberPractice})"


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
    name_group = Column(String(100), nullable=False)
    attribute_values = relationship('AttributeValue', backref='attribute_group', lazy=True)


class AttributeValue(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    name_value = Column(String(50), nullable=False)
    attribute_group_id = Column(Integer, ForeignKey('attribute_group.id'), nullable=False)


class RequirementSubject(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(String(10), ForeignKey('subject.id', onupdate='CASCADE'))
    require_subject_id = Column(String(10), ForeignKey('subject.id', onupdate='CASCADE'))
    type_requirement_id = Column(Integer, ForeignKey("requirement_type.id"), nullable=False)


class TypeRequirement(BaseModel):
    __tablename__ = 'requirement_type'
    name = Column(String(30), unique=True)
    requirement_subjects = relationship('RequirementSubject', backref='type_requirement', lazy=True)


class CourseObjective(BaseModel):
    content = Column(Text, nullable=False)
    subject_id = Column(String(10), ForeignKey('subject.id', onupdate="CASCADE"))
    course_learning_outcomes = relationship('CourseLearningOutcome', backref='course_objective', lazy=True,
                                            cascade="all, delete-orphan")
    # Quan hệ N-N với PLO
    programme_learning_outcomes = relationship('ProgrammeLearningOutcome',
                                               secondary='course_objective_programme_learning_outcome',
                                               backref='course_objectives', lazy=True)


class CourseLearningOutcome(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)
    course_objective_id = Column(Integer, ForeignKey('course_objective.id'))
    # Quan hệ custom association (CLO - PLO - Rating)
    plo_association = relationship('CloPloAssociation', backref='clo', lazy=True, cascade="all, delete-orphan")


class ProgrammeLearningOutcome(db.Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(Text, nullable=False)
    clo_association = relationship('CloPloAssociation', backref='plo', lazy=True)


# Bảng liên kết CLO-PLO có thêm cột rating (Association Object)
class CloPloAssociation(db.Model):
    clo_id = Column(Integer, ForeignKey('course_learning_outcome.id'), primary_key=True)
    plo_id = Column(Integer, ForeignKey('programme_learning_outcome.id'), primary_key=True)
    rating = Column(Integer, nullable=False)


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
        db.create_all()
        print("Database initialized successfully!")
