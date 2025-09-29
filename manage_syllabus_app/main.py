from flask import render_template, request, url_for, flash, jsonify
from werkzeug.utils import redirect

from manage_syllabus_app import app

from manage_syllabus_app import db

from manage_syllabus_app.models import Faculty, Lecturer, Credit, Subject, Syllabus, RequirementSubject, \
    TypeRequirement, MainSection, LearningMaterial, TypeLearningMaterial, TextSubSection, \
    CourseLearningOutcome, CourseObjective, SelectionSubSection, AttributeValue, ProgrammeLearningOutcome, \
    CloPloAssociation


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


app.jinja_env.filters['roman'] = to_roman


@app.route('/')
def index():
    all_faculties = Faculty.query.all()
    syllabuses = Syllabus.query.all()
    all_lecturers = Lecturer.query.all()
    return render_template('index.html', syllabuses=syllabuses, faculty=all_faculties, lecturer=all_lecturers)


@app.route('/editor')
def editor():
    return render_template('editor.html')


@app.route('/syllabus/<int:syllabus_id>/')
def syllabus_detail(syllabus_id):
    all_type_subjects = TypeRequirement.query.all()
    all_subjects = Subject.query.all()
    all_faculties = Faculty.query.all()
    all_lecturers = Lecturer.query.all()
    plos = ProgrammeLearningOutcome.query.all()
    learning_materials = TypeLearningMaterial.query.all()
    syllabus = Syllabus.query.get_or_404(syllabus_id)
    return render_template('syllabus_detail.html', syllabus=syllabus,
                           all_faculties=all_faculties, all_lecturers=all_lecturers,
                           plos=plos, learning_materials=learning_materials, all_subjects=all_subjects,
                           all_type_subjects=all_type_subjects)


@app.route('/get_lecturer_detail/<int:lecturer_id>/')
def get_lecturer_detail(lecturer_id):
    lecturer = db.session.get(Lecturer, lecturer_id)
    if lecturer:
        return jsonify({
            'email': lecturer.email or '',  # Trả về chuỗi rỗng nếu là None
            'room': lecturer.room or ''
        })
    return jsonify({'error': 'Lecturer not found'}), 404


@app.route('/update_director/<int:syllabus_id>/', methods=['POST'])
def update_director(syllabus_id):
    syllabus = db.session.get(Syllabus, syllabus_id)
    if not syllabus:
        flash('Không tìm thấy đề cương', 'danger')
        return redirect(url_for('index'))

    try:
        new_faculty_id = request.form.get('faculty_id')
        new_lecturer_id = request.form.get('lecturer_id')
        if new_faculty_id:
            syllabus.faculty_id = int(new_faculty_id)
        if new_lecturer_id:
            syllabus.lecturer_id = int(new_lecturer_id)

        lecturer_to_update = db.session.get(Lecturer, syllabus.lecturer_id)
        if lecturer_to_update:
            new_email = request.form.get('lecturer_email')
            new_room = request.form.get('lecturer_room')
            lecturer_to_update.email = new_email
            lecturer_to_update.room = new_room

        db.session.commit()
    except Exception as e:
        # Nếu có lỗi xảy ra, hoàn tác lại để đảm bảo an toàn.
        db.session.rollback()
        flash(f'Cập nhật thất bại! Lỗi: {str(e)}', 'danger')

    return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))


MODEL_MAP = {
    'Subject': Subject,
    'TextSubSection': TextSubSection,
    'Credit': Credit,
    'Lecturer': Lecturer,
    'MainSection': MainSection,
    'CourseLearningOutcome': CourseLearningOutcome,
    'CourseObjective': CourseObjective,
    'LearningMaterial': LearningMaterial,
}


