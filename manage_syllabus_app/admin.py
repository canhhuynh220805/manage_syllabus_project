import hashlib
import math
import os
from types import SimpleNamespace

from flask import redirect, request, url_for, flash, json
from flask_admin import BaseView, expose, AdminIndexView, Admin
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.fields import QuerySelectField
from flask_login import logout_user, current_user
from sqlalchemy import desc
from werkzeug.security import generate_password_hash
from wtforms import PasswordField

from manage_syllabus_app import app, db, dao, services
from manage_syllabus_app.models import UserRole, User, Faculty, Lecturer, Subject, Credit, TrainingProgram, Major, \
    Syllabus, TemplateSyllabus


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

    def on_model_change(self, form, model, is_created):
        if hasattr(form, 'password') and form.password.data:
            raw_password = form.password.data
            model.password = generate_password_hash(raw_password)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('admin.index', next=request.url))


# --- CÁC VIEW TÙY CHỈNH CHO TỪNG MODEL ---

# Lớp view tùy chỉnh cho quản lý Người dùng
class UserAdminView(AuthenticatedAdminView):
    # Cấu hình để trường password luôn là dạng ẩn (dấu chấm)
    form_overrides = {
        'password': PasswordField
    }
    column_list = ['name', 'username', 'user_role', 'lecturer']
    column_searchable_list = ['name', 'username']
    column_filters = ['user_role', 'active']
    column_exclude_list = ['avatar', 'joined_date', 'password']  # Ẩn cột password đã hash khỏi danh sách

    # Quy tắc hiển thị form khi TẠO MỚI
    form_create_rules = ('name', 'username', 'password','user_role')
    # Quy tắc hiển thị form khi CHỈNH SỬA
    form_edit_rules = ('name', 'username' ,'user_role', 'active', 'lecturer')



# Lớp view tùy chỉnh cho Giảng viên
class LecturerAdminView(AuthenticatedAdminView):
    column_list = ['name', 'email', 'room', 'faculty']
    form_columns = ['name', 'email', 'room', 'faculty']
    column_searchable_list = ['name', 'email']
    column_filters = ['faculty']
    column_auto_select_related = True  # Tự động load và hiển thị tên Khoa

# Ló view tùy chỉnh đề cương
class SyllabusAdminView(AuthenticatedAdminView):
    list_template = 'admin/custom_syllabus_list.html'


    form_columns = ['name', 'subject', 'faculty','lecturer', 'structure_file', 'training_programs']
    form_args = {
        'name': {'label': 'Tên đề cương'},
        'subject': {'label': 'Môn học'},
        'faculty': {'label': 'Khoa'},
        'lecturer': {'label': 'Giảng viên'},
        'structure_file': {'label': 'Đề cương mẫu'},
        'training_programs': {'label': 'Chương trình đào tạo'}
    }

    @expose('/')
    def index(self):
        page_size = app.config["PAGE_SIZE"]
        total = dao.count_syllabuses()
        page = request.args.get('page', 1, type=int)
        # Lấy tham số tìm kiếm từ URL
        key = request.args.get('key', '')
        selected_year = request.args.get('year')
        selected_program = request.args.get('programs_name')
        selected_template = request.args.get('template')

        syllabuses = dao.get_all_syllabuses(page=page, page_size=page_size, key=key, year=selected_year, program=selected_program, template=selected_template)
        # Lấy dữ liệu cho các ô lọc (Dropdown)
        years = db.session.query(TrainingProgram.academic_year).distinct().all()
        years = [y[0] for y in years]
        programs = TrainingProgram.query.all()
        # Mockup danh sách template file (thực tế bạn có thể quét thư mục)
        templates = ['syllabus_2025.json']

        return self.render(
            self.list_template,
            syllabuses=syllabuses,
            years=years,
            programs=programs,
            templates=templates,
            pages=math.ceil(total / page_size)
        )

    def after_model_change(self, form, model, is_created):
        if is_created:
            try:
                services.init_structure_syllabus(model)
                flash(f'Đã khởi tạo cấu trúc cho đề cương "{model.name}" thành công!', 'success')
            except Exception as e:
                flash(f'Lỗi khi tạo cấu trúc: {str(e)}', 'warning')


# Lớp view tùy chỉnh cho Môn học
class SubjectAdminView(AuthenticatedAdminView):
    column_list = ['id', 'name', 'credit']
    form_columns = ['id', 'name', 'credit']
    column_searchable_list = ['id', 'name']
    column_filters = ['credit']
    column_auto_select_related = True  # Tự động load và hiển thị thông tin Tín chỉ

# Lớp view tùy chỉnh chương trình đào tạo
class TrainingProgramAdminView(AuthenticatedAdminView):
    column_list = ['id', 'name', 'academic_year', 'major']
    form_columns = ['name', 'academic_year', 'major', 'clone_from']

    form_extra_fields = {
        'clone_from': QuerySelectField(
            label='Kế thừa từ chương trình (Optional)',
            query_factory=lambda: TrainingProgram.query.all(),
            allow_blank=True,
            blank_text='-- Không kế thừa --',
            get_label='name',
            description='Chọn chương trình cũ để copy toàn bộ đề cương sang chương trình này.'
        )
    }

    def on_model_change(self, form, model, is_created):
        if is_created and form.clone_from.data:
            source_program = form.clone_from.data
            for syllabus in source_program.syllabuses:
                model.syllabuses.append(syllabus)
        return super().on_model_change(form, model, is_created)


# Lớp view tùy chỉnh chuyên ngành
class MajorAdminView(AuthenticatedAdminView):
    column_list = ['id', 'name', 'code', 'faculty']
    form_columns = ['name', 'code', 'faculty','training_programs']

class TemplateSyllabusView(AuthenticatedAdminView):
    column_list = ['id', 'name']
    form_columns = ['name', 'structure']

class LogoutView(AuthenticatedBaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect(url_for('admin.index'))


# --- KHỞI TẠO TRANG ADMIN VÀ THÊM CÁC VIEW ---


admin = Admin(app=app, name='QUẢN TRỊ ĐỀ CƯƠNG', index_view=MyAdminIndex())

admin.add_view(UserAdminView(User, db.session, name='Người dùng'))
admin.add_view(SyllabusAdminView(Syllabus, db.session, name="Đề cương"))
admin.add_view(LecturerAdminView(Lecturer, db.session, name='Giảng viên'))
admin.add_view(SubjectAdminView(Subject, db.session, name='Môn học'))
admin.add_view(TrainingProgramAdminView(TrainingProgram, db.session, name="Chương trình đào tạo"))
admin.add_view(MajorAdminView(Major, db.session, name="Chuyên ngành học"))
admin.add_view(TemplateSyllabusView(TemplateSyllabus, db.session, name="Đề cương mẫu"))
admin.add_view(LogoutView(name='Đăng xuất'))