import math
import os

from manage_syllabus_app import app, dao, login
import functools
from flask import render_template, request, url_for, flash, jsonify, abort, Blueprint
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import redirect
from manage_syllabus_app import db

from manage_syllabus_app.models import Faculty, Lecturer, Credit, Subject, Syllabus, RequirementSubject, \
    TypeRequirement, MainSection, LearningMaterial, TypeLearningMaterial, TextSubSection, \
    CourseLearningOutcome, CourseObjective, SelectionSubSection, AttributeValue, ProgrammeLearningOutcome, \
    CloPloAssociation, User, UserRole
from manage_syllabus_app.services import build_mock_syllabus_from_json

api = Blueprint('api', __name__, url_prefix='/api')


def to_roman(n):
    """Chuyển một số nguyên sang số La Mã."""
    if not isinstance(n, int) or not 1 <= n < 4000:
        return n  # Trả về giá trị gốc nếu không phải là số hợp lệ
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1
    ]
    syb = [
        "M", "CM", "D", "CD",
        "C", "XC", "L", "XL",
        "X", "IX", "V", "IV",
        "I"
    ]
    roman_num = ''
    i = 0
    while n > 0:
        for _ in range(n // val[i]):
            roman_num += syb[i]
            n -= val[i]
        i += 1
    return roman_num



# CÁC ROUTE GỐC
@app.route('/')
def index():
    page_size = app.config["PAGE_SIZE"]
    total = dao.count_syllabuses()
    page = request.args.get('page', 1, type=int)
    syllabus = []
    if current_user.is_authenticated:
        if current_user.user_role == UserRole.ADMIN:
            # Đếm tất cả
            total = dao.count_syllabuses()
            # Lấy dữ liệu trang hiện tại
            syllabus = dao.get_all_syllabuses(page=page, page_size=page_size)

        elif current_user.user_role == UserRole.USER and current_user.lecturer_id:
            # Đếm theo giảng viên
            total = dao.count_syllabuses(lecturer_id=current_user.lecturer_id)
            # Lấy dữ liệu trang hiện tại
            syllabus = dao.get_syllabuses_by_lecturer_id(lecturer_id=current_user.lecturer_id,
                                                         page=page, page_size=page_size)
    all_faculties = dao.get_all_faculties()
    return render_template('index.html', syllabuses=syllabus, all_faculties=all_faculties,
                           pages=math.ceil(total / page_size))


@app.route('/editor')
@login_required
def editor():
    return render_template('editor.html')


@app.route('/specialist')
@login_required
def specialist_view():
    if current_user.user_role != UserRole.SPECIALIST:
        abort(403)
    template_files = []

    return render_template('specialist/index.html', template_files=template_files)

@app.route('/specialist/template/<filename>')
@login_required
def specialist_template_detail(filename):
    # 1. Kiểm tra quyền
    if current_user.user_role != UserRole.SPECIALIST:
        abort(403)


    # 3. Gọi hàm xử lý logic
    try:
        mock_syllabus = []
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for('specialist_view'))

    return render_template(
        'specialist/sample_syllabus_view.html',
        syllabus=mock_syllabus,
        is_sample=True,
        all_faculties=[], all_lecturers=[], learning_materials=[],
        all_subjects=[], all_type_subjects=[], plos=[]
    )

@app.route('/syllabus/<int:syllabus_id>/')
@login_required
def syllabus_detail(syllabus_id):
    syllabus = dao.get_syllabus_by_id(syllabus_id)
    all_faculties = dao.get_all_faculties()
    all_lecturers = dao.get_lecturers()
    all_type_subjects = dao.get_all_type_subjects()
    learning_materials = dao.get_all_learning_material_types()
    available_subjects = dao.get_available_require_subjects(syllabus.subject.id)
    plos = dao.get_all_plos()
    sorted_plos = dao.get_sorted_plos_for_syllabus(syllabus_id)
    return render_template('syllabus_detail.html', syllabus=syllabus,
                           all_faculties=all_faculties, all_lecturers=all_lecturers,
                           learning_materials=learning_materials,
                           all_type_subjects=all_type_subjects, all_subjects=available_subjects, plos=plos,
                           unique_plos=sorted_plos)


