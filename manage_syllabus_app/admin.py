import os
from types import SimpleNamespace

from flask import redirect, request, url_for, flash, json
from flask_admin import BaseView, expose, AdminIndexView, Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import logout_user, current_user
from werkzeug.security import generate_password_hash
from wtforms import PasswordField

from manage_syllabus_app import app, db, dao
from manage_syllabus_app.models import UserRole, User, Faculty, Lecturer, Subject, Credit



# Lớp Index View tùy chỉnh để xử lý đăng nhập
class MyAdminIndex(AdminIndexView):
    @expose('/')
    def index(self):
        if current_user.is_authenticated and current_user.user_role != UserRole.ADMIN:
            flash('Bạn không có quyền truy cập trang quản trị.', 'danger')
            return redirect(url_for('index'))
        all_syllabuses = dao.get_all_syllabuses()
        return self.render('admin/index.html', syllabuses=all_syllabuses)

    def is_accessible(self):
        return True

# --- CÁC VIEW CHO CHỨC NĂNG PHỤ ---

class AuthenticatedBaseView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin.index', next=request.url))

# Lớp view bảo vệ chung
class AuthenticatedAdminView(ModelView):

    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin.index', next=request.url))


# --- CÁC VIEW TÙY CHỈNH CHO TỪNG MODEL (PHIÊN BẢN HOÀN CHỈNH) ---

# Lớp view tùy chỉnh cho quản lý Người dùng
class UserAdminView(AuthenticatedAdminView):
    # Cấu hình để trường password luôn là dạng ẩn (dấu chấm)
    form_overrides = {
        'password': PasswordField
    }
    column_list = ['name', 'username', 'user_role', 'active', 'lecturer_id']
    column_searchable_list = ['name', 'username']
    column_filters = ['user_role', 'active']
    column_exclude_list = ['avatar', 'joined_date', 'password']  # Ẩn cột password đã hash khỏi danh sách

    # Quy tắc hiển thị form khi TẠO MỚI
    form_create_rules = ('name', 'username', 'password', 'user_role', 'active')
    # Quy tắc hiển thị form khi CHỈNH SỬA
    form_edit_rules = ('name', 'username', 'password', 'user_role', 'active')

    def on_model_change(self, form, model, is_created):
        # Chỉ mã hóa lại mật khẩu nếu người dùng nhập mật khẩu mới vào form
        if form.password.data:
            model.password = generate_password_hash(form.password.data)


# Lớp view tùy chỉnh cho Khoa
class FacultyAdminView(AuthenticatedAdminView):
    column_list = ['name', 'lecturers']  # Hiển thị tên khoa và danh sách giảng viên thuộc khoa
    form_columns = ['name']
    column_searchable_list = ['name']


# Lớp view tùy chỉnh cho Giảng viên
class LecturerAdminView(AuthenticatedAdminView):
    column_list = ['name', 'email', 'room', 'faculty']
    form_columns = ['name', 'email', 'room', 'faculty']
    column_searchable_list = ['name', 'email']
    column_filters = ['faculty']
    column_auto_select_related = True  # Tự động load và hiển thị tên Khoa


# Lớp view tùy chỉnh cho Tín chỉ
class CreditAdminView(AuthenticatedAdminView):
    column_list = ['numberTheory', 'numberPractice', 'hourSelfStudy']
    form_columns = ['numberTheory', 'numberPractice', 'hourSelfStudy']


# Lớp view tùy chỉnh cho Môn học
class SubjectAdminView(AuthenticatedAdminView):
    column_list = ['id', 'name', 'credit']
    form_columns = ['id', 'name', 'credit']
    column_searchable_list = ['id', 'name']
    column_filters = ['credit']
    column_auto_select_related = True  # Tự động load và hiển thị thông tin Tín chỉ


