from datetime import datetime
import math, json

from manage_syllabus_app import app, dao, login, services
import functools
from flask import render_template, request, url_for, flash, jsonify, abort, Blueprint, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import redirect
from manage_syllabus_app import db

from manage_syllabus_app.models import Faculty, Lecturer, Credit, Subject, Syllabus, RequirementSubject, \
    TypeRequirement, MainSection, LearningMaterial, TypeLearningMaterial, TextSubSection, \
    CourseLearningOutcome, CourseObjective, SelectionSubSection, AttributeValue, ProgrammeLearningOutcome, \
    CloPloAssociation, User, UserRole, AttributeGroup, TemplateSyllabus, TableSubSection, Assessment, Method, \
    MethodCourseLearningOutcome


# CÁC ROUTE GỐC
@app.route('/')
def index():
    page_size = app.config["PAGE_SIZE"]
    total = dao.count_syllabuses()
    page = request.args.get('page', 1, type=int)
    syllabus = []
    if current_user.is_authenticated:
        if current_user.user_role == UserRole.ADMIN:
            total = dao.count_syllabuses()
            syllabus = dao.get_all_syllabuses(page=page, page_size=page_size)

        elif current_user.user_role == UserRole.USER and current_user.lecturer_id:
            total = dao.count_syllabuses(lecturer_id=current_user.lecturer_id)
            syllabus = dao.get_syllabuses_by_lecturer_id(lecturer_id=current_user.lecturer_id,
                                                         page=page, page_size=page_size)
    all_faculties = dao.get_all_faculties()
    return render_template('index.html', syllabuses=syllabus, all_faculties=all_faculties,
                           pages=math.ceil(total / page_size), current_page=page)


@app.route('/specialist/editor')
@login_required
def editor():
    return render_template('specialist/editor.html')


@app.route('/specialist')
@login_required
def specialist_view():
    if current_user.user_role != UserRole.SPECIALIST:
        abort(403)
    template_files = dao.get_all_template()
    # draft_key = f"draft_syllabus_{template_id}"
    draft_template_ids = []
    for key in session.keys():
        if key.startswith('draft_syllabus_'):
            try:
                t_id = int(key.split('_')[-1])
                draft_template_ids.append(t_id)
            except ValueError:
                continue

    return render_template('specialist/index.html', template_files=template_files
                           , draft_template_ids=draft_template_ids)


