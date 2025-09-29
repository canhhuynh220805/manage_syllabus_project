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

    // Gọi đến API endpoint mới mà chúng ta đã tạo ở backend
    fetch('/get_lecturer_detail/' + lecturerId)
        .then(response => response.json())
        .then(data => {
            if (data) {
                // Cập nhật giá trị của các ô input với thông tin mới
                emailInput.value = data.email;
                roomInput.value = data.room;
            }
        })
        .catch(error => console.error('Error fetching lecturer details:', error));
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
                onclick="removeSelection(this)">
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
        <span class="badge bg-success">${ploId}</span>
        <button type="button" onclick="removePill(this)" class="btn btn-danger btn-sm sm-2"><i
                class="fa-solid fa-trash"></i>
        </button>
        <input type="hidden" name="plo_ids" value="${ploId}">
    `;
    container.appendChild(pill);
}


document.addEventListener('DOMContentLoaded', ()=>{

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
})