from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, ForeignKey, Table, Column, Integer, UniqueConstraint, Text
from sqlalchemy.orm import Mapped, relationship, mapped_column
from enum import Enum as UserEnum
from flask_login import UserMixin
from manage_syllabus_app import db, app

# quan hệ nhiều - nhiều giữa đề cương và học liệu
Syllabus_LearningMaterial = Table("syllabus_learning_material",
                                  db.metadata,
                                  Column("syllabus_id", ForeignKey("syllabus.id"), primary_key=True),
                                  Column("learning_material_id", ForeignKey("learning_material.id"), primary_key=True))

# quan hệ nhiều - nhiều giữa tiểu mục lựa chọn và giá trị được chọn của đề cương
SubSection_AttributeValue = Table("subsection_attribute_value",
                                  db.metadata,
                                  Column("subsection_id", ForeignKey("sub_section.id"), primary_key=True),
                                  Column("attribute_value_id", ForeignKey("attribute_value.id"), primary_key=True))

CourseObjective_ProgrammeLearningOutcome = Table("course_objective_programme_learning_outcome",
                                                 db.metadata,
                                                 Column("course_objective_id", ForeignKey("course_objective.id"),
                                                        primary_key=True),
                                                 Column("programme_learning_outcome_id",
                                                        ForeignKey("programme_learning_outcome.id"), primary_key=True))


# LỚP ĐỀ CƯƠNG
class Syllabus(db.Model):
    __tablename__ = 'syllabus'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    main_sections: Mapped[List["MainSection"]] = relationship(
        back_populates="syllabus",
        order_by="MainSection.position",
        cascade="all, delete-orphan",
    )
    # khóa ngoại tham chiếu môn học
    subject_id: Mapped[str] = mapped_column(ForeignKey('subject.id', onupdate='CASCADE'), nullable=False)
    subject: Mapped["Subject"] = relationship(back_populates="syllabuses", lazy=False)
    # khóa ngoại tham chiếu khoa quản lí
    faculty_id: Mapped[int] = mapped_column(ForeignKey('faculty.id'), nullable=False)
    faculty: Mapped["Faculty"] = relationship(back_populates="syllabuses", lazy=False)
    # khóa ngoai tham chiếu giảng viên phụ trách
    lecturer_id: Mapped[int] = mapped_column(ForeignKey('lecturer.id'), nullable=False)
    lecturer: Mapped["Lecturer"] = relationship(back_populates="syllabuses", lazy=False)
    # 1 đề cương xây dựng bởi nhiều học liệu
    learning_materials: Mapped[List["LearningMaterial"]] = relationship(secondary=Syllabus_LearningMaterial,
                                                                        back_populates="syllabuses")
    structure_file: Mapped[Optional[str]] = mapped_column(String(100), default="syllabus_2025.json")

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'subject': self.subject.to_dict(),
            'lecturer': self.lecturer.to_dict(),
            'main parts': self.main_sections.to_dict(),
        }


# LỚP PHẦN CỦA ĐỀ CƯƠNG
class MainSection(db.Model):
    __tablename__ = 'main_section'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    syllabus_id: Mapped[int] = mapped_column(ForeignKey('syllabus.id'), nullable=False)
    syllabus: Mapped["Syllabus"] = relationship(back_populates="main_sections")
    sub_sections: Mapped[List["SubSection"]] = relationship(
        back_populates="main_section",
        order_by="SubSection.position",
        cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'syllabus_id': self.syllabus.id
        }

    __table_args__ = (UniqueConstraint('code', 'syllabus_id', name='uq_code_per_syllabus'),)


# LỚP TIỂU MỤC CHA
class SubSection(db.Model):
    __tablename__ = 'sub_section'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    main_section_id: Mapped[int] = mapped_column(ForeignKey('main_section.id'), nullable=False)
    main_section: Mapped["MainSection"] = relationship(back_populates="sub_sections")
    type: Mapped[str] = mapped_column(String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'sub_section',
        'polymorphic_on': type
    }


