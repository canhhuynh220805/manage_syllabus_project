import math

from flask import render_template, request, jsonify, redirect
from flask_login import login_required, current_user

from manage_syllabus_app import app, dao, db


@app.route('/admin')
@login_required
def admin_view():
    page = request.args.get('page', 1, type=int)
    page_size = app.config.get("PAGE_SIZE", 10)
    syllabus = []
    total = 0
    if current_user.is_authenticated:
        total = dao.count_syllabuses()
        syllabus = dao.get_all_syllabuses(page=page, page_size=page_size)

    all_faculties = dao.get_all_faculties()
    total_pages = math.ceil(total / page_size)
    lecturers = dao.get_lecturers()
    years = dao.get_years()
    programs = dao.get_all_training_program()

    return render_template(
        'admin/index.html',
        syllabuses=syllabus,
        all_faculties=all_faculties,
        pages=total_pages,
        current_page=page,
        lecturers=lecturers,
        years=years,
        programs=programs,
    )


@app.route('/admin/users')
@login_required
def admin_users_view():
    page = request.args.get('page', 1, type=int)
    page_size = app.config.get("PAGE_SIZE", 10)
    total = dao.count_users()
    total_pages = math.ceil(total / page_size)
    users = dao.get_all_user(page=page)
    roles = dao.get_all_roles()
    return render_template('admin/user_management.html', users=users, pages=total_pages,
                           current_page=page, roles=roles)


@app.route('/admin/user', methods=['GET', 'POST'])
@login_required
def admin_add_user():
    if request.method == 'GET':
        return render_template('admin/create_user.html')
    else:
        try:
            name = request.form.get('name')
            username = request.form.get('username')
            email = request.form.get('email')
            role = request.form.get('role')
            password = request.form.get('password')
            confirm_password = request.form.get('confirmPassword')
            avatar = request.files.get('avatar')
            if password != confirm_password:
                err_msg = 'Mật khẩu KHÔNG khớp'
                return render_template('admin/create_user.html', err_msg=err_msg)

            dao.add_user(name=name, username=username, email=email, role=role, password=password, avatar=avatar)
            return redirect('/admin/users')
        except Exception as e:
            return render_template('admin/create_user.html', err_msg=str(e))


@app.route('/admin/user/<int:user_id>', methods=['POST'])
@login_required
def change_user_role(user_id):
    try:
        user = dao.get_user_by_id(user_id)
        if not user:
            return jsonify({
                'status': 400,
                "err_msg": "Không tìm thấy user"
            })
        data = request.json
        role_name = data.get('role_name')
        if dao.change_user_role(user, role_name):
            return jsonify({
                'status': 200,
                "msg": "Thay đổi thành công"
            })
        else:
            return jsonify({
                'status': 400,
                "err_msg": "Thay đổi thất bại"
            })
    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


