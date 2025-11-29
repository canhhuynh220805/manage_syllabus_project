// Scripts cho hiệu ứng Navbar
window.addEventListener('DOMContentLoaded', event => {

    // Hàm co nhỏ Navbar
    var navbarShrink = function () {
        const navbarCollapsible = document.body.querySelector('#mainNav');
        if (!navbarCollapsible) {
            return;
        }
        if (window.scrollY === 0) {
            navbarCollapsible.classList.remove('navbar-shrink')
        } else {
            navbarCollapsible.classList.add('navbar-shrink')
        }
    };

    // Co nhỏ navbar ngay khi tải trang (nếu trang không ở trên cùng)
    navbarShrink();

    // Co nhỏ navbar khi cuộn trang
    document.addEventListener('scroll', navbarShrink);

    // Tự động đóng menu trên di động khi một mục được chọn
    const navbarToggler = document.body.querySelector('.navbar-toggler');
    const responsiveNavItems = [].slice.call(
        document.querySelectorAll('#navbarResponsive .nav-link')
    );
    responsiveNavItems.map(function (responsiveNavItem) {
        responsiveNavItem.addEventListener('click', () => {
            if (window.getComputedStyle(navbarToggler).display !== 'none') {
                navbarToggler.click();
            }
        });
    });


    const addFormContainers = document.querySelectorAll('.add-form-container');

    addFormContainers.forEach( container =>{
        const addBtn = container.querySelector('.add-btn');
        const addForm = container.querySelector('.add-form');
        const cancelBtn = container.querySelector('.cancel-btn');

        if(addBtn && addForm && cancelBtn){
            addBtn.addEventListener('click', () =>{
                addForm.style.display = 'block';
                addBtn.style.display = 'none';
            })

            cancelBtn.addEventListener('click', () =>{
                addForm.style.display = 'none';
                addBtn.style.display = 'block';
            })
        }
    })

     document.querySelectorAll('.ajax-form').forEach(form => {
        form.addEventListener('submit', function (event) {
            event.preventDefault(); // Ngăn tải lại trang

            const formData = new FormData(this);
            const url = this.action;
            const method = this.method;

            fetch(url, {
                method: method,
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => { throw new Error(err.message || 'Có lỗi xảy ra'); });
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    location.reload(); // Tải lại trang để thấy thay đổi
                } else {
                    alert('Lỗi: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Fetch Error:', error);
                alert('Không thể gửi yêu cầu: ' + error.message);
            });
        });
    });

    document.querySelectorAll('.rest-form').forEach(form => {
            form.addEventListener('submit', function(event) {
                event.preventDefault(); // Luôn ngăn tải lại trang

                const url = this.dataset.url; // Lấy URL từ data-url
                const method = this.dataset.method.toUpperCase(); // Lấy Method từ data-method (PATCH, POST, DELETE)

                console.log(`Đang gửi qua 'rest-form' (API mới) tới ${method} ${url}`);

                const formData = new FormData(this);
                // Chuyển FormData thành một đối tượng JSON
                let jsonData = {};
                  formData.forEach((value, key) => {
                      const inputField = form.querySelector(`[name="${key}"]`);

                      // Bỏ qua nếu là trường ẩn hoặc bị vô hiệu hóa
                      if (!inputField || inputField.disabled ) {
                          return;
                      }

                      // Kiểm tra xem key đã tồn tại (trường hợp mảng)
                      if (key in jsonData) {
                          // Nếu đã là mảng, push thêm
                          if (Array.isArray(jsonData[key])) {
                              jsonData[key].push(value);
                          } else {
                              // Nếu chưa là mảng, tạo mảng mới
                              jsonData[key] = [jsonData[key], value];
                          }
                      } else {
                          // Nếu là lần đầu thấy key này, gán giá trị
                          jsonData[key] = value;
                      }
                  });

                fetch(url, {
                    method: method,
                    headers: {
                        'Content-Type': 'application/json', // Báo cho server biết chúng ta gửi JSON
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify(jsonData) // Gửi body dạng JSON
                })
                .then(response => {
                    if (!response.ok) {
                        // Nếu lỗi, đọc lỗi JSON từ server
                        return response.json().then(err => {
                            throw new Error(err.message || err.description || 'Có lỗi từ server');
                        });
                    }
                    // Nếu thành công (200 OK, 201 Created), đọc data JSON
                    return response.json();
                })
                .then(data => {
                    // 'data' là đối tượng JSON được cập nhật (từ hàm to_dict())
                    console.log('Thành công! Dữ liệu trả về:', data);

                    // Tạm thời vẫn reload để thấy kết quả
                    alert('Cập nhật (qua API mới) thành công!');
                    location.reload();
                })
                .catch(error => {
                    console.error('Lỗi REST API:', error);
                    alert('Không thể gửi yêu cầu: ' + error.message);
                });
            });
        });
    const facultySelect = document.getElementById('faculty');
    const lecturerSelect = document.getElementById('lecturer');

    // Chỉ chạy nếu tìm thấy 2 ô này trên trang
    if (facultySelect && lecturerSelect) {

        // Hàm tải danh sách giảng viên (Đã sửa lỗi trùng lặp)
        function loadLecturers(facultyId) {

            // 1. Reset về trạng thái "Đang tải..." ngay lập tức để người dùng biết
            lecturerSelect.innerHTML = '<option value="">Đang tải dữ liệu...</option>';
            refreshSelect2(); // Cập nhật giao diện ngay

            // Nếu không có ID khoa (trường hợp bỏ chọn), reset về mặc định
            if (!facultyId) {
                lecturerSelect.innerHTML = '<option value="">Chọn giảng viên</option>';
                refreshSelect2();
                return;
            }

            // 2. Gọi API
            fetch(`/api/faculties/${facultyId}/lecturers`)
                .then(response => {
                    if (!response.ok) throw new Error('Lỗi mạng');
                    return response.json();
                })
                .then(data => {
                    // === [QUAN TRỌNG] ===
                    // Kiểm tra lại xem giá trị Khoa hiện tại có khớp với ID đang tải không
                    // (Tránh trường hợp mạng lag: Chọn Khoa A -> Chọn Khoa B -> Data Khoa A mới về tới)
                    const currentFacultyId = facultySelect.value;
                    if (currentFacultyId != facultyId) {
                        return; // Bỏ qua nếu người dùng đã đổi sang khoa khác
                    }

                    // === [SỬA LỖI TRÙNG LẶP] ===
                    // Xóa sạch danh sách một lần nữa trước khi thêm mới
                    lecturerSelect.innerHTML = '';

                    // Thêm option mặc định
                    const defaultOption = document.createElement('option');
                    defaultOption.value = '';
                    defaultOption.text = 'Chọn giảng viên';
                    lecturerSelect.appendChild(defaultOption);

                    // 3. Đổ dữ liệu mới vào
                    data.forEach(item => {
                        const option = document.createElement('option');
                        option.value = item.id;
                        option.text = item.name;
                        lecturerSelect.appendChild(option);
                    });

                    // 4. Cập nhật giao diện Select2
                    refreshSelect2();
                })
                .catch(error => {
                    console.error('Lỗi tải giảng viên:', error);
                    lecturerSelect.innerHTML = '<option value="">Lỗi tải dữ liệu</option>';
                    refreshSelect2();
                });
        }

        function refreshSelect2() {
            if (window.jQuery) {
                $(lecturerSelect).trigger('change');
            }
        }

        if (window.jQuery) {
            $('#faculty').on('change', function() {
                loadLecturers($(this).val());
            });
        } else {
            facultySelect.addEventListener('change', function() {
                loadLecturers(this.value);
            });
        }
    }
});