# LỚP TIỂU MỤC VĂN BẢN
class TextSubSection(SubSection):
    __tablename__ = 'text_sub_section'
    id: Mapped[int] = mapped_column(ForeignKey('sub_section.id'), primary_key=True, nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text)
    __mapper_args__ = {
        'polymorphic_identity': 'text'
    }


# LỚP TIỂU MỤC LỰA CHỌN
class SelectionSubSection(SubSection):
    __tablename__ = 'selection_sub_section'
    id: Mapped[int] = mapped_column(ForeignKey('sub_section.id'), primary_key=True, nullable=False)

    attribute_group_id: Mapped[int] = mapped_column(ForeignKey('attribute_group.id'), nullable=False)
    attribute_group: Mapped["AttributeGroup"] = relationship(back_populates="selection_sub_sections")
    selected_values: Mapped[List["AttributeValue"]] = relationship(
        secondary=SubSection_AttributeValue,
        back_populates="selection_sub_sections"
    )
    __mapper_args__ = {
        'polymorphic_identity': 'selection'
    }


# --- LỚP MỚI: TIỂU MỤC THAM CHIẾU ---
class ReferenceSubSection(SubSection):
    """
    Tiểu mục này không chứa dữ liệu, chỉ chứa một mã để tham chiếu
    tới một đối tượng dữ liệu phức tạp khác (ví dụ: Credit).
    """
    __tablename__ = 'reference_sub_section'
    id: Mapped[int] = mapped_column(ForeignKey('sub_section.id'), primary_key=True, nullable=False)

    reference_code: Mapped[str] = mapped_column(String(50), nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'reference'
    }


# LỚP NHÓM THUỘC TÍNH
class AttributeGroup(db.Model):
    __tablename__ = 'attribute_group'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name_group: Mapped[str] = mapped_column(String(100), nullable=False)
    attribute_values: Mapped[List["AttributeValue"]] = relationship(back_populates="attribute_group")
    selection_sub_sections: Mapped[List["SelectionSubSection"]] = relationship(back_populates="attribute_group")


# LỚP GIÁ TRỊ CỦA NHÓM THUỘC TÍNH
class AttributeValue(db.Model):
    __tablename__ = 'attribute_value'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name_value: Mapped[str] = mapped_column(String(50), nullable=False)
    attribute_group_id: Mapped[int] = mapped_column(ForeignKey('attribute_group.id'), nullable=False)
    attribute_group: Mapped["AttributeGroup"] = relationship(back_populates="attribute_values")

    selection_sub_sections: Mapped[List["SelectionSubSection"]] = relationship(
        secondary=SubSection_AttributeValue,
        back_populates="selected_values"
    )