@app.route('/update_generic_field', methods=['POST'])
def update_generic_field():
    form_data = request.form

    model_name = form_data.get('model_name')
    object_id = form_data.get('object_id')
    syllabus_id = form_data.get('syllabus_id')
    ModelClass = MODEL_MAP.get(model_name)
    if not ModelClass or not object_id:
        flash('Yêu cầu không hợp lệ!', 'danger')
        return redirect(url_for('index'))

    obj_to_update = db.session.get(ModelClass, object_id)
    if not obj_to_update:
        flash('Không tìm thấy đối tượng', 'danger')
        return redirect(url_for('index'))
    try:
        for field, new_value in form_data.items():
            if hasattr(obj_to_update, field):
                setattr(obj_to_update, field, new_value)

        db.session.commit()
        flash("Cập nhật thành công", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Cập nhật thất bại! Lỗi: {str(e)}', 'danger')

    return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))


@app.route('/update_selection/<int:subsection_id>', methods=['POST'])
def update_selection(subsection_id):
    subsection = db.session.get(SelectionSubSection, subsection_id)
    syllabus_id = subsection.main_section.syllabus_id

    if not subsection:
        flash('Không tìm thấy tiểu mục!', 'danger')
        return redirect(url_for('index'))

    try:
        selected_ids = request.form.getlist('selected_ids')
        subsection.selected_values.clear()

        if selected_ids:
            int_ids = [int(id_str) for id_str in selected_ids]
            new_selection = AttributeValue.query.filter(AttributeValue.id.in_(int_ids)).all()
            subsection.selected_values.extend(new_selection)

        db.session.commit()
        flash("Cập nhật thành công", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Cập nhật thất bại! Lỗi: {str(e)}', 'danger')

    return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))


@app.route('/update_co_plos/<int:co_id>', methods=['POST'])
def update_co_plos(co_id):
    co = db.session.get(CourseObjective, co_id)
    if not co:
        flash('Không tìm thấy mục tiêu môn học!', 'danger')
        return redirect(url_for('index'))
    syllabus_id = request.form.get('syllabus_id')
    try:
        current_plos_id = {plo.id for plo in co.programme_learning_outcomes}
        selected_plos_id = set(request.form.getlist('plo_ids'))

        plo_to_add_ids = selected_plos_id - current_plos_id
        plo_to_remove_ids = current_plos_id - selected_plos_id

        if plo_to_add_ids:
            plos_to_add = ProgrammeLearningOutcome.query.filter(ProgrammeLearningOutcome.id.in_(plo_to_add_ids)).all()
            co.programme_learning_outcomes.extend(plos_to_add)

        if plo_to_remove_ids:
            plos_to_remove = ProgrammeLearningOutcome.query.filter(
                ProgrammeLearningOutcome.id.in_(plo_to_remove_ids)).all()
            for plo in plos_to_remove:
                co.programme_learning_outcomes.remove(plo)

        child_clos = co.course_learning_outcomes
        for clo in child_clos:
            if plo_to_remove_ids:
                CloPloAssociation.query.filter(
                    CloPloAssociation.clo_id == clo.id,
                    CloPloAssociation.plo_id.in_(plo_to_remove_ids)
                ).delete(synchronize_session=False)

            if plo_to_add_ids:
                for plo_id in plo_to_add_ids:
                    exists = CloPloAssociation.query.filter_by(plo_id=plo_id, clo_id=clo.id).first()
                    if not exists:
                        new_association = CloPloAssociation(
                            plo_id=plo_id,
                            clo_id=clo.id,
                            rating=0
                        )
                        db.session.add(new_association)

        db.session.commit();
        flash("Cập nhật thành công", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Cập nhật thất bại! Lỗi: {str(e)}', 'danger')

    return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))


@app.route('/update_learning_material_type/<int:material_id>', methods=['POST'])
def update_learning_material_type(material_id):
    syllabus_id = request.form.get('syllabus_id')
    new_learning_material_id = request.form.get('type_material_id')

    material_to_update = db.session.get(LearningMaterial, material_id)
    if not material_to_update:
        flash('Không tìm thấy loại tài liệu môn học!', 'danger')
        return redirect(url_for('index'))

    try:
        material_to_update.type_material_id = int(new_learning_material_id)
        db.session.commit();
        flash('Cập nhật loại tài liệu thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Cập nhật thất bại! Lỗi: {str(e)}', 'danger')

    return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))

