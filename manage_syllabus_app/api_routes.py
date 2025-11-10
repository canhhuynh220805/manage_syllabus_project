from flask import request

from flask import Blueprint, jsonify, abort
from flask_login import login_required

from manage_syllabus_app import dao, db
from manage_syllabus_app.models import TextSubSection

api = Blueprint('api', __name__, url_prefix='/api')


@api.errorhandler(404)
def resource_not_found(e):
    """Xử lý lỗi 404 (Không tìm thấy) cho API."""
    return jsonify(success=False, message=e.description or "Không tìm thấy tài nguyên."), 404

@api.errorhandler(403)
def forbidden(e):
    """Xử lý lỗi 403 (Cấm truy cập) cho API."""
    return jsonify(success=False, message=e.description or "Bạn không có quyền thực hiện hành động này."), 403

@api.errorhandler(400)
def bad_request(e):
    """Xử lý lỗi 400 (Yêu cầu sai) cho API."""
    return jsonify(success=False, message=e.description or "Yêu cầu không hợp lệ."), 400


@api.route('/lecturers/<int:lecturer_id>', methods=['GET'])
@login_required
def get_lecturer(lecturer_id):
    """
    Đây là API RESTful mới, thay thế cho /get_lecturer_detail/<id>
    Method: GET
    Url: /api/v1/lecturers/123
    """
    lecturer = dao.get_lecturers(lecturer_id)

    # Nếu không tìm thấy, dùng abort(404) để trả về lỗi JSON 404
    if not lecturer:
        abort(404, description="Không tìm thấy giảng viên với ID này.")

    # Trả về dữ liệu JSON chuẩn (giống file PDF)
    return jsonify({
        'id': lecturer.id,
        'name': lecturer.name,
        'email': lecturer.email or '',
        'room': lecturer.room or ''
    })

@api.route('/subjects/<string:subject_id>', methods=['PATCH'])
# @login_required
def update_subject(subject_id):
    subject = dao.get_subject_by_id(subject_id)
    if not subject:
        abort(404, description="Không tìm thấy môn học.")

    data = request.get_json()
    if not data:
        abort(400, description="Không có dữ liệu đầu vào (Yêu cầu phải là JSON).")

    # Cập nhật các trường được phép
    if 'name' in data:
        subject.name = data['name']


    try:
        db.session.commit()
        # Trả về tài nguyên đã được cập nhật (dùng hàm .to_dict() mới)
        return jsonify(subject.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"Lỗi khi cập nhật CSDL: {str(e)}"), 500


@api.route('/text-subsections/<int:subsection_id>', methods=['PATCH'])
def update_text_subsection(subsection_id):
    subsection = db.session.get(TextSubSection, subsection_id)
    if not subsection:
        abort(404, description="Không tìm thấy tiểu mục văn bản này.")
    data = request.get_json()
    if not data or 'content' not in data:
        abort(400, description="Yêu cầu phải là JSON và chứa trường 'content'.")
    subsection.content = data.get('content')
    try:
        db.session.commit()
        return jsonify(subsection.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"Lỗi khi cập nhật CSDL: {str(e)}"), 500