# LỚP MÔN HỌC
class Subject(db.Model):
    __tablename__ = 'subject'
    id: Mapped[str] = mapped_column(String(10), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    # 1 môn học có nhiều đề cương
    syllabuses: Mapped[List[Syllabus]] = relationship(back_populates='subject')
    # khóa ngoại tham chiếu tới tín chỉ
    credit_id: Mapped[int] = mapped_column(ForeignKey('credit.id'), nullable=False)
    credit: Mapped["Credit"] = relationship(back_populates="subjects")
    # quan hệ các môn là yêu cầu cho môn này
    required_by_relation: Mapped[List['RequirementSubject']] = relationship(
        foreign_keys='RequirementSubject.subject_id', back_populates="subject",
        cascade="all, delete-orphan")
    # quan hệ các môn mà môn này là điều kiện cho
    required_relation: Mapped[List['RequirementSubject']] = relationship(
        foreign_keys='RequirementSubject.require_subject_id', cascade="all, delete-orphan",
        back_populates="require_subject")
    course_objectives: Mapped[List["CourseObjective"]] = relationship(
        back_populates="subject",
        cascade="all, delete-orphan"
    )

    def __str__(self):
        return self.name

    def to_dict(self):
        """Chuyển đổi đối tượng Subject sang định dạng JSON (dictionary)."""
        return {
            'id': self.id,
            'name': self.name,
            'credit_id': self.credit_id
        }

# LỚP KHOA
class Faculty(db.Model):
    __tablename__ = 'faculty'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    # 1 khoa quản lí nhiều đề cương
    syllabuses: Mapped[List[Syllabus]] = relationship(back_populates='faculty')
    # 1 khoa có nhiều giảng viên
    lecturers: Mapped[List["Lecturer"]] = relationship(back_populates='faculty')

    def __str__(self):
        return self.name


# LỚP GIẢNG VIÊN
class Lecturer(db.Model):
    __tablename__ = 'lecturer'
    # tự cung cấp mã
    # id = Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    # cấp mã tự động để test
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    email: Mapped[str] = mapped_column(String(100), nullable=True)
    room: Mapped[str] = mapped_column(String(200), nullable=True)
    # 1 giảng viên thuộc 1 khoa
    faculty_id: Mapped[int] = mapped_column(ForeignKey('faculty.id'), nullable=False)
    faculty: Mapped[Faculty] = relationship(back_populates="lecturers")
    # 1 giảng viên phụ trách nhiều đề cương
    syllabuses: Mapped[Optional[List[Syllabus]]] = relationship(back_populates='lecturer')
    user: Mapped["User"] = relationship(back_populates="lecturer")  # Mối quan hệ 1-1 ngược lại
    def __str__(self):
        return self.name


# LỚP TÀI LIỆU THAM KHẢO
class LearningMaterial(db.Model):
    __tablename__ = 'learning_material'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    # 1 học liệu chỉ thuộc 1 loại học liệu, khóa ngoại tham chiếu tới loại học liệu
    type_material_id: Mapped[int] = mapped_column(ForeignKey('type_learning_material.id'), nullable=False)
    type_material: Mapped["TypeLearningMaterial"] = relationship(back_populates="learningMaterials")
    # 1 học liệu có thể thuộc nnhiều đề cương
    syllabuses: Mapped[List[Syllabus]] = relationship(secondary=Syllabus_LearningMaterial,
                                                      back_populates='learning_materials')


# LỚP LOẠI TÀI LIỆU THAM KHẢO
class TypeLearningMaterial(db.Model):
    __tablename__ = 'type_learning_material'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    # 1 loại học liệu có nhiều học liệu
    learningMaterials: Mapped[Optional[List["LearningMaterial"]]] = relationship(back_populates="type_material")


# LỚP TÍN CHỈ
class Credit(db.Model):
    __tablename__ = 'credit'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    numberTheory: Mapped[int] = mapped_column(Integer, nullable=False)
    numberPractice: Mapped[int] = mapped_column(Integer, nullable=False)
    hourSelfStudy: Mapped[int] = mapped_column(Integer, nullable=False)
    # 1 tín chỉ thuộc nhiều môn học , có thể có hoặc ko
    subjects: Mapped[List["Subject"]] = relationship(back_populates="credit")

    def getTotalCredit(self):
        return self.numberTheory + self.numberPractice;

    def __str__(self):
        return f"TC: {self.getTotalCredit()} (LT: {self.numberTheory} - TH: {self.numberPractice})"



# LỚP MÔN HỌC ĐIỀU KIỆN
class RequirementSubject(db.Model):
    __tablename__ = 'requirement_subject'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # môn học bị yêu cầu ( có yêu cầu )
    subject_id: Mapped[str] = mapped_column(ForeignKey('subject.id', onupdate='CASCADE'))
    subject: Mapped[Subject] = relationship(foreign_keys=[subject_id], back_populates="required_by_relation")
    # môn học điều kiện
    require_subject_id: Mapped[str] = mapped_column(ForeignKey('subject.id', onupdate='CASCADE'))
    require_subject: Mapped[Subject] = relationship(foreign_keys=[require_subject_id],
                                                    back_populates="required_relation")
    # loại điều kiện
    type_requirement_id: Mapped[int] = mapped_column(ForeignKey("requirement_type.id"), nullable=False)
    type_requirement: Mapped["TypeRequirement"] = relationship(foreign_keys=[type_requirement_id],
                                                               back_populates="requirement_subjects")


# LỚP LOẠI MÔN HỌC ĐIỀU KIỆN
class TypeRequirement(db.Model):
    __tablename__ = 'requirement_type'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)
    # 1 loại môn học điều kiện có nhiều môn học điều kiện
    requirement_subjects: Mapped[List[RequirementSubject]] = relationship(back_populates="type_requirement")


