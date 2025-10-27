from flask import flash
from werkzeug.security import generate_password_hash
from wtforms.validators import none_of

from manage_syllabus_app import app, db, dao
from manage_syllabus_app.models import User, UserRole, Lecturer, MainSection, TextSubSection, SelectionSubSection, \
    ReferenceSubSection
from manage_syllabus_app.seed_database import seed_data, seed_data_2, seed_data_3
import unicodedata
import re
import traceback
from manage_syllabus_app.syllabus_layout import MASTER_STRUCTURE


def strip_accents(s):
   return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')
@app.cli.command("create-db")
def create_db():
    """Tạo tất cả các bảng trong cơ sở dữ liệu."""
    with app.app_context():
        db.create_all()
        print("Đã tạo cơ sở dữ liệu thành công!")

@app.cli.command("seed-db")
def seed_db():
    """Thêm dữ liệu mẫu vào cơ sở dữ liệu."""
    with app.app_context():
        seed_data()
        seed_data_2()
        seed_data_3()
        print("Đã thêm dữ liệu mẫu thành công!")

@app.cli.command("seed-accounts")
def seed_accounts():
    """Tạo các tài khoản mẫu: 1 Admin và 3 Giảng viên."""
    with app.app_context():
        # 1. Tạo tài khoản Admin
        admin_username = 'admin'
        if not User.query.filter_by(username=admin_username).first():
            admin_user = User(
                name='Quản trị viên',
                username=admin_username,
                password=generate_password_hash('123'),
                user_role=UserRole.ADMIN
            )
            db.session.add(admin_user)
            print(f"Đã tạo tài khoản Admin: username='{admin_username}', password='123'")

        # 2. Tạo tài khoản cho 3 Giảng viên
        lecturer_names = ["Trần Thị B", "Lê Văn C", "Nguyễn Văn An"]
        for name in lecturer_names:
            lecturer = Lecturer.query.filter_by(name=name).first()
            if lecturer:
                # Tạo username tự động (ví dụ: "Trần Thị B" -> "tranthib")
                temp_name = strip_accents(name).lower()
                username = re.sub(r'\s+', '', temp_name)

                # Kiểm tra xem user đã tồn tại chưa
                if not User.query.filter_by(username=username).first():
                    new_user = User(
                        name=lecturer.name,
                        username=username,
                        password=generate_password_hash('123'),
                        user_role=UserRole.USER,
                        lecturer_id=lecturer.id  # Liên kết User với Lecturer
                    )
                    db.session.add(new_user)
                    print(f"Đã tạo tài khoản cho GV '{name}': username='{username}', password='123'")
                else:
                    print(f"Bỏ qua, tài khoản cho GV '{name}' đã tồn tại.")
            else:
                print(f"CẢNH BÁO: Không tìm thấy giảng viên '{name}' trong CSDL. Bỏ qua việc tạo tài khoản.")

        db.session.commit()
        print("Thêm tài khoản thành công!")


@app.cli.command("sync-structure")
def sync_structure():
    '''
    hàm notify đồng bộ cập nhật tất cả đề cương (observers)
    '''
    try:
        with app.app_context():
            all_syllabuses = dao.get_all_syllabuses()
            change_count = 0
            print(f"Bắt đầu đồng bộ cấu trúc cho {len(all_syllabuses)} đề cương...")

            # Lấy danh sách code/tên chuẩn từ MASTER_STRUCTURE để so sánh
            master_part_codes = {p['code'] for p in MASTER_STRUCTURE}

            for syllabus in all_syllabuses:

                # --- GIAI ĐOẠN 1: DỌN DẸP CÁC PHẦN KHÔNG CÒN TỒN TẠI ---
                parts_to_delete = [p for p in syllabus.main_sections if p.code not in master_part_codes]
                if parts_to_delete:
                    for part in parts_to_delete:
                        print(f"  -> Xóa MainSection cũ '{part.name}' khỏi '{syllabus.name}'")
                        db.session.delete(part)
                        change_count += 1

                # --- GIAI ĐOẠN 2: THÊM VÀ ĐỒNG BỘ CÁC PHẦN ---
                existing_part_codes = {p.code for p in syllabus.main_sections}

                # 2a. Thêm MainSection còn thiếu
                for part_def in MASTER_STRUCTURE:
                    if part_def['code'] not in existing_part_codes:
                        new_part = MainSection(name=part_def['name'], code=part_def['code'],
                                               position=part_def['position'])
                        syllabus.main_sections.append(new_part)
                        change_count += 1
                        print(f"  -> Thêm MainSection mới '{part_def['name']}' vào '{syllabus.name}'")

                # 2b. Đồng bộ SubSection cho từng MainSection
                for part in syllabus.main_sections:
                    part_def = next((p for p in MASTER_STRUCTURE if p['code'] == part.code), None)
                    if part_def:
                        master_sub_names = {s['name'] for s in part_def['sub_sections']}

                        # Dọn dẹp SubSection cũ
                        subs_to_delete = [s for s in part.sub_sections if s.name not in master_sub_names]
                        if subs_to_delete:
                            for sub in subs_to_delete:
                                print(f"    -> Xóa SubSection cũ '{sub.name}' khỏi phần '{part.name}'")
                                db.session.delete(sub)
                                change_count += 1

                        # Thêm SubSection mới
                        existing_sub_names = {s.name for s in part.sub_sections}
                        for sub_def in part_def['sub_sections']:
                            if sub_def['name'] not in existing_sub_names:
                                new_sub = None
                                if sub_def['type'] == 'text':
                                    new_sub = TextSubSection(name=sub_def['name'], position=sub_def['position'],
                                                             content='')
                                elif sub_def['type'] == 'selection':
                                    new_sub = SelectionSubSection(name=sub_def['name'], position=sub_def['position'],
                                                                  attribute_group_id=sub_def['attribute_group_id'])
                                elif sub_def['type'] == 'reference':
                                    new_sub = ReferenceSubSection(name=sub_def['name'], position=sub_def['position'],
                                                                  reference_code=sub_def['reference_code'])

                                if new_sub:
                                    part.sub_sections.append(new_sub)
                                    change_count += 1
                                    print(f"    -> Thêm SubSection mới '{sub_def['name']}' vào phần '{part.name}'")

            if change_count > 0:
                db.session.commit()
                print(f"\n✅ Đồng bộ thành công! {change_count} thay đổi đã được áp dụng.")
            else:
                print("\nℹ️ Cấu trúc đã được đồng bộ. Không có gì thay đổi.")
    except Exception as e:
        print(f"\n❌ ĐÃ XẢY RA LỖI: {e}")
        traceback.print_exc()
        db.session.rollback()



'''
(.venv) PS D:\PythonProject> $env:FLASK_APP="manage_syllabus_app.index"
(.venv) PS D:\PythonProject> flask create-db                          
Đã tạo cơ sở dữ liệu thành công!
(.venv) PS D:\PythonProject> flask seed-db
(.venv) PS D:\PythonProject> flask seed-accounts
'''