# Xóa đính kèm đề cương, chưa hoàn thành
@app.route('/admin/user/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    try:
        user = dao.get_user_by_id(user_id)
        if not user:
            return jsonify({
                'status': 400,
                'err_msg': "Không tìm thấy người dùng"
            })

        db.session.delete(user)
        db.session.commit()
        return jsonify({
            'status': 200,
            'msg': "Xóa thành công"
        })
    except Exception as e:
        return jsonify({
            "status": 500,
            "err_msg": str(e)
        })


@app.route('/admin/subjects')
@login_required
def admin_subjects_view():
    page = request.args.get('page', 1, type=int)
    page_size = app.config.get("PAGE_SIZE", 10)
    total = dao.count_subjects()
    total_pages = math.ceil(total / page_size)
    subjects = dao.get_subjects()
    return render_template('admin/subject_management.html', pages=total_pages,
                           current_page=page, subjects=subjects)


@app.route('/admin/subject', methods=['GET', 'POST'])
@login_required
def admin_add_subject():
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        subject_id = data.get('subjectId')
        number_theory = data.get('numberTheory')
        number_practice = data.get('numberPractice')
        self_hour_study = data.get('hourSelfStudy')

        subject = dao.create_subject(name, subject_id, number_theory, number_practice, self_hour_study)
        if subject:
            return jsonify({
                'status': 200,
                'msg': "Tạo thành công"
            })
        else:
            return jsonify({
                'status': 400,
                'err_msg': "Tạo thất bại"
            })
    return render_template('admin/subject_form.html', subject=None)


@app.route('/admin/subject/<subject_id>', methods=['GET', 'PATCH'])
@login_required
def admin_update_subject(subject_id):
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        number_theory = data.get('numberTheory')
        number_practice = data.get('numberPractice')
        self_hour_study = data.get('hourSelfStudy')
        try:
            subject = dao.get_subject_by_id(subject_id)
            subject.name = name
            subject.credit.numberTheory = number_theory
            subject.credit.numberPractice = number_practice
            subject.credit.hourSelfStudy = self_hour_study
            db.session.commit()
            return jsonify({
                'status': 200,
                'msg': "Cập nhật thành công"
            })
        except Exception as e:
            return jsonify({
                'status': 500,
                'err_msg': str(e)
            })
    subject = dao.get_subject_by_id(subject_id)
    return render_template('admin/subject_form.html', subject=subject)


@app.route('/admin/majors')
@login_required
def admin_majors_view():
    page = request.args.get('page', 1, type=int)
    page_size = app.config.get("PAGE_SIZE", 10)
    total = dao.count_majors()
    total_pages = math.ceil(total / page_size)
    faculties = dao.get_all_faculties()
    majors = dao.get_all_majors()
    return render_template('admin/major_management.html', pages=total_pages,
                           current_page=page, faculties=faculties, majors=majors)


@app.route('/admin/major', methods=['GET', 'POST'])
@login_required
def admin_add_major():
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        major_code = data.get('majorCode')
        faculty_id = data.get('facultyId')

        major = dao.create_major(name, major_code, faculty_id)
        if major:
            return jsonify({
                'status': 200,
                'msg': "Tạo thành công"
            })
        else:
            return jsonify({
                'status': 400,
                'err_msg': "Tạo thất bại"
            })
    faculties = dao.get_all_faculties()
    return render_template('admin/major_form.html', major=None, faculties=faculties)


@app.route('/admin/major/<major_id>', methods=['GET', 'PATCH'])
@login_required
def admin_update_major(major_id):
    major = dao.get_major_by_id(major_id)
    if request.method == 'PATCH':
        try:
            data = request.json
            name = data.get('name')
            faculty_id = data.get('facultyId')
            major.name = name
            major.faculty_id = faculty_id
            db.session.commit()
            return jsonify({
                'status': 200,
                'msg': "Cập nhật thành công"
            })
        except Exception as e:
            return jsonify({
                'status': 500,
                'err_msg': str(e)
            })
    faculties = dao.get_all_faculties()
    return render_template('admin/major_form.html', major=major, faculties=faculties)


@app.route('/admin/training-program-view')
@login_required
def admin_training_programs_view():
    page = request.args.get('page', 1, type=int)
    page_size = app.config.get("PAGE_SIZE", 10)
    total = dao.count_training_programs()
    total_pages = math.ceil(total / page_size)
    programs = dao.get_all_training_program()
    years = dao.get_years()
    return render_template('admin/training_program_management.html', pages=total_pages,
                           current_page=page, programs=programs, years=years)


@app.route('/admin/training-program', methods=['GET', 'POST'])
@login_required
def admin_add_training_program():
    if request.method == 'POST':
        try:
            data = request.json
            name = data.get('name')
            academic_year = data.get('academicYear')
            major_id = data.get('majorId')
            old_program_id = data.get('oldProgramId')
            new_program = dao.create_training_program(name, academic_year, major_id, old_program_id)
            if new_program:
                return jsonify({
                    'status': 200,
                    "msg": "Tạo thành công"
                })
            else:
                return jsonify({
                    'status': 400,
                    "err_msg": "Tạo thất bại"
                })
        except Exception as e:
            return jsonify({
                'status': 500,
                'err_msg': str(e)
            })

    majors = dao.get_all_majors()
    other_programs = dao.get_all_training_program()
    return render_template('admin/training_program_form.html', program=None, majors=majors,
                           other_programs=other_programs)


@app.route('/admin/training-program/<program_id>', methods=['GET', 'PATCH'])
@login_required
def admin_update_training_program(program_id):
    program = dao.get_training_program_by_id(program_id)
    if request.method == 'PATCH':
        try:
            data = request.json
            name = data.get('name')
            academic_year = data.get('academicYear')
            major_id = data.get('majorId')

            old_program_id = data.get('oldProgramId')

            program.name = name
            program.academic_year = academic_year
            program.major_id = major_id
            if old_program_id:
                old_program = dao.get_training_program_by_id(old_program_id)
                program.syllabuses = old_program.syllabuses
            db.session.commit()
            return jsonify({
                'status': 200,
                'msg': "Lưu thành công"
            })
        except Exception as e:
            return jsonify({
                'status': 500,
                'err_msg': str(e)
            })
    majors = dao.get_all_majors()
    other_programs = dao.get_all_training_program()
    return render_template('admin/training_program_form.html', program=program, majors=majors,
                           other_programs=other_programs)


@app.route('/admin/syllabus/lecturers/<int:lecturer_id>', methods=['POST'])
@login_required
def admin_assign_lecturer_syllabus(lecturer_id):
    try:
        data = request.json
        syllabus_id = data.get('syllabusId')
        s = dao.get_syllabus_by_id(syllabus_id)
        if not s:
            return jsonify({
                'status': 404,
                'err_msg': 'Không tìm thấy đề cương'
            })

        s.lecturer_id = lecturer_id
        db.session.commit()
        return jsonify({
            "status": 200,
            "msg": "Thay đổi giảng viên thành công"
        })
    except Exception as e:
        return jsonify({
            'status': 500,
            'err_msg': str(e)
        })