@app.context_processor
def util():
    def set_param(**kwargs):
        args = request.args.to_dict()
        args.update(kwargs)
        return url_for('.index', **args)

    return dict(set_param=set_param)


@api.route('/faculties/<int:faculty_id>/lecturers', methods=['GET'])
def get_lecturers_by_faculty(faculty_id):
    lecturers = Lecturer.query.filter_by(faculty_id=faculty_id).all()
    # Trả về list object đơn giản
    return jsonify([{'id': l.id, 'name': l.name} for l in lecturers])


# CÁC ROUTE XÁC THỰC
@app.route('/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = dao.get_user_by_username(username)

        if user and dao.check_password(user, password):
            login_user(user=user)
        else:
            flash('Tên đăng nhập hoặc mật khẩu không chính xác!', 'danger')

        if user.user_role == UserRole.SPECIALIST:
            return redirect('/specialist')
        return redirect('/')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def user_register():
    err_msg = ""
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        if password != confirm:
            err_msg = "Mật khẩu xác nhận không khớp!"
        else:
            try:
                dao.add_user(name=name, username=username, password=password)
                return redirect(url_for('user_login'))
            except Exception as e:
                err_msg = "Đã có lỗi xảy ra: " + str(e)

    return render_template('register.html', err_msg=err_msg)


@app.route('/logout')
def user_logout():
    logout_user()
    return redirect(url_for('user_login'))


@app.route('/admin-login', methods=['POST'])
def admin_login():
    username = request.form['username']
    password = request.form['password']
    user = dao.get_user_by_username(username)
    if user and dao.check_password(user, password):
        login_user(user=user)
    else:
        flash('Tên đăng nhập hoặc mật khẩu không chính xác!', 'danger')
    return redirect('/admin')


@api.route('/syllabuses/<int:syllabus_id>/director', methods=['PATCH'])
@login_required
def update_syllabus_director(syllabus_id):
    syllabus = db.session.get(Syllabus, syllabus_id)
    if not syllabus:
        flash('Không tìm thấy đề cương', 'danger')
        return redirect(url_for('index'))

    data = request.get_json()
    if not data:
        abort(400, description="Không có dữ liệu đầu vào (Yêu cầu phải là JSON).")

    try:
        # 1. Cập nhật Syllabus
        if 'faculty_id' in data:
            syllabus.faculty_id = int(data['faculty_id'])
        if 'lecturer_id' in data:
            syllabus.lecturer_id = int(data['lecturer_id'])

        # 2. Cập nhật Lecturer (nếu có thông tin)
        lecturer_to_update = db.session.get(Lecturer, syllabus.lecturer_id)
        if lecturer_to_update:
            if 'lecturer_email' in data:
                lecturer_to_update.email = data['lecturer_email']
            if 'lecturer_room' in data:
                lecturer_to_update.room = data['lecturer_room']

        db.session.commit()

        # Trả về thông tin giảng viên đã được cập nhật
        return jsonify(lecturer_to_update.to_dict())

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


@api.route('/subjects/<string:subject_id>', methods=['PATCH'])
@login_required
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


@api.route('/credits/<int:credit_id>', methods=['PATCH'])
def update_credit(credit_id):
    credit = dao.get_credit_by_id(credit_id)

    if not credit:
        abort(404, description="Không tìm thấy tín chỉ")

    data = request.get_json()

    if 'numberTheory' in data:
        credit.numberTheory = data.get('numberTheory')
    if 'numberPractice' in data:
        credit.numberPractice = data.get('numberPractice')
    if 'hourSelfStudy' in data:
        credit.hourSelfStudy = data.get('hourSelfStudy')

    try:
        db.session.commit()
        # Trả về tài nguyên đã được cập nhật
        return jsonify(credit.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"Lỗi khi cập nhật CSDL: {str(e)}"), 500


@api.route('/selection-subsections/<int:subsection_id>', methods=['PATCH'])
@login_required
def update_selection_subsection(subsection_id):
    subsection = db.session.get(SelectionSubSection, subsection_id)
    if not subsection:
        abort(404, description="Không tìm thấy tiểu mục lựa chọn này.")

    data = request.get_json()
    if not data or 'selected_ids' not in data:
        abort(400, description="Yêu cầu phải là JSON và chứa 'selected_ids' (có thể là mảng rỗng).")
    print(data)
    try:
        selected_ids = data.get('selected_ids')
        print(selected_ids)
        if selected_ids is None:
            selected_ids = []
        elif not isinstance(selected_ids, list):
            selected_ids = [selected_ids]
        subsection.selected_values.clear()
        if selected_ids:
            int_ids = [int(id) for id in selected_ids]
            print(int_ids)
            new_selection = AttributeValue.query.filter(AttributeValue.id.in_(int_ids)).all()
            print(new_selection)
            subsection.selected_values.extend(new_selection)

        db.session.commit()
        return jsonify(subsection.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"Lỗi khi cập nhật CSDL: {str(e)}"), 500


@api.route('/learning-materials/<int:material_id>', methods=['PATCH'])
@login_required
def update_learning_material(material_id):
    material = db.session.get(LearningMaterial, material_id)
    if not material:
        abort(404, description="Không tìm thấy tài liệu")
    data = request.get_json()
    if not data:
        abort(400, description="Yêu cầu phải là JSON")
    if 'name' in data:
        material.name = data.get('name')
    try:
        db.session.commit()
        return jsonify(material.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"Lỗi server: {str(e)}"), 500


@api.route('/learning-materials/<int:material_id>/type', methods=['PATCH'])
@login_required
def update_learning_material_type(material_id):
    material = db.session.get(LearningMaterial, material_id)
    if not material:
        abort(404, description="Không tìm thấy tài liệu")

    data = request.get_json()
    if not data or 'type_material_id' not in data:
        abort(400, description="Yêu cầu phải là JSON và chứa 'type_material_id'.")

    try:
        new_type_id = data.get('type_material_id')
        material.type_material_id = new_type_id
        db.session.commit()
        return jsonify(material.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"Lỗi server: {str(e)}"), 500


@api.route('/clos/<int:clo_id>/plos/<int:plo_id>/rating', methods=['PUT'])
# @login_required
def update_rating_api(clo_id, plo_id):
    data = request.get_json()
    if not data or 'rating' not in data:
        abort(400, description="Thiếu thông tin rating.")

    try:
        new_rating = int(data['rating'])

        # Tìm rating cũ (lưu ý: plo_id trong DB có thể là int hoặc str tùy cấu hình trước đó)
        # Nếu DB đã chuẩn hóa int thì dùng plo_id, nếu chưa thì dùng str(plo_id)
        assoc = CloPloAssociation.query.filter_by(clo_id=clo_id, plo_id=plo_id).first()

        if not assoc:
            # Thử tìm lại với dạng string nếu int không thấy (phòng hờ)
            assoc = CloPloAssociation.query.filter_by(clo_id=clo_id, plo_id=str(plo_id)).first()

        if assoc:
            assoc.rating = new_rating
            db.session.commit()
            return jsonify({"success": True, "rating": new_rating})
        else:
            abort(404, description="Không tìm thấy liên kết rating này.")

    except ValueError:
        abort(400, description="Rating phải là số nguyên.")
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=str(e)), 500