@app.route('/specialist/template/<template_id>')
@login_required
def specialist_template_detail(template_id):
    if current_user.user_role != UserRole.SPECIALIST:
        abort(403)
    try:
        mock_syllabus = services.create_fake_syllabus_from_template(template_id)
    except ValueError as e:
        flash(str(e), "danger")
        return redirect(url_for('specialist_view'))
    type_assessments = dao.get_type_assessments()
    assessments = dao.get_assessments_by_syllabus(mock_syllabus.id)
    return render_template(
        'specialist/sample_syllabus_view.html',
        syllabus=mock_syllabus,
        is_sample=True,
        all_faculties=[], all_lecturers=[], all_type_learning_materials=[],
        all_subjects=[], all_type_subjects=[], plos=[], type_assessments=type_assessments,
        assessments=assessments,
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
    type_assessments = dao.get_type_assessments()
    assessments = dao.get_assessments_by_syllabus(syllabus_id)
    clos = dao.get_clos_by_subject_id(syllabus.subject_id)
    schedule_groups = dao.get_schedule_groups()
    teaching_sessions = dao.get_teaching_sessions(syllabus_id)
    return render_template('syllabus_detail.html', syllabus=syllabus,
                           all_faculties=all_faculties, all_lecturers=all_lecturers,
                           all_type_learning_materials=learning_materials,
                           all_type_subjects=all_type_subjects, all_subjects=available_subjects, plos=plos,
                           unique_plos=sorted_plos, is_editing=False, type_assessments=type_assessments,
                           assessments=assessments, clos=clos, schedule_groups=schedule_groups,
                           teaching_sessions=teaching_sessions)


# CÁC ROUTE XÁC THỰC
@app.route('/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            return render_template('login.html', err_msg="Vui lòng nhập đúng tên tài khoản và mật khẩu")
        user = dao.auth_user(username, password)
        if user:
            login_user(user=user)
        else:
            flash('Tên đăng nhập hoặc mật khẩu không chính xác!', 'danger')
        if user.user_role == UserRole.SPECIALIST:
            return redirect('/specialist')
        elif user.user_role == UserRole.ADMIN:
            return redirect('/admin')
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


@app.route('/syllabus/sync-batch-upgrade', methods=['POST'])
def syllabus_sync_batch_upgrade():
    try:
        data = request.json
        old_template_id = data['old_template_id']
        new_template_id = data['new_template_id']
        new_template = dao.get_template_by_id(new_template_id)
        if not new_template:
            return jsonify({
                'status': 400,
                'err_msg': "Không tìm thấy mẫu đề cương này"
            })
        new_structure = new_template.structure

        syllabuses = Syllabus.query.filter_by(template_id=old_template_id).all()
        if not syllabuses:
            return jsonify({
                'status': 400,
                'err_msg': "không có đề cương nào để đồng bộ"
            })

        count = 0
        for syllabus in syllabuses:
            print(f"DEBUG SYLLABUS ID: {syllabus.id}")
            print(f"DEBUG Count Learning Materials: {len(syllabus.learning_materials)}")
            exist = Syllabus.query.filter_by(
                id=syllabus.id,
                template_id=new_template_id,
                lecturer_id=syllabus.lecturer_id
            ).first()
            if exist: continue
            old_obj = syllabus.to_structure_json()

            new_syllabus_structure = services.merge_syllabus_data(new_structure, old_obj)
            now = datetime.now().strftime("%d/%m/%Y")
            s = Syllabus(
                name=f"{syllabus.name} {new_template.name}",
                subject=syllabus.subject,
                lecturer=syllabus.lecturer,
                faculty=syllabus.faculty,
                template=new_template,
                status=f"{current_user.name} đã tạo đề cương ngày {now}"
            )
            services.build_syllabus_structure(new_syllabus=s, json_structure_syllabus=new_syllabus_structure)
            count = count + 1
            db.session.add(s)

        print(f"Đã khởi tạo {count} đề cương mới")
        db.session.commit()
        return jsonify({
            'status': 200,
            'msg': f'Đã đồng bộ và tạo mới {count} đề cương.',
        })


    except Exception as e:
        return jsonify({
            'status': 500,
            'err_msg': str(e)
        })


@app.route('/syllabus/create_from_template/<template_id>', methods=['GET'])
def create_from_template(template_id):
    template_id = template_id
    try:
        new_syllabus = services.create_fake_syllabus_from_template(template_id)

        draft_key = f"draft_syllabus_{template_id}"
        draft_data = session.get(draft_key)
        attribute_groups = dao.get_all_attribute_groups()
        auto_restore = request.args.get('restore') == 'true'
        return render_template(
            'specialist/editor.html',
            is_editing=True, draft_json=draft_data, auto_restore=auto_restore,
            syllabus=new_syllabus,
            all_faculties=[], all_lecturers=[], all_type_learning_materials=[],
            all_subjects=[], all_type_subjects=[], plos=[],
            attribute_groups=attribute_groups,
            template_id=template_id,
        )
    except Exception as e:
        raise e


@app.route('/syllabus/template', methods=['POST'])
def create_template():
    try:
        data = request.json
        name = data.get('name_syllabus')
        structure = data.get('data')
        if isinstance(structure, str):
            print("Structure là String -> Cần parse")
            structure = json.loads(structure)
        else:
            print("Structure đã là List/Dict -> Dùng luôn")
        print(name)
        print(structure)
        try:
            t = TemplateSyllabus(name=f"{name} MỚI", structure=structure)
            db.session.add(t)
            db.session.commit()
        except Exception as e:
            print(e)
        return jsonify({
            'status': 200,
            'msg': 'Tạo thành công',
            'new_template_id': t.id,
        })
    except Exception as e:
        return jsonify({
            'status': 500,
            "err_msg": str(e)
        })


@app.route('/syllabus/draft/save', methods=['POST'])
def draft_save():
    try:
        data = request.json
        obj_id = data.get("id")

        draft_key = f"draft_syllabus_{obj_id}"
        session[draft_key] = data.get('structure')
        session.modified = True
        return jsonify({
            "status": 200,
            "msg": "Lưu thành công"
        })

    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": f"Lỗi {str(e)}"
        })