function toggleFieldEdit(uniqueId, isEditing) {
    const container = document.getElementById('editable-container-' + uniqueId);
    if (!container) return;

    const displayView = container.querySelector('.display-view');
    const editView = container.querySelector('.edit-view');

    if (isEditing) {
        displayView.style.display = 'none';
        editView.style.display = 'block';
        // Tự động focus vào ô nhập liệu
        const input = editView.querySelector('input, textarea');
        if (input) input.focus();
    } else {
        displayView.style.display = 'block';
        editView.style.display = 'none';
    }
}

function updateLecturerInfo(selectElement) {
    // Lấy ID của giảng viên vừa được chọn
    const lecturerId = selectElement.value;

    // Tìm form cha để có thể tìm các ô input khác
    const form = selectElement.closest('form');
    const emailInput = form.querySelector('input[name="lecturer_email"]');
    const roomInput = form.querySelector('input[name="lecturer_room"]');

    // Gọi đến API endpoint
    const api_url = `/api/lecturers/${lecturerId}`
    fetch(api_url)
        .then(response => {
            if (!response.ok) {
                // Nếu API trả về lỗi (404, 500), lấy message từ JSON
                return response.json().then(err => {
                    throw new Error(err.message || 'Lỗi không xác định');
                });
            }
            // Nếu thành công (200), trả về JSON data
            return response.json();
        })
        .then(data => {
            if (data) {
                // Cập nhật giá trị của các ô input với thông tin mới
                emailInput.value = data.email;
                roomInput.value = data.room;
            }
        })
        .catch(error => {
            console.error('Error fetching lecturer details:', error);
            // Hiển thị lỗi cho người dùng
            alert(`Không thể tải thông tin giảng viên: ${error.message}`);
        });


}