@app.route('/update_rating/', methods=['POST'])
def update_rating():
    syllabus_id = request.form.get('syllabus_id')
    clo_id = request.form.get('clo_id', type=int)
    plo_id = request.form.get('plo_id')
    new_rating = request.form.get('rating')

    if not all([syllabus_id, clo_id, plo_id, new_rating]):
        flash('Yêu cầu không hợp lệ!', 'danger')
        return redirect(url_for('index'))

    association = CloPloAssociation.query.filter_by(clo_id=clo_id, plo_id=plo_id).first()

    try:
        if new_rating and new_rating.strip():
            new_rating = int(new_rating)
            if association:
                association.rating = new_rating
            else:
                new_association = CloPloAssociation(clo_id=clo_id, plo_id=plo_id, rating=new_rating)
                db.session.add(new_association)

        db.session.commit()
        flash('Cập nhật loại rating thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Cập nhật thất bại! Lỗi: {str(e)}', 'danger')

    return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))

@app.route('/update_requirement_subject/<int:subject_id>', methods=['POST'])
def update_requirement_subject(subject_id):
    syllabus_id = request.form.get('syllabus_id')
    subject = db.session.get(RequirementSubject, subject_id)

    if not subject:
        flash('Không tìm thấy môn học!', 'danger')
        return redirect(url_for('index'))

    try:
        new_requirement_subject_id = request.form.get('requirement_subject_id')
        new_type_id = request.form.get('type_subject_id')

        if new_requirement_subject_id:
            subject.require_subject_id = new_requirement_subject_id

        if new_type_id:
            subject.type_requirement_id = new_type_id

        db.session.commit();
        flash('Cập nhật thành công!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Cập nhật thất bại! Lỗi: {str(e)}', 'danger')

    return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))


@app.route('/add_requirement_subject/<string:subject_id>', methods=['POST'])
def add_requirement_subject(subject_id):
    syllabus_id = request.form.get('syllabus_id')

    new_requirement_subject_id = request.form.get('require_subject_id')
    type_requirement_id = request.form.get('type_subject_id')

    if not all([syllabus_id, new_requirement_subject_id, type_requirement_id]):
        flash('Vui lòng chọn đầy đủ thông tin!', 'danger')
        return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))

    try:
        new_requirement_subject = RequirementSubject(
            subject_id=subject_id,
            require_subject_id=new_requirement_subject_id,
            type_requirement_id=int(type_requirement_id)
        )

        db.session.add(new_requirement_subject)
        db.session.commit()
        flash('Cập nhật thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Cập nhật thất bại! Lỗi: {str(e)}', 'danger')
    return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))

@app.route('/delete_requirement_subject/<int:subject_id>', methods=['POST'])
def delete_requirement_subject(subject_id):
    syllabus_id = request.form.get('syllabus_id')

    requirement_subject = db.session.get(RequirementSubject, subject_id)
    if not requirement_subject:
        flash('Không tìm thấy môn học điều kiện để xóa!', 'danger')
        return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))

    try:
        db.session.delete(requirement_subject)
        db.session.commit()
        flash('Cập nhật thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Cập nhật thất bại! Lỗi: {str(e)}', 'danger')

    return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))

@app.route('/add_course_objective/<string:subject_id>', methods=['POST'])
def add_course_objective(subject_id):
    syllabus_id = request.form.get('syllabus_id')

    co_description = request.form.get('co_description')
    co_list_plos_id = request.form.getlist('plo_ids')

    if not all([co_description, co_list_plos_id]):
        flash('Vui lòng điền đầy đủ Mô tả cho mục tiêu!', 'danger')
        return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))


    try:
        co_list_plos = ProgrammeLearningOutcome.query.filter(ProgrammeLearningOutcome.id.in_(co_list_plos_id)).all()
        subject = db.session.get(Subject, subject_id)
        len_co = len(subject.course_objectives)
        co_name = f"CO{len_co + 1}"

        new_co = CourseObjective(
            name=co_name,
            content = co_description,
            subject = subject,
            programme_learning_outcomes = co_list_plos
        )

        db.session.add(new_co)
        db.session.commit()
        flash(f'Đã thêm mục tiêu môn học "{co_name}" thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Cập nhật thất bại! Lỗi: {str(e)}', 'danger')

    return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))

