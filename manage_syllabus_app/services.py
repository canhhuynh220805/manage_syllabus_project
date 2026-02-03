import copy, json
from manage_syllabus_app import app, db, dao
from manage_syllabus_app.models import MainSection, TextSubSection, AttributeGroup, SelectionSubSection, \
    ReferenceSubSection, Syllabus, Subject, Lecturer, SubSection, TableSubSection, AttributeValue


def init_structure_syllabus(syllabus):
    templates = syllabus.template

    for part_def in templates.structure:
        new_part = MainSection(
            name=part_def['name'],
            code=part_def['code'],
            position=part_def['position'],
            syllabus=syllabus,
        )
        db.session.add(new_part)

        for sub_part in part_def['sub_sections']:
            if sub_part['type'] == 'text':
                new_sub = TextSubSection(
                    name=sub_part['name'],
                    position=sub_part['position'],
                    content=''
                )
            elif sub_part['type'] == 'selection':
                # Tìm AttributeGroup tương ứng
                group_id = sub_part.get('attribute_group_id')
                attribute_group = db.session.get(AttributeGroup, group_id) if group_id else None

                new_sub = SelectionSubSection(
                    name=sub_part['name'],
                    position=sub_part['position'],
                    attribute_group=attribute_group
                )
            elif sub_part['type'] == 'reference':
                new_sub = ReferenceSubSection(
                    name=sub_part['name'],
                    position=sub_part['position'],
                    reference_code=sub_part['reference_code']
                )
            if new_sub:
                new_part.sub_sections.append(new_sub)
                db.session.add(new_sub)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi khi khởi tạo cấu trúc: {e}")


def create_fake_syllabus_from_template(template_id):
    template = dao.get_template_by_id(template_id)
    fake_syllabus = Syllabus(
        id=template_id,
        name=template.name,
        subject=Subject(name="(Môn học mẫu)", credit=dao.get_credit_by_id(1)),
        lecturer=Lecturer(name="(Tên giảng viên)"),
    )
    fake_syllabus.main_sections = []
    raw_structure = template.structure
    fake_id_counter = [-1]
    if raw_structure:
        for part_def in raw_structure:
            new_part = MainSection(
                name=part_def['name'],
                code=part_def['code'],
                position=part_def['position']
            )
            new_part.sub_sections = []
            for sub_part in part_def.get('sub_sections', []):
                clone_sub_section(sub_part, new_part, fake_id_counter)
            fake_syllabus.main_sections.append(new_part)

    return fake_syllabus

def clone_sub_section(sub_section, main_section, id):
    current_fake_id = id[0]
    id[0] -= 1

    common_data = {
        'id': current_fake_id,
        'name': sub_section['name'],
        'code': sub_section['code'],
        'position': sub_section['position'],
        'type': sub_section['type'],
    }
    new_sub_section = None

    if sub_section['type'] == 'text':
        new_sub_section = TextSubSection(
            **common_data,
            place_holder=sub_section.get('placeholder', 'place_holder'),
            display_mode=sub_section['display_mode'],
            content=""
        )
    elif sub_section['type'] == 'selection':
        new_sub_section = SelectionSubSection(
            **common_data,
            attribute_group_id=sub_section['attribute_group_id']
        )
    elif sub_section['type'] == 'reference':
        new_sub_section = ReferenceSubSection(
            **common_data,
            reference_code=sub_section['reference_code']
        )
    elif sub_section['type'] == 'table':
        data = copy.deepcopy(sub_section['data'])
        # data['rows'] = []
        new_sub_section = TableSubSection(
            **common_data,
            data=data
        )
    main_section.sub_sections.append(new_sub_section)