@app.route('/syllabus/draft/delete', methods=['DELETE'])
def draft_delete():
    try:
        data = request.json
        obj_id = data.get("id")
        draft_key = f"draft_syllabus_{obj_id}"
        session.pop(draft_key)
        session.modified = True
        return jsonify({
            "status": 200,
            "msg": "Đã xóa bản nháp"
        })
    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": f"Lỗi {str(e)}"
        })


# API ĐỀ CƯƠNG USER
@app.route('/text-subsection/<int:section_id>', methods=['PATCH'])
def update_text_subsection(section_id):
    try:
        s = TextSubSection.query.get(section_id)
        if not s:
            return jsonify({
                "status": 400,
                "err_msg": "Không tìm thấy tiểu mục"
            })

        data = request.json
        if dao.update_text_sub_section(data.get('content'), s):
            return jsonify({
                "status": 200,
                "msg": "Cập nhật thành công"
            })
        else:
            return jsonify({
                "status": 400,
                "err_msg": "Lỗi cập nhật"
            })
    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route('/table-subsection/<int:section_id>', methods=['PATCH'])
def update_table_subsection(section_id):
    try:
        s = TableSubSection.query.get(section_id)
        data = request.json
        data_table = data.get('data_table')
        s.data = data_table
        db.session.commit()
        return jsonify({
            "status": 200,
            "msg": "Cập nhật thành công"
        })
    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route('/course-objective/<int:co_id>', methods=['PATCH'])
def update_course_objective(co_id):
    try:
        co = dao.get_co_by_id(co_id)
        if not co:
            return jsonify({
                "status": 400,
                "err_msg": "Không tìm thấy mục tiêu môn học"
            })
        data = request.json
        if dao.update_co(data.get('content'), co):
            return jsonify({
                "status": 200,
                "msg": "Cập nhật thành công"
            })
        else:
            return jsonify({
                "status": 400,
                "err_msg": "Lỗi cập nhật"
            })
    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route('/course-learning-outcome/<int:clo_id>', methods=['PATCH'])
def update_course_learning_outcome(clo_id):
    try:
        clo = dao.get_clo_by_id(clo_id)
        if not clo:
            return jsonify({
                "status": 400,
                "err_msg": "Không tìm thấy mô tả chuẩn đầu ra"
            })
        data = request.json
        if dao.update_clo(data.get('content'), clo):
            return jsonify({
                "status": 200,
                "msg": "Cập nhật thành công"
            })
        else:
            return jsonify({
                "status": 400,
                "err_msg": "Lỗi cập nhật"
            })
    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route('/syllabus/<int:syllabus_id>/learning-material', methods=['POST'])
def add_learning_material(syllabus_id):
    try:
        syllabus = dao.get_syllabus_by_id(syllabus_id)
        if not syllabus:
            return jsonify({
                "status": 400,
                "err_msg": "Không tìm thấy đề cương"
            })
        data = request.json

        name = data.get('name')
        type_id = data.get('type_id')
        if dao.add_learning_material(name=name, type_id=type_id, syllabus=syllabus):
            return jsonify({
                "status": 200,
                "msg": "Thêm thành công"
            })
        else:
            return jsonify({
                "status": 400,
                "err_msg": "Thêm thất bại"
            })

    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route('/syllabus/<int:syllabus_id>/learning-material/<int:material_id>', methods=['DELETE'])
def del_learning_material(syllabus_id, material_id):
    try:
        syllabus = dao.get_syllabus_by_id(syllabus_id)
        material = dao.get_learning_material(id=material_id)
        if not syllabus or not material:
            return jsonify({
                "status": 400,
                "err_msg": "Không đủ dữ liệu"
            })
        if dao.remove_learning_material(material=material, syllabus=syllabus):
            return jsonify({
                "status": 200,
                "msg": "Xóa thành công"
            })
        else:
            return jsonify({
                "status": 400,
                "err_msg": "Xóa thất bại"
            })

    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route('/learning-material/<int:material_id>', methods=['PATCH'])