@api.route('/requirement-subjects/<req_id>', methods=['PATCH'])
@login_required
def update_requirement_subject(req_id):
    req_subject = db.session.get(RequirementSubject, req_id)
    if not req_subject:
        abort(404, description="Không tìm thấy môn học điều kiện.")

    data = request.get_json()
    if not data:
        abort(400, description="Yêu cầu phải là JSON.")

    try:
        if 'requirement_subject_id' in data:
            req_subject.require_subject_id = data['requirement_subject_id']

        if 'type_subject_id' in data:
            req_subject.type_requirement_id = int(data['type_subject_id'])

        db.session.commit()
        return jsonify(req_subject.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"Lỗi server: {str(e)}"), 500


@api.route('/subjects/<subject_id>/requirements', methods=['POST'])
@login_required
def add_requirement_subject(subject_id):
    data = request.get_json()
    print(data)
    if not data:
        abort(404, description="Yêu cầu phải là JSON.")

    require_subject_id = data.get('requirement_subject_id')
    type_requirement_id = data.get('type_subject_id')

    if str(require_subject_id) == str(subject_id):
        return jsonify({"success": False, "message": "Không thể chọn chính môn"}), 400

    print(require_subject_id)
    print(type_requirement_id)
    if not all([require_subject_id, type_requirement_id]):
        abort(400, description="Thiếu thông tin môn học hoặc loại điều kiện.")

    from dao import get_available_require_subjects
    available = get_available_require_subjects(subject_id)
    available_ids = {s.id for s in available}
    if require_subject_id not in available_ids:
        return jsonify({"success": False, "message": "Môn đã được chọn hoặc không hợp lệ"}), 400

    try:
        new_req = RequirementSubject(
            subject_id=subject_id,
            require_subject_id=require_subject_id,
            type_requirement_id=type_requirement_id,
        )
        db.session.add(new_req)
        db.session.commit()
        return jsonify(new_req.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"Lỗi server: {str(e)}"), 500