@app.route('/delete_course_objective/<int:co_id>', methods=['POST'])
def delete_course_objective(co_id):
    syllabus_id = request.form.get('syllabus_id')

    course_objective = db.session.get(CourseObjective, co_id)
    if not course_objective:
        flash('Không tìm thấy mục tiêu môn học để xóa!', 'danger')
        return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))

    try:
        db.session.delete(course_objective)
        db.session.commit()
        flash('Xóa thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Cập nhật thất bại! Lỗi: {str(e)}', 'danger')

    return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))

@app.route('/add_clo/<int:co_id>', methods=['POST'])
def add_clo(co_id):
    syllabus_id = request.form.get('syllabus_id')

    course_objective = db.session.get(CourseObjective, co_id)
    clo_description = request.form.get('clo_content')
    if not all([course_objective, clo_description]):
        flash('Vui lòng điền đầy đủ Mô tả cho mục tiêu!', 'danger')
        return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))

    try:
        new_clo = CourseLearningOutcome(
            content=clo_description,
            course_objective = course_objective,
        )
        db.session.add(new_clo)

        parent_plos = course_objective.programme_learning_outcomes

        for plo in parent_plos:
            new_association = CloPloAssociation(
                clo = new_clo,
                plo = plo,
                rating=0
            )
            db.session.add(new_association)
        db.session.commit()
        flash(f'Đã thêm thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Cập nhật thất bại! Lỗi: {str(e)}', 'danger')

    return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))



@app.route('/delete_course_learning_outcome/<int:clo_id>', methods=['POST'])
def delete_course_learning_outcome(clo_id):
    syllabus_id = request.form.get('syllabus_id')
    course_learning_outcome = db.session.get(CourseLearningOutcome, clo_id)
    try:
        db.session.delete(course_learning_outcome)
        db.session.commit()
        flash('Cập nhật thành công!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Cập nhật thất bại! Lỗi: {str(e)}', 'danger')
    return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))

@app.route('/add_learning_material/<int:syllabus_id>', methods=['POST'])
def add_learning_material(syllabus_id):
    syllabus = db.session.get(Syllabus, syllabus_id)
    if not syllabus:
        flash('Không tìm thấy đề cương!', 'danger')
        return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))

    try:
        name_material = request.form.get('name_material')
        type_material_id = request.form.get('type_material_id')

        if not all([name_material, type_material_id]):
            flash('Vui lòng điền đầy đủ thông tin!', 'danger')
            return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))

        lm_obj = LearningMaterial.query.filter_by(name=name_material).first()

        if not lm_obj:
            lm_obj = LearningMaterial(
                name=name_material,
                type_material_id=int(type_material_id),
            )
            db.session.add(lm_obj)

        if lm_obj not in syllabus.learning_materials:
            syllabus.learning_materials.append(lm_obj)
            flash('Thêm tài liệu tham khảo thành công!', 'success')
        else:
            flash('Tài liệu này đã có trong đề cương!', 'warning')

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Cập nhật thất bại! Lỗi: {str(e)}', 'danger')

    return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))

@app.route('/delete_learning_material/<int:material_id>', methods=['POST'])
def delete_learning_material(material_id):
    syllabus_id = request.form.get('syllabus_id')

    syllabus = db.session.get(Syllabus, syllabus_id)
    material_to_remove = db.session.get(LearningMaterial, material_id)
    if not material_to_remove:
        flash('Không tìm thấy tài liệu', 'danger')
        return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))

    try:
        if material_to_remove in syllabus.learning_materials:
            syllabus.learning_materials.remove(material_to_remove)
            db.session.commit()
            flash('Đã xóa tài liệu khỏi đề cương thành công!', 'success')
        else:
            flash('Tài liệu không có trong đề cương này!', 'warning')

    except Exception as e:
        db.session.rollback()
        flash(f'Cập nhật thất bại! Lỗi: {str(e)}', 'danger')
    return redirect(url_for('syllabus_detail', syllabus_id=syllabus_id))
if __name__ == '__main__':
    app.run(debug=True)