def update_learning_material(material_id):
    try:
        m = dao.get_learning_material(id=material_id)
        if not m:
            return jsonify({
                "status": 400,
                "err_msg": "Không tìm thấy tài liệu tham khảo"
            })

        data = request.json
        if dao.update_learning_material(data.get('name'), m):
            return jsonify({
                "status": 200,
                "msg": "Cập nhật thành công"
            })
        else:
            return jsonify({
                "status": 400,
                "err_msg": "Lỗi cập nhật"
            })

    except  Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route('/attribute-group/<int:group_id>', methods=['GET'])
def get_attribute_group(group_id):
    try:
        subsection_id = request.args.get('subsection_id', type=int)
        ag = AttributeGroup.query.get(group_id)
        ag_values = dao.get_attribute_group_values(group_id, subsection_id)
        if not ag_values:
            return jsonify({
                "status": 400,
                "err_msg": "Không tìm thấy nhóm thuộc tính"
            })
        return jsonify({
            "status": 200,
            "results": [item.to_dict() for item in ag_values],
            "attribute_group": {
                'id': ag.id,
                'name': ag.name,
            }
        })
    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route('/attribute-group', methods=['POST'])
def add_attribute_group():
    try:
        data = request.json
        name = data.get('name')
        attribute_values = data.get('attribute_values')
        if not name or not attribute_values:
            return jsonify({
                "status": 400,
                "err_msg": "Lỗi dữ liệu"
            })
        av = []
        for value in attribute_values:
            new_av = AttributeValue(
                name_value=value
            )
            db.session.add(new_av)
            av.append(new_av)

        ag = AttributeGroup(
            name=name,
            attribute_values=av
        )
        db.session.add(ag)
        db.session.commit()
        return jsonify({
            "status": 200,
            "msg": "Tạo nhóm thuộc tính thành công",
            'data': {
                "name": name,
                "id": ag.id,
            }
        })
    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route('/subsection/attribute', methods=['POST'])
def add_subsection_attribute():
    try:
        data = request.json
        subsection_id = data.get('subsection_id')
        attribute_id = data.get('attribute_id')
        if not subsection_id or not attribute_id:
            return jsonify({
                "status": 400,
                "err_msg": "Lỗi id"
            })

        if dao.add_attribute(subsection_id, attribute_id):
            return jsonify({
                "status": 200,
                "msg": "Thêm thành công"
            })
        else:
            return jsonify({
                "status": 400,
                "err_msg": "Thêm thất bại"
            })
    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route('/subsection/attribute', methods=['DELETE'])
def delete_subsection_attribute():
    try:
        data = request.json
        subsection_id = data.get('subsection_id')
        attribute_id = data.get('attribute_id')
        if not subsection_id or not attribute_id:
            return jsonify({
                "status": 400,
                "err_msg": "Lỗi id"
            })

        if dao.del_attribute(subsection_id, attribute_id):
            return jsonify({
                "status": 200,
                "msg": "Xóa thành công"
            })
        else:
            return jsonify({
                "status": 400,
                "err_msg": "Xóa thất bại"
            })
    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route('/syllabus/update-credits', methods=['PUT'])
def update_credits():
    try:
        data = request.json
        credit_id = data.get('credit_id')
        if not credit_id:
            return jsonify({
                "status": 400,
                "err_msg": "Không tìm thấy credit_id"
            })
        theory = data.get('theory')
        practice = data.get('practice')
        self_study = data.get('self_study')
        if not theory or not practice or not self_study:
            return jsonify({
                "status": 400,
                "err_msg": "Lỗi dữ liệu"
            })

        if dao.update_credit(credit_id, theory, practice, self_study):
            return jsonify({
                "status": 200,
                "msg": "Cập nhật thành công",
                "total": theory + practice
            })
        else:
            return jsonify({
                "status": 400,
                "err_msg": "Cập nhật thất bại"
            })
    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route('/syllabus/<int:syllabus_id>/requirement-subject', methods=['POST'])