def merge_syllabus_data(template, syllabus):
    subject_info = syllabus.get('subject', {}) or {}
    reference_store = {
        "credit": subject_info.get('credit'),
        "requirement_subject": subject_info.get('required_subjects', []),
        "director": syllabus.get('lecturer'),
        "lecturer_info": syllabus.get('lecturer'),
        "objectives_and_outcomes": syllabus.get('course_objectives', []),
        "course_learning_outcomes": syllabus.get('course_objectives', []),
        "learning_material": syllabus.get('learning_materials', []),
        "subject_assessment": syllabus.get('assessments', [])
    }
    data_map = {}
    data_syllabus = syllabus.get('main_sections', [])
    for main in data_syllabus:
        m_code = main.get('code')
        if not m_code: continue

        sub_map = {}
        for sub in main.get('sub_sections', []):
            s_code = sub.get('code')
            if s_code:
                sub_map[s_code] = sub

        data_map[m_code] = sub_map

    merger_result = []
    for main in template:
        new_main = copy.deepcopy(main)
        old_subs = data_map.get(main.get('code'))
        new_subs = []
        for sub in main.get('sub_sections', []):
            new_sub = copy.deepcopy(sub)
            sub_type = sub.get('type')
            sub_code = sub.get('code')
            if sub_type == "reference":
                ref_code = sub.get('reference_code')
                if ref_code == 'learning_material' or ref_code == 'learning_materials':
                    print(f"DEBUG: Tìm thấy ref_code='{ref_code}'")
                    print(f"DEBUG: Có trong store không? {ref_code in reference_store}")
                    print(f"DEBUG: Dữ liệu là: {reference_store.get(ref_code)}")
                if ref_code and ref_code in reference_store:
                    ref_data = reference_store[ref_code]

                    if ref_data:
                        new_sub['ref_data'] = ref_data

                # if old_subs_storage:
                #     old_item = old_subs_storage.get(sub_code)
                #     if old_item and 'content' in old_item:
                #         new_sub['content'] = old_item['content']

            elif old_subs:
                item = old_subs.get(sub_code)
                if item:
                    if sub_type == 'text':
                        new_sub['content'] = item['content']
                        new_sub['display_mode'] = item['display_mode']
                        new_sub['placeholder'] = item['placeholder']
                    elif sub_type == 'selection':
                        new_sub['selected_value_ids'] = item['selected_value_ids']
                    elif sub_type == 'table':
                        if 'data' in item and 'rows' in item['data']:
                            if 'data' not in new_sub: new_sub['data'] = {}
                            new_sub['data']['rows'] = item['data']['rows']


            new_subs.append(new_sub)
        new_main['sub_sections'] = new_subs
        merger_result.append(new_main)
    return merger_result

def build_syllabus_structure(new_syllabus, json_structure_syllabus):

    for inx_main, main in enumerate(json_structure_syllabus):
        new_main = MainSection(
            name=main.get('name'),
            code=main.get('code'),
            position=main.get('position', inx_main + 1),
        )
        new_syllabus.main_sections.append(new_main)

        for idx_sub, sub in enumerate(main.get('sub_sections', [])):
            sub_type = sub.get('type')
            base_data = {
                'name': sub.get('name'),
                'code': sub.get('code'),
                'position': sub.get('position', idx_sub + 1),
            }
            new_sub = None
            if sub_type == 'text':
                new_sub = TextSubSection(
                    **base_data,
                    content=sub.get('content'),
                    place_holder=sub.get('placeholder'),
                    display_mode=sub.get('display_mode')
                )
            elif sub_type == 'selection':
                new_sub = SelectionSubSection(
                    **base_data,
                    attribute_group_id=sub.get('attribute_group_id')
                )

                selected_value_ids = sub.get('selected_value_ids')
                if selected_value_ids:
                    values = AttributeValue.query.filter(AttributeValue.id.in_(selected_value_ids)).all()
                    new_sub.selected_values.extend(values)

            elif sub_type == 'table':
                new_sub = TableSubSection(
                    **base_data,
                    data=sub.get('data', {})
                )
            elif sub_type == 'reference':
                new_sub = ReferenceSubSection(
                    **base_data,
                    reference_code=sub.get('reference_code')
                )

            if new_sub:
                new_main.sub_sections.append(new_sub)
                print(new_sub)


    return new_syllabus