@api.route('/requirement-subjects/<req_id>', methods=['DELETE'])
@login_required
def delete_requirement_subject(req_id):
    requirement_subject = db.session.get(RequirementSubject, req_id)
    if not requirement_subject:
        abort(404, description="Không tìm thấy để xóa.")
    try:
        db.session.delete(requirement_subject)
        db.session.commit()
        return jsonify({"success": True, "message": "Đã xóa thành công"})
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"Lỗi server: {str(e)}"), 500


@api.route('/subjects/<subject_id>/course-objectives', methods=['POST'])
@login_required
def add_course_objective(subject_id):
    subject = dao.get_subject_by_id(subject_id)
    if not subject:
        abort(404, description="Không tìm thấy môn học.")

    data = request.get_json()
    if not data:
        abort(400, description="Yêu cầu phải là JSON.")
    description = data.get('co_description')
    # Xử lý plo_ids giống như selected_ids (chấp nhận cả string đơn và list)
    raw_plo_ids = data.get('plo_ids')

    plo_ids = []
    if raw_plo_ids:
        if isinstance(raw_plo_ids, list):
            plo_ids = raw_plo_ids
        else:
            plo_ids = [raw_plo_ids]

    if not description or not plo_ids:
        abort(400, description="Thiếu mô tả hoặc PLO.")
    plos = dao.get_all_plos(plo_ids)
    print(plos)
    try:
        current_count = len(subject.course_objectives)
        co_name = f"CO{current_count + 1}"
        new_co = CourseObjective(
            name=co_name,
            content=description,
            subject_id=subject_id,
            programme_learning_outcomes=plos
        )
        db.session.add(new_co)
        db.session.commit()
        return jsonify(new_co.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"Lỗi server: {str(e)}"), 500


@api.route('/course-objectives/<int:co_id>', methods=['DELETE'])
@login_required
def delete_course_objective(co_id):
    course_objective = db.session.get(CourseObjective, co_id)
    if not course_objective:
        abort(404, description="Không tìm thấy CO để xóa.")
    try:
        db.session.delete(course_objective)
        db.session.commit()
        return jsonify({"success": True, "message": "Đã xóa CO thành công"})
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"Lỗi server: {str(e)}"), 500