class SampleSyllabusView(AuthenticatedBaseView):
    @expose('/')
    def index(self):
        # 1. Đọc cấu trúc từ tệp JSON mặc định
        default_structure_file = 'syllabus_2025.json'  # Tên tệp JSON mẫu
        structures_dir = os.path.join(app.root_path, 'data', 'structures')
        json_path = os.path.join(structures_dir, default_structure_file)

        master_structure_data = []
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                master_structure_data = json.load(f)
        except Exception as e:
            flash(f"LỖI NGHIÊM TRỌNG: Không thể tải tệp cấu trúc mẫu '{default_structure_file}'. Lỗi: {e}", "danger")
            # Trả về một trang lỗi đơn giản
            return self.render('admin/sample_syllabus_view.html', syllabus=None, is_sample=True)

        # 2. Tự động xây dựng "Syllabus giả" từ dữ liệu JSON
        mock_main_sections = []
        # Thay thế MASTER_STRUCTURE bằng master_structure_data
        for part_def in master_structure_data:
            mock_sub_sections = []
            for i, sub_def in enumerate(part_def['sub_sections']):
                # Tạo một bản sao để tránh thay đổi dữ liệu gốc (nếu sub_def là dict)
                mock_sub_def = sub_def.copy()
                mock_sub_def['id'] = (part_def['position'] * 100) + i

                if mock_sub_def.get('type') == 'selection':
                    # Dữ liệu giả cho nhóm lựa chọn
                    mock_sub_def['attribute_group'] = SimpleNamespace(
                        attribute_values=[
                            SimpleNamespace(id=1, name_value='[Lựa chọn mẫu 1]'),
                            SimpleNamespace(id=2, name_value='[Lựa chọn mẫu 2]')
                        ]
                    )
                mock_sub_sections.append(SimpleNamespace(**mock_sub_def))

            mock_part = SimpleNamespace(
                id=part_def['position'],
                name=part_def['name'],
                code=part_def['code'],
                position=part_def['position'],
                sub_sections=mock_sub_sections
            )
            mock_main_sections.append(mock_part)

        # 3. (Giữ nguyên) Xây dựng các đối tượng dữ liệu giả phức tạp
        mock_plos = [
            SimpleNamespace(id='PLO.1'),
            SimpleNamespace(id='PLO.2'),
            SimpleNamespace(id='PLO.3')
        ]

        mock_subject = SimpleNamespace(
            id='SAMPLE',
            name='[Tên môn học]',
            credit=SimpleNamespace(id=0, getTotalCredit=lambda: 0, numberTheory=0, numberPractice=0, hourSelfStudy=0),

            required_by_relation=[
                SimpleNamespace(id=1, require_subject=SimpleNamespace(id='PRE101', name='[Tên môn tiên quyết 1]'),
                                type_requirement=SimpleNamespace(name='Tiên quyết')),
                SimpleNamespace(id=2, require_subject=SimpleNamespace(id='PRE102', name='[Tên môn học trước]'),
                                type_requirement=SimpleNamespace(name='Học trước')),
            ],

            course_objectives=[
                SimpleNamespace(
                    id=1, name='CO1', content='[Mô tả mục tiêu môn học 1]',
                    programme_learning_outcomes=mock_plos,
                    course_learning_outcomes=[
                        SimpleNamespace(id=101, content='[Mô tả chuẩn đầu ra 1.1]',
                                        plo_association=[
                                            SimpleNamespace(plo_id='PLO.1', rating=4),
                                            SimpleNamespace(plo_id='PLO.2', rating=3),
                                            SimpleNamespace(plo_id='PLO.3', rating=3),
                                        ]),
                        SimpleNamespace(id=102, content='[Mô tả chuẩn đầu ra 1.2]',
                                        plo_association=[
                                            SimpleNamespace(plo_id='PLO.1', rating=4),
                                            SimpleNamespace(plo_id='PLO.2', rating=3),
                                            SimpleNamespace(plo_id='PLO.3', rating=3),
                                        ]),
                    ]
                ),
                SimpleNamespace(
                    id=2, name='CO2', content='[Mô tả mục tiêu môn học 2]',
                    programme_learning_outcomes=[mock_plos[2]],
                    course_learning_outcomes=[
                        SimpleNamespace(id=201, content='[Mô tả chuẩn đầu ra 2.1]',
                                        plo_association=[
                                            SimpleNamespace(plo_id='PLO.3', rating=2),
                                        ]),
                    ]
                )
            ]
        )

        mock_syllabus = SimpleNamespace(
            id=0,
            main_sections=mock_main_sections,
            subject=mock_subject,
            lecturer=SimpleNamespace(id=0, name='[Tên giảng viên]', email='[Email]', room='[Phòng]'),
            faculty=SimpleNamespace(id=0, name='[Tên Khoa]'),
            subject_id=0, lecturer_id=0, faculty_id=0,

            learning_materials=[
                SimpleNamespace(id=1, name='[Tên sách giáo trình chính]',
                                type_material=SimpleNamespace(name='Sách giáo trình')),
                SimpleNamespace(id=2, name='[Tên tài liệu tham khảo 1]',
                                type_material=SimpleNamespace(name='Tài liệu tham khảo')),
            ]
        )

        # 4. Render template
        return self.render('admin/sample_syllabus_view.html',
                           syllabus=mock_syllabus,
                           is_sample=True,
                           all_faculties=[], all_lecturers=[], learning_materials=[], all_subjects=[],
                           all_type_subjects=[],
                           plos=[])  # `plos` ở đây là để render form, mock_plos ở trên là cho dữ liệu


class LogoutView(AuthenticatedBaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect(url_for('admin.index'))


# --- KHỞI TẠO TRANG ADMIN VÀ THÊM CÁC VIEW ---


admin = Admin(app=app, name='QUẢN TRỊ ĐỀ CƯƠNG', template_mode='bootstrap4', index_view=MyAdminIndex())

admin.add_view(UserAdminView(User, db.session, name='Người dùng'), )
admin.add_view(FacultyAdminView(Faculty, db.session, name='Khoa'))
admin.add_view(LecturerAdminView(Lecturer, db.session, name='Giảng viên'))
admin.add_view(CreditAdminView(Credit, db.session, name='Tín chỉ'))  # Thêm view quản lý Tín chỉ
admin.add_view(SubjectAdminView(Subject, db.session, name='Môn học'))
admin.add_view(SampleSyllabusView(name='Đề cương mẫu', endpoint='sample-syllabus'))
admin.add_view(LogoutView(name='Đăng xuất'))