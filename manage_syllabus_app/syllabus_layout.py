# ====================SUBJECT=============================
# Mọi thay đổi về cấu trúc (thêm/bớt phần) đều phải được thực hiện ở đây.

MASTER_STRUCTURE = [
    {
        "name": "Thông tin tổng quát - General Information",
        "code": "general_info",
        "position": 1,
        "sub_sections": [
            {"name": "Tên môn học tiếng Anh/Course title in English", "type": "text", "position": 1},
            {"name": "Phương thức giảng dạy", "type": "selection", "position": 2, "attribute_group_id": 1},
            {"name": "Ngôn ngữ giảng dạy", "type": "selection", "position": 3, "attribute_group_id": 3},
            {"name": "Thành phần kiến thức", "type": "selection", "position": 4, "attribute_group_id": 2},
            {"name": "Số tín chỉ / Credits", "type": "reference", "position": 5, "reference_code": "credit"},
            {"name": "Phụ trách môn học/ Administration of the course", "type": "reference", "position": 6, "reference_code": "director"},
        ]
    },
    {
        "name": "Mô tả môn học - Course Overview",
        "code": "course_overview",
        "position": 2,
        "sub_sections": [
            {"name": "Mô tả chi tiết", "type": "text", "position": 1},
            {"name": "Môn học điều kiện/Requirements", "type": "reference", "position": 2, "reference_code": "requirement_subject"},
            {"name": "Mục tiêu môn học, Chuẩn đầu ra và PLOs", "type": "reference", "position": 3, "reference_code": "objectives_and_outcomes"},
            {"name": "Chuẩn đầu ra môn học - Course Learning Outcomes", "type": "reference", "position": 4, "reference_code": "course_learning_outcomes"},
            {"name": "Học liệu - Textbook and materials", "type": "reference", "position": 5, "reference_code": "learning_material"},
        ]
    },
    # --- VÍ DỤ: NẾU MUỐN THÊM PHẦN MỚI---
    # {
    #     "name": "Đánh giá môn học",
    #     "code": "course_evaluation",
    #     "position": 3,
    #     "sub_sections": [
    #         {"name": "Thành phần đánh giá", "type": "text", "position": 1},
    #         {"name": "Thang điểm", "type": "selection", "position": 2, "attribute_group_id": 4} # Giả sử có group 4
    #     ]
    # }
]