@api.route('/course-objectives/<int:co_id>', methods=['PATCH'])
@login_required
def update_course_objective(co_id):
    course_objective = db.session.get(CourseObjective, co_id)
    if not course_objective:
        abort(404, description="Không tìm thấy CO để xóa.")

    data = request.get_json()
    if not data or 'content' not in data:
        abort(400, description="Thiếu trường 'content'.")

    course_objective.content = data.get('content')
    try:
        db.session.commit()
        return jsonify(course_objective.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"Lỗi server: {str(e)}"), 500


@api.route('/course-objectives/<int:co_id>/plos', methods=['PUT'])
@login_required
def update_course_objective_plos(co_id):
    co = db.session.get(CourseObjective, co_id)
    if not co:
        abort(404, description="Không tìm thấy CO.")

    data = request.get_json()

    # --- 1. Xử lý input: ÉP KIỂU VỀ INT ---
    raw_ids = data.get('plo_ids')
    target_plo_ids = []

    if raw_ids:
        if not isinstance(raw_ids, list):
            raw_ids = [raw_ids]  # Bọc string/int đơn vào list

        # Ép tất cả về số nguyên (int) ngay từ đầu
        try:
            target_plo_ids = [int(x) for x in raw_ids]
        except (ValueError, TypeError):
            # Nếu có giá trị bậy bạ không convert được, bỏ qua hoặc báo lỗi
            print(f"Cảnh báo: Danh sách PLO ID chứa giá trị không hợp lệ: {raw_ids}")
            abort(400, description="Danh sách PLO ID phải là số.")

    try:
        # 2. Cập nhật bảng quan hệ chính (CO - PLO)
        if target_plo_ids:
            # Dùng .in_ với danh sách số nguyên
            new_plos = ProgrammeLearningOutcome.query.filter(
                ProgrammeLearningOutcome.id.in_(target_plo_ids)
            ).all()
            co.programme_learning_outcomes = new_plos
        else:
            co.programme_learning_outcomes = []  # Xóa hết nếu input rỗng

        # 3. Cập nhật bảng rating (CloPloAssociation)
        for clo in co.course_learning_outcomes:
            # Xóa các rating không còn được chọn
            if not target_plo_ids:
                CloPloAssociation.query.filter_by(clo_id=clo.id).delete()
            else:
                CloPloAssociation.query.filter(
                    CloPloAssociation.clo_id == clo.id,
                    CloPloAssociation.plo_id.notin_(target_plo_ids)
                ).delete(synchronize_session=False)

            # Thêm rating mới nếu chưa có
            if target_plo_ids:
                existing_assocs = db.session.query(CloPloAssociation.plo_id).filter_by(clo_id=clo.id).all()

                # Tạo Set chứa ID (Int) đã tồn tại
                existing_plo_ids_set = set()
                for r in existing_assocs:
                    try:
                        existing_plo_ids_set.add(int(r[0]))
                    except (ValueError, TypeError):
                        pass

                print(f"Debug - CLO {clo.id} Existing: {existing_plo_ids_set} | Target: {target_plo_ids}")

                for plo_id in target_plo_ids:
                    # Bây giờ cả plo_id và existing_plo_ids_set đều là INT
                    if plo_id not in existing_plo_ids_set:
                        new_assoc = CloPloAssociation(clo_id=clo.id, plo_id=plo_id, rating=0)
                        db.session.add(new_assoc)

        db.session.commit()
        return jsonify(co.to_dict())

    except Exception as e:
        db.session.rollback()
        print(f"Lỗi update_co_plos: {e}")
        return jsonify(success=False, message=f"Lỗi server: {str(e)}"), 500


