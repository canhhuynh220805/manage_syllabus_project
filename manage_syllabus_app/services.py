import os

from flask import json

from manage_syllabus_app import app, db
from manage_syllabus_app.models import MainSection, TextSubSection, AttributeGroup, SelectionSubSection, \
    ReferenceSubSection


def init_structure_syllabus(syllabus):
    structure_name = syllabus.structure_file or 'syllabus_2025.json'
    structures_dir = os.path.join(app.root_path, 'data', 'structures')
    json_path = os.path.join(structures_dir, structure_name)

    if not os.path.exists(json_path):
        print(f"Cảnh báo: Không tìm thấy file cấu trúc {json_path}")
        return

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            structure_data = json.load(f)
    except Exception as e:
        print(f"Lỗi đọc JSON: {e}")
        return

    for part_def in structure_data:
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
                    content=''  # Nội dung trống ban đầu
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