def add_requirement_subject(syllabus_id):
    try:
        s = dao.get_syllabus_by_id(syllabus_id)
        if not s:
            return jsonify({
                "status": 400,
                "err_msg": "Không tìm thấy đề cương"
            })
        data = request.json
        subject_id = data.get('subject_id')
        type_id = data.get('type_id')
        if not subject_id or not type_id:
            return jsonify({
                "status": 400,
                "err_msg": "Thiếu thông tin môn học hoặc loại điều kiện"
            })

        if dao.add_requirement_subject(syllabus=s, subject_id=subject_id, type_id=type_id):
            subject = dao.get_subject_by_id(subject_id)
            type = dao.get_type_subject(type_id)
            return jsonify({
                "status": 200,
                "msg": "Thêm thành công",
                "subject": subject.to_dict(),
                "type": type.to_dict()
            })
        else:
            return jsonify({
                "status": 400,
                "err_msg": "Thêm thất bại"
            })
    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route('/syllabus/<int:syllabus_id>/requirement-subject/<string:req_subject_id>', methods=['DELETE'])
def delete_requirement_subject(syllabus_id, req_subject_id):
    try:
        s = dao.get_syllabus_by_id(syllabus_id)
        if not s:
            return jsonify({
                "status": 400,
                "err_msg": "Không tìm thấy đề cương"
            })

        if dao.delete_requirement_subject(syllabus=s, subject_id=req_subject_id):
            return jsonify({
                "status": 200,
                "msg": "Xóa thành công"
            })
        else:
            return jsonify({
                "status": 400,
                "err_msg": "Xóa thất bại"
            })
    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route('/course-objective/<int:co_id>/plo', methods=['POST'])
def add_plo_objective(co_id):
    try:
        co = dao.get_co_by_id(co_id)
        plo_id = request.json.get('plo_id')
        plo = dao.get_plo_by_id(plo_id)
        if not co or not plo:
            return jsonify({
                "status": 400,
                "msg": "Lỗi dữ liệu"
            })
        if dao.add_plo_for_co(co=co, plo=plo):
            return jsonify({
                "status": 200,
                "msg": "Thêm thành công"
            })
        else:
            return jsonify({
                "status": 400,
                "err_msg": "Thêm thất bại"
            })
    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route('/course-objective/<int:co_id>/delete-plo/<int:plo_id>', methods=['DELETE'])
def del_plo_objective(co_id, plo_id):
    try:
        co = dao.get_co_by_id(co_id)
        plo = dao.get_plo_by_id(plo_id)
        if not co or not plo:
            return jsonify({
                "status": 400,
                "msg": "Lỗi dữ liệu"
            })
        if dao.delete_plo_for_co(co=co, plo=plo):
            return jsonify({
                "status": 200,
                "msg": "Xóa thành công"
            })
        else:
            return jsonify({
                "status": 400,
                "err_msg": "Xóa thất bại"
            })
    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route('/subject/<subject_id>/course-objective', methods=['POST'])
def add_course_objective(subject_id):
    try:
        subject = dao.get_subject_by_id(subject_id)
        if not subject:
            return jsonify({
                "status": 400,
                "err_msg": "Không tìm thấy môn học"
            })
        data = request.json
        co_content = data.get('content')
        plo_ids = data.get('plo_ids')
        plos = dao.get_plos(plo_ids=plo_ids)
        co = CourseObjective(subject=subject, content=co_content, programme_learning_outcomes=plos)
        db.session.add(co)
        db.session.commit()
        return jsonify({
            "status": 200,
            "msg": "Thêm thành công"
        })
    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route('/subject/<subject_id>/course-objective/<int:co_id>', methods=['DELETE'])
def del_course_objective(subject_id, co_id):
    try:
        subject = dao.get_subject_by_id(subject_id)
        co = dao.get_co_by_id(co_id)
        if not subject:
            return jsonify({
                "status": 400,
                "err_msg": "Không tìm thấy môn học"
            })

        if not co:
            return jsonify({
                "status": 400,
                "err_msg": "Không tìm thấy mục tiêu môn học"
            })

        subject.course_objectives.remove(co)
        db.session.commit()
        return jsonify({
            "status": 200,
            "msg": "Xóa thành công"
        })
    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route('/course-objective/<int:co_id>/clo', methods=['POST'])