@api.route('/course-objectives/<int:co_id>/course-learning-outcomes', methods=['POST'])
@login_required
def add_course_learning_outcome(co_id):
    course_objective = db.session.get(CourseObjective, co_id)
    if not course_objective:
        abort(404, description="Không tìm thấy mục tiêu môn học (CO) cha.")

    data = request.get_json()
    if not data or 'clo_content' not in data:
        abort(400, description="Yêu cầu phải là JSON và chứa 'clo_content'.")

    clo_description = data.get('clo_content')
    if not clo_description:
        abort(400, description="Nội dung CLO không được rỗng.")

    try:
        new_clo = CourseLearningOutcome(
            content=clo_description,
            course_objective_id=course_objective.id
        )
        db.session.add(new_clo)

        parent_plos = course_objective.programme_learning_outcomes
        for plo in parent_plos:
            new_association = CloPloAssociation(
                clo=new_clo,
                plo_id=plo.id,
                rating=0
            )
            db.session.add(new_association)
        db.session.commit()
        return jsonify(new_clo.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"Lỗi server: {str(e)}"), 500


@api.route('/course-learning-outcomes/<int:clo_id>', methods=['PATCH'])
@login_required
def update_course_learning_outcome(clo_id):
    clo = db.session.get(CourseLearningOutcome, clo_id)
    if not clo:
        abort(404, description="Không tìm thấy CLO.")

    data = request.get_json()
    if not data or 'content' not in data:
        abort(400, description="Yêu cầu phải là JSON và chứa trường 'content'.")

    clo.content = data.get('content')
    try:
        db.session.commit()
        # Trả về đối tượng CLO đã được cập nhật
        return jsonify(clo.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=str(e)), 500


@api.route('/course-learning-outcomes/<int:clo_id>', methods=['DELETE'])
@login_required
def delete_course_learning_outcome(clo_id):
    course_learning_outcome = db.session.get(CourseLearningOutcome, clo_id)
    if not course_learning_outcome:
        abort(404, description="Không tìm thấy CLO để xóa.")

    try:
        db.session.delete(course_learning_outcome)
        db.session.commit()
        return jsonify({"success": True, "message": "Đã xóa CLO thành công."})
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"Lỗi server: {str(e)}"), 500


@api.route('/syllabuses/<int:syllabus_id>/learning-materials', methods=['POST'])
@login_required
def add_learning_material(syllabus_id):
    syllabus = db.session.get(Syllabus, syllabus_id)
    if not syllabus:
        flash('Không tìm thấy đề cương!', 'danger')
        return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))

    data = request.get_json()
    if not data or 'name_material' not in data or 'type_material_id' not in data:
        abort(400, description="Thiếu tên tài liệu hoặc loại tài liệu.")

    name_material = data.get('name_material')
    type_material_id = data.get('type_material_id')

    try:
        lm_obj = dao.find_learning_material(name=name_material)

        if not lm_obj:
            lm_obj = LearningMaterial(
                name=name_material,
                type_material_id=int(type_material_id),
            )
            db.session.add(lm_obj)

        if lm_obj not in syllabus.learning_materials:
            syllabus.learning_materials.append(lm_obj)
            db.session.commit()
            return jsonify(lm_obj.to_dict()), 201
        else:
            db.session.rollback()
            return jsonify(success=False, message="Tài liệu này đã có trong đề cương."), 409

    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"Lỗi server: {str(e)}"), 500


@api.route('/syllabuses/<int:syllabus_id>/learning-materials/<int:material_id>', methods=['DELETE'])
@login_required
def delete_learning_material(syllabus_id, material_id):
    syllabus = dao.get_syllabus_by_id(syllabus_id)
    if not syllabus:
        abort(404, description="Không tìm thấy đề cương.")

    material_to_remove = dao.find_learning_material(id=material_id)
    if not material_to_remove:
        abort(404, description="Không tìm thấy tài liệu.")

    try:
        if material_to_remove in syllabus.learning_materials:
            # Xóa mối quan hệ, không xóa tài liệu gốc
            syllabus.learning_materials.remove(material_to_remove)
            db.session.commit()
            return jsonify({"success": True, "message": "Đã xóa tài liệu khỏi đề cương."})
        else:
            abort(404, description="Tài liệu không có trong đề cương này.")
    except Exception as e:
        db.session.rollback()
        return jsonify(success=False, message=f"Lỗi server: {str(e)}"), 500
