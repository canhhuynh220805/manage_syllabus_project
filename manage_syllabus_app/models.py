from typing import List, Optional

from sqlalchemy import String, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.testing.schema import mapped_column
from manage_syllabus_app import db, app

# quan hệ nhiều - nhiều giữa đề cương và học liệu
Syllabus_LearningMaterial = Table("syllabus_learning_material",
                                  db.metadata,
                                  Column("syllabus_id", ForeignKey("syllabus.id"), primary_key=True),
                                  Column("learning_material_id", ForeignKey("learning_material.id"), primary_key=True))


# quan hệ nhiều nhiều giữa môn học và các thuộc tính, vd 1 môn học có thuộc tính sau: ngôn ngữ giảng dạy là tiếng việt
# hình thức dạy là onl , thuộc thành phần kiến thức nào, ngược lại ngôn ngữ giảng dạy tiếng việt có thể thuộc nhiều môn học

# Subject_PropertyValue = Table("subject_property_value",
#                               db.metadata,
#                               Column("subject_id", ForeignKey("subject.id"), primary_key=True),
#                               Column("property_value_id", ForeignKey("property_value.id"), primary_key=True))


class Syllabus(db.Model):
    __tablename__ = 'syllabus'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    main_parts : Mapped[List["MainPart"]] = relationship(back_populates="syllabus")
    # khóa ngoại tham chiếu môn học
    subject_id: Mapped[str] = mapped_column(ForeignKey('subject.id'), nullable=False)
    subject: Mapped["Subject"] = relationship(back_populates="syllabuses")
    # khóa ngoại tham chiếu khoa quản lí
    faculty_id: Mapped[int] = mapped_column(ForeignKey('faculty.id'), nullable=False)
    faculty: Mapped["Faculty"] = relationship(back_populates="syllabuses")
    # khóa ngoai tham chiếu giảng viên phụ trách
    lecturer_id: Mapped[int] = mapped_column(ForeignKey('lecturer.id'), nullable=False)
    lecturer: Mapped["Lecturer"] = relationship(back_populates="syllabuses")
    # 1 đề cương xây dựng bởi nhiều học liệu
    learning_materials: Mapped[List["LearningMaterial"]] = relationship(secondary=Syllabus_LearningMaterial,
                                                                        back_populates="syllabuses")


class MainPart(db.Model):
    __tablename__ = 'main_part'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    syllabus_id: Mapped[int] = mapped_column(ForeignKey('syllabus.id'), nullable=False)
    syllabus: Mapped["Syllabus"] = relationship(back_populates="main_parts")


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
        foreign_keys=['RequirementSubject.subject_id'], back_populates="subject",
        cascade="all, delete-orphan")
    # quan hệ các môn mà môn này là điều kiện cho
    required_relation: Mapped[List['RequirementSubject']] = relationship(
        foreign_keys=['RequirementSubject.require_subject_id'], back_populates="require_subject",
        cascade="all, delete-orphan")
    # # 1 môn học có nhều thuộc tính
    # property_values = Mapped[List['PropertyValue']] = relationship(secondary=Subject_PropertyValue,
    #                                                                back_populates="subjects")


class Faculty(db.Model):
    __tablename__ = 'faculty'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    # 1 khoa quản lí nhiều đề cương
    syllabuses: Mapped[List[Syllabus]] = relationship(back_populates='faculty')
    # 1 khoa có nhiều giảng viên
    lecturers: Mapped[List["Lecturer"]] = relationship(back_populates='faculty')


class Lecturer(db.Model):
    __tablename__ = 'lecturer'
    # tự cung cấp mã
    # id = Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    # cấp mã tự động để test
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    # 1 giảng viên thuộc 1 khoa
    faculty_id: Mapped[int] = mapped_column(ForeignKey('faculty.id'), nullable=False)
    faculty: Mapped[Faculty] = relationship(back_populates="lecturers")
    # 1 giảng viên phụ trách nhiều đề cương
    syllabuses: Mapped[Optional[List[Syllabus]]] = relationship(back_populates='lecturer')


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


class TypeLearningMaterial(db.Model):
    __tablename__ = 'type_learning_material'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    # 1 loại học liệu có nhiều học liệu
    learningMaterials: Mapped[Optional[List["LearningMaterial"]]] = relationship(back_populates="type_material")


class Credit(db.Model):
    __tablename__ = 'credit'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    numberTheory: Mapped[int] = mapped_column(nullable=False)
    numberPractice: Mapped[int] = mapped_column(nullable=False)
    hourSelfStudy: Mapped[int] = mapped_column(nullable=False)
    # 1 tín chỉ thuộc nhiều môn học , có thể có hoặc ko
    subjects: Mapped[List["Subject"]] = relationship(back_populates="credit")

    def getTotalCredit(self):
        return self.numberTheory + self.numberPractice;


class RequirementSubject(db.Model):
    __tablename__ = 'requirement_subject'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # môn học bị yêu cầu ( có yêu cầu )
    subject_id: Mapped[str] = mapped_column(ForeignKey('subject.id'), primary_key=True)
    subject: Mapped[Subject] = relationship(foreign_keys=[subject_id], back_populates="required_by_relation")
    # môn học điều kiện
    require_subject_id: Mapped[str] = mapped_column(ForeignKey('subject.id'), primary_key=True)
    require_subject: Mapped[Subject] = relationship(foreign_keys=[require_subject_id],
                                                    back_populates="required_relation")
    # loại điều kiện
    type_requirement_id: Mapped[int] = mapped_column(ForeignKey("requirement_type.id"), nullable=False)
    type_requirement: Mapped["TypeRequirement"] = relationship(foreign_keys=[type_requirement_id],
                                                               back_populates="requirement_subjects")


class TypeRequirement(db.Model):
    __tablename__ = 'requirement_type'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)
    # 1 loại môn học điều kiện có nhiều môn học điều kiện
    requirement_subjects: Mapped[List[RequirementSubject]] = relationship(back_populates="type_requirement")

# class PropertyGroup(db.Model):
#     __tablename__ = 'property_group'
#     id = Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
#     name = Mapped[str] = mapped_column(String(20), nullable=False)
#     # 1 nhóm thuộc tính có nhiều giá trị thuộc tính cùng loại với nhóm
#     property_values = Mapped[List["PropertyValue"]] = relationship(back_populates="property_group")
#
#
# class PropertyValue(db.Model):
#     __tablename__ = 'property_value'
#     id = Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
#     value = Mapped[str] = mapped_column(String(20), nullable=False)
#     # 1 giá trị thuộc tính thuộc 1 nhóm thuộc tính
#     property_group_id = Mapped[int] = mapped_column(ForeignKey("property_group.id"), primary_key=True)
#     property_group = Mapped[PropertyGroup] = relationship(back_populates="property_values")
#     subjects = Mapped[List["Subject"]] = relationship(secondary=Subject_PropertyValue,
#                                                       back_populates="property_values")


if __name__ == '__main__':
    with app.app_context():
        db.create_all()