# LỚP MỤC TIÊU MÔN HỌC
class CourseObjective(db.Model):
    __tablename__ = 'course_objective'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    subject_id: Mapped[str] = mapped_column(ForeignKey('subject.id', onupdate="CASCADE"))
    subject: Mapped[Subject] = relationship(back_populates="course_objectives")
    course_learning_outcomes: Mapped[List["CourseLearningOutcome"]] = relationship(
        back_populates="course_objective",
        cascade="all, delete-orphan",
    )
    programme_learning_outcomes: Mapped[List["ProgrammeLearningOutcome"]] = relationship(
        secondary=CourseObjective_ProgrammeLearningOutcome
        , back_populates="course_objectives")


# LỚP CHUẨN ĐẦU RA MÔN HỌC
class CourseLearningOutcome(db.Model):
    __tablename__ = 'course_learning_outcome'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    course_objective: Mapped[CourseObjective] = relationship(back_populates="course_learning_outcomes")
    course_objective_id: Mapped[int] = mapped_column(ForeignKey('course_objective.id'))

    plo_association: Mapped[List["CloPloAssociation"]] = relationship(
        back_populates="clo",
        cascade="all, delete-orphan",
    )


# LỚP PLO
class ProgrammeLearningOutcome(db.Model):
    __tablename__ = 'programme_learning_outcome'
    id: Mapped[str] = mapped_column(String(10), primary_key=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    course_objectives: Mapped[List[CourseObjective]] = relationship(secondary=CourseObjective_ProgrammeLearningOutcome
                                                                    , back_populates="programme_learning_outcomes")

    clo_association: Mapped[List["CloPloAssociation"]] = relationship(back_populates="plo")


# LỚP QUAN HỆ NHIỀU NHIỀU GIỮA CLO VÀ PLO (CÓ ĐIỂM RATING)
class CloPloAssociation(db.Model):
    __tablename__ = 'clo_plo_association'
    clo_id: Mapped[int] = mapped_column(ForeignKey('course_learning_outcome.id'), primary_key=True)
    plo_id: Mapped[str] = mapped_column(ForeignKey('programme_learning_outcome.id'), primary_key=True)
    rating: Mapped[int] = mapped_column(nullable=False)

    clo: Mapped[CourseLearningOutcome] = relationship(back_populates="plo_association")
    plo: Mapped[ProgrammeLearningOutcome] = relationship(back_populates="clo_association")


#========================= USER ===============================

class UserRole(UserEnum):
    ADMIN = 1
    USER = 2


class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(default=True)
    joined_date: Mapped[datetime] = mapped_column(default=datetime.now)
    avatar: Mapped[str] = mapped_column(String(100), nullable=True)
    user_role: Mapped[UserRole] = mapped_column(default=UserRole.USER)
    lecturer_id: Mapped[Optional[int]] = mapped_column(ForeignKey('lecturer.id'), nullable=True)
    lecturer: Mapped[Optional["Lecturer"]] = relationship(back_populates="user")
    def __str__(self):
        return self.username


