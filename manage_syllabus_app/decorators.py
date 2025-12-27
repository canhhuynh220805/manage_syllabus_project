from functools import wraps
from flask_login import current_user
from flask import abort, request, flash, jsonify, url_for, redirect

from . import db
from .models import UserRole
import functools
# =============PHÂN QUYỀN ADMIN================
def admin_required(f):
    """
    Decorator để giới hạn quyền truy cập chỉ cho người dùng có vai trò là ADMIN.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Nếu người dùng chưa đăng nhập hoặc vai trò không phải ADMIN
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
            abort(403)  # Trả về lỗi Forbidden (Cấm truy cập)
        return f(*args, **kwargs)
    return decorated_function