def add_course_clo(co_id):
    try:
        co = dao.get_co_by_id(co_id)
        if not co:
            return jsonify({
                "status": 400,
                "err_msg": "Không tìm thấy mục tiêu môn học"
            })
        data = request.json
        clo_content = data.get('content')
        clo = CourseLearningOutcome(content=clo_content)
        if dao.add_clo_for_co(co=co, clo=clo):
            return jsonify({
                "status": 200,
                "msg": "Thêm thành công"
            })
        else:
            return jsonify({
                "status": 400,
                "err_msg": "Thêm thất bại"
            })
    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route('/course-objective/<int:co_id>/clo/<int:clo_id>', methods=['DELETE'])
def del_course_clo(co_id, clo_id):
    try:
        co = dao.get_co_by_id(co_id)
        clo = dao.get_clo_by_id(clo_id)
        if not co or not clo:
            return jsonify({
                "status": 400,
                "err_msg": "Lỗi data"
            })

        if dao.delete_clo_for_co(co=co, clo=clo):
            return jsonify({
                "status": 200,
                "msg": "Xoa thành công"
            })
        else:
            return jsonify({
                "status": 400,
                "err_msg": "Xóa thất bại"
            })
    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route('/clo/<int:clo_id>/plo/<int:plo_id>', methods=['PUT'])
def update_rating(clo_id, plo_id):
    try:
        data = request.json
        rating = data.get('rating')
        if not rating:
            return jsonify({
                "status": 400,
                "err_msg": "Không lấy được rating"
            })
        if dao.update_rating(clo_id=clo_id, plo_id=plo_id, rating=rating):
            return jsonify({
                "status": 200,
                "msg": "Cập nhật thành công"
            })
        else:
            return jsonify({
                "status": 400,
                "err_msg": "Cập nhật thất bại"
            })
    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route('/syllabus/<int:syllabus_id>/assessment/', methods=['POST'])
def add_syllabus_assessment(syllabus_id):
    try:
        s = dao.get_syllabus_by_id(syllabus_id)
        data = request.json
        assessment_id = data.get('assessmentId')
        method_id = data.get('methodId')
        type_assess_id = data.get('typeAssessId')
        clo_ids = [int(c) for c in data.get('cloIds', [])]

        is_valid_assessment = dao.is_valid_assessment(
            assessment_id=assessment_id)  # true nếu có tồn tại false ngược lại
        is_valid_method = dao.is_valid_method(method_id=method_id)  # true nếu có tồn tại false ngược lại

        if not is_valid_assessment:
            assessment = Assessment(syllabus_id=s.id, type_assessment_id=type_assess_id)
            db.session.add(assessment)
            s.assessments.append(assessment)
        else:
            assessment = dao.get_assessment_by_id(assessment_id=assessment_id)

        if not is_valid_method:
            method = Method(
                name=data.get('methodName'),
                time=data.get('methodTime'),
                weight=data.get('weight')
            )
            assessment.assessment_methods.append(method)
            db.session.add(method)
        else:
            method = dao.get_method_by_id(method_id=method_id)
            method.name = data.get('methodName')
            method.time = data.get('methodTime')
            method.weight = data.get('weight')

        for existing_clo in method.course_learning_outcomes:
            if existing_clo.clo_id not in clo_ids:
                db.session.delete(existing_clo)

        existing_clo_ids = [c.clo_id for c in method.course_learning_outcomes]
        for clo_id in clo_ids:
            if clo_id not in existing_clo_ids:
                method.course_learning_outcomes.append(MethodCourseLearningOutcome(clo_id=int(clo_id)))

        db.session.commit()

        return jsonify({
            "status": 200,
            "msg": "Lưu thành công"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route("/assessment/<int:assessment_id>/", methods=['DELETE'])
def delete_assessment(assessment_id):
    try:
        assessment = dao.get_assessment_by_id(assessment_id)
        if not assessment:
            return jsonify({
                "status": 400,
                "err_msg": "Không tìm thấy bài đánh giá cần xóa"
            })

        db.session.delete(assessment)
        db.session.commit()
        return jsonify({
            "status": 200,
            "msg": "Xóa thành công"
        })
    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route("/methods/<int:method_id>", methods=['DELETE'])
def delete_method(method_id):
    try:
        method = dao.get_method_by_id(method_id)
        if not method:
            return jsonify({"status": 404, "err_msg": "Không tìm thấy phương pháp"})

        db.session.delete(method)
        db.session.commit()
        return jsonify({
            "status": 200,
            "msg": "Xóa thành công"
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })

