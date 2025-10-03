from flask import redirect, request, url_for
from flask_admin import BaseView, expose, AdminIndexView, Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import logout_user, current_user

from manage_syllabus_app import app, db
from manage_syllabus_app.models import UserRole, User, Faculty, Lecturer, Subject


# Lớp Index View tùy chỉnh để xử lý đăng nhập
class MyAdminIndex(AdminIndexView):
    @expose('/')
    def index(self):
        # Nếu chưa đăng nhập hoặc không phải admin, chuyển về trang đăng nhập chính
        if not current_user.is_authenticated or current_user.user_role != UserRole.ADMIN:
            return redirect(url_for('user_login', next=request.url))

        return super(MyAdminIndex, self).index()


# Lớp view bảo vệ cho các trang quản lý Model, yêu cầu phải là ADMIN
class AuthenticatedAdminView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        # Chuyển hướng về trang đăng nhập nếu không có quyền
        return redirect(url_for('admin_login', next=request.url))


# Lớp view bảo vệ cho các trang tùy chỉnh (như Logout)
class AuthenticatedBaseView(BaseView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.user_role == UserRole.ADMIN

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('user_login', next=request.url))


# Trang Đăng xuất khỏi Admin
class LogoutView(AuthenticatedBaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect(url_for('admin.index'))


# Khởi tạo trang admin với MyAdminIndex tùy chỉnh
admin = Admin(app=app, name='QUẢN TRỊ ĐỀ CƯƠNG', template_mode='bootstrap4', index_view=MyAdminIndex())

# Thêm các view quản lý model vào trang admin
admin.add_view(AuthenticatedAdminView(User, db.session, name='Người dùng'))
admin.add_view(AuthenticatedAdminView(Faculty, db.session, name='Khoa'))
admin.add_view(AuthenticatedAdminView(Lecturer, db.session, name='Giảng viên'))
admin.add_view(AuthenticatedAdminView(Subject, db.session, name='Môn học'))
admin.add_view(LogoutView(name='Đăng xuất'))