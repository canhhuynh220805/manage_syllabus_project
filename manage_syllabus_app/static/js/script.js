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


function activateEditMode(cell){
    if(!cell.classList.contains('is-editing')){
        cell.classList.add('is-editing');
        const input = cell.querySelector('input[type="text"], input[type="number"], textarea');
        if(input)
            input.focus();
    }
}

function cancelEditMode(cancelButton, event){
    const cell = cancelButton.closest('.editable-cell');
    cell.classList.remove('is-editing');
    // Ngăn sự kiện click bị lan ra ngoài và kích hoạt lại chế độ sửa
    event.stopPropagation();
}