function removePill(button){
    const badge = button.closest('.selection-pill');
    if(badge)
        badge.remove();
}

function addSelection(subItemId, optionId, optionName, event) {
    event.preventDefault();
    const container = document.getElementById('edit-selected-values-' + subItemId);
    const form = document.getElementById('form-' + subItemId);

    if (form.querySelector(`input[name="selected_ids"][value="${optionId}"]`)) {
        alert("Lựa chọn này đã có");
        return;
    }

    const pill = document.createElement('div');
    pill.className = 'selection-pill';

    pill.innerHTML = `
        <span class="badge bg-success d-flex align-items-center">${optionName}</span>
        <button type="button" class="btn btn-danger btn-sm ms-2"
                onclick="removePill(this)">
            <i class="fa-solid fa-trash"></i>
        </button>
        <input type="hidden" name="selected_ids" value="${optionId}">
    `;

    container.appendChild(pill);
}

function toggleSelectionEdit(subsectionId,isEditing){
    const container = document.getElementById('selection-container-' + subsectionId);
    const displayView = container.querySelector('.display-view');
    const editView = container.querySelector('.edit-view');

    if (isEditing) {
        displayView.style.display = 'none';
        editView.style.display = 'block';
    } else {
        displayView.style.display = 'block';
        editView.style.display = 'none';
    }
}

function addPillForCO(coId, ploId, event){
    event.preventDefault();
    container = document.getElementById('edit-selected-values-co-' + coId);

    if(container.querySelector(`input[name="plo_ids"][value="${ploId}"]`)){
        alert("Lựa chọn này đã có")
        return;
    }

    const pill = document.createElement('div');
    pill.className = "selection-pill";
    pill.innerHTML = `
        <span class="badge bg-success">PLO.${ploId}</span>
        <button type="button" onclick="removePill(this)" class="btn btn-danger btn-sm sm-2"><i
                class="fa-solid fa-trash"></i>
        </button>
        <input type="hidden" name="plo_ids" value="${ploId}">
    `;
    container.appendChild(pill);
}

function toggleDetails(year, majorId) {
    // 1. Đóng tất cả các hàng mở rộng khác (nếu muốn chỉ mở 1 hàng tại 1 thời điểm)
    // document.querySelectorAll('.expansion-row').forEach(row => row.classList.add('d-none'));

    // 2. Lấy hàng mở rộng tương ứng với Năm
    const row = document.getElementById(`expand-row-${year}`);

    // 3. Ẩn tất cả các nội dung chi tiết cũ trong hàng đó
    const contents = row.querySelectorAll('.program-detail-container');
    contents.forEach(content => content.classList.add('d-none'));

    // 4. Hiển thị nội dung của ô (Ngành) được chọn
    const targetContent = document.getElementById(`detail-content-${year}-${majorId}`);
    if (targetContent) {
        targetContent.classList.remove('d-none');

        // 5. Mở hàng ra
        row.classList.remove('d-none');
    }
}

function closeRow(year) {
    const row = document.getElementById(`expand-row-${year}`);
    if (row) {
        row.classList.add('d-none');
    }
}

function confirmDelete(button) {
    // Tìm cái form chứa nút bấm này
    const form = button.closest('.form-delete');

    // Gọi SweetAlert2
    Swal.fire({
        title: 'Bạn chắc chắn muốn xóa?',
        text: "Hành động này không thể hoàn tác!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545', // Màu đỏ cho nút Xóa
        cancelButtonColor: '#007bff',  // Màu xanh cho nút Hủy (giống theme)
        confirmButtonText: 'Vâng, xóa nó!',
        cancelButtonText: 'Hủy bỏ',
        reverseButtons: true // Đảo vị trí nút cho thuận tay
    }).then((result) => {
        if (result.isConfirmed) {
            // Nếu người dùng bấm "Vâng", dùng JS submit form
            form.submit();
        }
    })
}