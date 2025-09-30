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


def handle_ajax_request(f):
    """
    Decorator tự động xử lý commit, rollback, flash message,
    và trả về JSON cho request AJAX hoặc redirect cho request thường.
    """

    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Lấy syllabus_id từ form để dùng cho việc chuyển hướng cuối cùng
        syllabus_id_for_redirect = request.form.get('syllabus_id')
        try:
            # Gọi hàm controller gốc (ví dụ: delete_course_objective)
            result = f(*args, **kwargs)

            # Nếu hàm controller trả về một giá trị (ví dụ: một redirect khi không tìm thấy),
            # thì decorator sẽ thực thi và trả về giá trị đó ngay lập tức.
            if result is not None:
                return result

            # Nếu hàm controller chạy xong mà không có lỗi, commit thay đổi
            db.session.commit()
            flash('Thao tác thành công!', 'success')

            # Kiểm tra xem có phải là AJAX request không để trả về JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': 'Thao tác thành công!'})

        except Exception as e:
            # Nếu có bất kỳ lỗi nào xảy ra trong quá trình thực thi, rollback lại
            db.session.rollback()
            error_message = f'Thao tác thất bại! Lỗi: {str(e)}'
            flash(error_message, 'danger')

            # Trả về lỗi dạng JSON nếu là AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': False, 'message': str(e)}), 500

        # Nếu là request thường, chuyển hướng về trang chi tiết đề cương
        return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id_for_redirect))

    return decorated_function