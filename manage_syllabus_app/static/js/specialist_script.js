function collectSyllabus(){
    mainSections = []
    document.querySelectorAll('.main-section').forEach(mainDiv =>{
        const partName = mainDiv.querySelector(".part-input")
        const name = partName ? partName.value : mainDiv.dataset.name;
        const mainData = {
            position: parseInt(mainDiv.dataset.position),
            name: name,
            code: mainDiv.dataset.code,
            sub_sections: []
        }

        mainDiv.querySelectorAll('.sub-section').forEach(subDiv =>{
            const type = subDiv.dataset.type;
            const title = subDiv.querySelector(".label-input");
            const name = title ? title.value : subDiv.dataset.name;
            const code = subDiv.querySelector(".label-code");
            const subData = {
                position: parseInt(subDiv.dataset.position),
                name: name,
                code: code ? code.value : subDiv.dataset.code,
                type: type,
            }

            if(type == "text"){
                const display_mode = subDiv.dataset.displayMode
                subData.display_mode = display_mode
            }
            else if (type == "selection"){
                const attribute_group_id = parseInt(subDiv.dataset.groupId)
                subData.attribute_group_id = attribute_group_id
            }
            else if (type == "reference"){
                const reference_code = subDiv.dataset.refCode
                subData.reference_code = reference_code
            }
            else if (type == 'table'){
                const tableEl = subDiv.querySelector('table');
                const data = extractTableData(tableEl);
                subData.data = data;
            }
            mainData.sub_sections.push(subData)
        })

        mainSections.push(mainData)
    })

    return mainSections
}

function save() {
    const old_template_id = document.getElementById('template_id').value
    const name = document.getElementById('name-syllabus')
    if(!name){
        showToast('Vui lòng nhập tên mẫu đề cương', 'danger');
        return;
    }
    let data = collectSyllabus();
    data = (JSON.stringify(data));
    fetch('/syllabus/template',{
        method: 'POST',
        body: JSON.stringify({
            'name_syllabus': name.value,
            'data': data
        }),
        headers: { 'Content-Type': 'application/json' },
    }).then(res => res.json()).then(data => {
        if(data.status == 200){
            showToast('Hệ thống đang đồng bộ hóa đề cương theo mẫu mới')
            fetch(`/syllabus/sync-batch-upgrade`,{
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    'old_template_id': old_template_id,
                    'new_template_id': data.new_template_id
                }),
            }).then(res => res.json()).then(data2 => {
                if(data2.status == 200) {
                    showToast(data2.msg, 'success');
                } else {
                    showToast('Lỗi: ' + data2.err_msg, 'danger');
                }
            }).catch(err => {
                showToast("Lỗi kết nối server" + err, "danger");
            });
        }else{
            showToast('Lỗi: ' + data.err_msg, 'danger');
        }
    }).catch(err => {
        showToast("Lỗi kết nối server" + err, "danger");
    });

}

function clearDraft(templateId){
    fetch('/syllabus/draft/delete',{
        method: 'DELETE',
        body: JSON.stringify({
            'id': templateId,
        }),
        headers: { 'Content-Type': 'application/json' },
    }).then(res => res.json()).then(data => {
        if(data.status == 200) {
            showToast(data.msg, 'success');
        } else {
            showToast('Lỗi: ' + data.err_msg, 'danger');
        }
    })
}

function saveDraft(templateId){
    const data = collectSyllabus();
    btnDraft = document.getElementById("btnDraft");
    const originalText = btnDraft.innerHTML;
    btnDraft.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang lưu...';
    btnDraft.disabled = true;
    fetch('/syllabus/draft/save',{
        method: 'POST',
        body: JSON.stringify({
            'id': templateId,
            'structure': data
        }),
        headers: { 'Content-Type': 'application/json' },
    }).then(res => res.json()).then(data => {
        if(data.status == 200) {
            showToast(data.msg, 'success');
        } else {
            showToast('Lỗi: ' + data.err_msg, 'danger');
        }
    }).finally(() => {
        btnDraft.innerHTML = originalText;
        btnDraft.disabled = false;
    });
}
    document.addEventListener('DOMContentLoaded', () => {
    const contextEl = document.getElementById('editor-context');
    const rawDraft = contextEl.dataset.draft;
    const serverDraft = (rawDraft && rawDraft !== "null") ? JSON.parse(rawDraft) : null;
    const isAutoRestore = contextEl.dataset.autoRestore === "true";
    if (serverDraft) {
        if (isAutoRestore) {
            console.log("Auto restoring draft...");
            restoreDraftData(serverDraft);
            showToast('Đã tải lại bản nháp cũ', 'info');
        }
        else {
            if (confirm("Phát hiện bản nháp...")) {
                restoreDraftData(serverDraft);
            }
        }
    }
});

function restoreDraftData(savedData){
    savedData.sort((a, b) => a.position - b.position);
    data = savedData;
    data.forEach(section =>{
        const mainDiv = document.querySelector(`.main-section[data-position="${section.position}"]`);
        const labelName = mainDiv.querySelector(".part-input")
        if(labelName) labelName.value = section.name;
        mainDiv.dataset.name = section.name
        const tbody = mainDiv.querySelector('tbody');
        tbody.innerHTML = '';
        const items = section.subSections || []
        items.forEach(sub_section =>{
            let row = mainDiv.querySelector(`.sub-section[data-position="${sub_section.position}"]`);
            if (!row) {
                restoreCustomRow(tbody, sub_section.type, sub_section);
                row = tbody.querySelector(`tr[data-position="${sub_section.position}"]`);
                if (!row) row = tbody.lastElementChild;
            }
            else if (row) {
                tbody.appendChild(row);
                console.info(tbody)
                if (sub_section.name) {
                    const labelInput = row.querySelector('.label-input');
                    if (labelInput) labelInput.value = sub_section.name;
                    row.dataset.name = sub_section.name;
                }
            }
        })

        reindexRows(tbody)
    })
}
function restoreCustomRow(triggerEl, type, existingData = null, display_mode = null) {
    let targetContainer;
    if (triggerEl.tagName === 'TBODY') {
        targetContainer = triggerEl;
    } else {
        targetContainer = triggerEl.closest('tbody');
    }

    let displayMode = display_mode;
    if (existingData && existingData.display_mode) {
        displayMode = existingData.display_mode;
    }

    const template = document.getElementById(`tpl-${type}`);
    if (!template) return;
    const newRow = template.content.cloneNode(true).querySelector('tr');
    const tempPos = (existingData && existingData.position)
                    ? existingData.position
                    : (targetContainer.children.length + 1);
    newRow.dataset.position = tempPos;
    newRow.dataset.code = existingData.code;
    newRow.dataset.type = type;
    newRow.dataset.display_mode = displayMode;

    const codeValue = existingData && existingData.code ? existingData.code : '';
    const codeInputId = `code-${existingData.position}`;

    const codeInputHtml = `
        <div class="input-group input-group-sm mb-2 ps-4">
            <span class="input-group-text bg-transparent border-0 text-muted p-0 me-2 small">
                <small>Mã định danh tiểu mục:</small>
            </span>
            <input type="text"
                   class="form-control form-control-sm border-0 bg-light text-secondary font-monospace py-0 h-auto label-code"
                   style="font-size: 0.85rem;"
                   value="${codeValue}"
                   id="${codeInputId}"
                   placeholder="VD: subject_name_vi"
            >
        </div>
    `;
    if (type === 'text') {
        const contentCell = newRow.lastElementChild;
        const nameLabel = existingData.name ? existingData.name : 'Tiêu đề mục';
        const actionButtonsHtml = `
        <div class="d-flex align-items-center my-2">
            <div class="dropdown me-1">
                <button class="btn btn-sm btn-outline-success border-0 dropdown-toggle" type="button"
                        data-bs-toggle="dropdown" aria-expanded="false">
                    <i class="fas fa-plus-circle"></i> Thêm mục
                </button>
                <ul class="dropdown-menu shadow">
                    <li><a class="dropdown-item" href="javascript:void(0)" onclick="addCustomRow(this, 'text','input')"><i class="fas fa-minus me-2"></i>Text (1 dòng)</a></li>
                    <li><a class="dropdown-item" href="javascript:void(0)" onclick="addCustomRow(this, 'text', 'textarea')"><i class="fas fa-align-justify text-muted me-2"></i> Văn bản (Nhiều dòng)</a></li>
                    <li><a class="dropdown-item" href="javascript:void(0)" onclick="addCustomRow(this, 'selection')"><i class="far fa-check-square me-2"></i>Selection</a></li>
                    <li><a class="dropdown-item" href="javascript:void(0)" onclick="addCustomRow(this, 'table')"><i class="fas fa-table me-2"></i>Table</a></li>
                </ul>
            </div>
            <button type="button" class="btn btn-sm btn-outline-danger border-0"
                    onclick="removeRow(this)" title="Xóa mục này">
                <i class="fas fa-trash-alt"></i>
            </button>
        </div>
        `;
        if (displayMode === 'textarea') {
            contentCell.innerHTML = `
                    ${codeInputHtml}
                    <div class="d-flex align-items-center mb-2">
                        <label class="fw-bold text-dark me-2 mb-0 text-nowrap">
                            ${tempPos}.
                        </label>
                        <input
                                type="text"
                                class="form-control label-input"
                                value="${nameLabel}"
                                placeholder="Nhập tên tiểu mục"
                        >
                    </div>
                    ${actionButtonsHtml}
                    <textarea class="form-control mb-2 label-input" rows="4" placeholder="Nhập nội dung chi tiết..."></textarea>
            `;
        } else {
            contentCell.innerHTML = `
                ${codeInputHtml}
                <div class="d-flex align-items-center mb-2">
                    <label class="fw-bold text-dark me-2 mb-0 text-nowrap">
                    ${tempPos}.
                    </label>
                    <input
                            type="text"
                            class="form-control label-input"
                            value="${nameLabel}"
                            placeholder="Nhập tên tiểu mục"
                    >
                </div>
                ${actionButtonsHtml}
                <input type="text" class="form-control label-input" placeholder="Nhập nội dung...">
            `;
        }
    }else if (type === 'selection' && existingData) {
        const rowId = existingData.position;

        const selectGroup = newRow.querySelector('select');
        const openModalBtn = newRow.querySelector('button[onclick^="openCreateGroupModal"]');

        if (selectGroup) {
            selectGroup.id = `selection-group-${existingData.attribute_group_id}`;
            selectGroup.setAttribute('onchange', `updateAttributeGroupForSubSection(this, ${rowId})`);

            if (existingData && existingData.attribute_group_id) {
                newRow.dataset.groupId = existingData.attribute_group_id;
                selectGroup.value = existingData.attribute_group_id;
            }
        }

        if (openModalBtn) {
            openModalBtn.setAttribute('onclick', `openCreateGroupModal(${rowId})`);
        }

        const displayList = newRow.querySelector('[id^="display-list"]');
        if (displayList) {
            displayList.id = `display-list-${rowId}`;
            if (!existingData || !existingData.selected_values || existingData.selected_values.length === 0) {
                displayList.innerHTML = '<span class="text-muted small fst-italic">Chưa có lựa chọn</span>';
            }
        }

        const addTagBtn = newRow.querySelector('button[onclick^="loadOptions"]');

        if (addTagBtn) {
            const currentGroupId = (existingData && existingData.attribute_group_id) ? existingData.attribute_group_id : '';
            addTagBtn.setAttribute('onclick', `loadOptions(this, ${rowId}, '${currentGroupId}')`);
            const parentDiv = addTagBtn.closest('.dropdown') || addTagBtn.parentElement;
            const dropdownMenu = parentDiv.querySelector('.dropdown-menu');
            if (dropdownMenu) {
                dropdownMenu.id = `dropdown-menu-${rowId}`;
                dropdownMenu.innerHTML = '';
                dropdownMenu.removeAttribute('data-loaded');
            }
        }

        if (existingData && existingData.name) {
            newRow.dataset.name = existingData.name;
            const labelInput = newRow.querySelector('.label-input');
            if (labelInput) labelInput.value = existingData.name;
            const labelContainer = labelInput.closest('.d-flex');
            if (labelContainer) {
                labelContainer.insertAdjacentHTML('afterend', codeInputHtml);
            }
        }
    }
    else if (type=="reference"){
        const labelInput = newRow.querySelector('.label-input');
        if (labelInput) {
            const labelContainer = labelInput.closest('.d-flex');
            if (labelContainer) {
                labelContainer.insertAdjacentHTML('afterend', codeInputHtml);
            }
        }
    }

    targetContainer.appendChild(newRow);
    return newRow
}

function createTemplate(){
    showConfirmDialog(
    "Xác nhận tạo mới","Tạo mới từ phiên bản này" ,
    function(){
        const data = collectSyllabus();
    }
    )
}

function addCustomRow(btn, type, display_mode = null){
    const currentRow = btn.closest('tr');
    const timestamp = Date.now();
    const tempId = Date.now();
    let templateId = `tpl-${type}`;

    if (type == 'text' && display_mode == 'textarea') {
        templateId = 'tpl-textarea';
    }

    const template = document.getElementById(templateId);
    if (!template) {
        console.error(`Không tìm thấy template: ${templateId}`);
        return;
    }

    const cloneFragment = template.content.cloneNode(true);
    const newRow = cloneFragment.querySelector('tr');

    newRow.dataset.type = type;
    newRow.dataset.position = "";
    newRow.dataset.name = "";
    newRow.dataset.displayMode = display_mode;

    currentRow.insertAdjacentElement('afterend', newRow);
    reindexRows(currentRow.closest('tbody'));
    const labelInput = newRow.querySelector('.label-input');
    if (labelInput) {
        labelInput.id = `content-${tempId}`;
    }
    if (type === 'selection') {

        const selectGroup = newRow.querySelector('select[id^="selection-group"]');
        const openModalBtn = newRow.querySelector('button[onclick^="openCreateGroupModal"]');

        if (selectGroup) {
            selectGroup.id = `selection-group-${tempId}`;
            selectGroup.setAttribute('onchange', `updateAttributeGroupForSubSection(this, ${tempId})`);
        }
        if (openModalBtn) {
            openModalBtn.setAttribute('onclick', `openCreateGroupModal(${tempId})`);
        }
        const displayList = newRow.querySelector('[id^="display-list"]');
        if (displayList) {
            displayList.id = `display-list-${tempId}`;
            displayList.innerHTML = '<span class="text-muted small fst-italic">Chưa có lựa chọn</span>';
        }


        const addTagBtn = newRow.querySelector('button[onclick^="loadOptions"]');

        if (addTagBtn) {
            addTagBtn.setAttribute('onclick', `loadOptions(this, ${tempId}, '')`);
            const parentDiv = addTagBtn.parentElement;
            const dropdownMenu = parentDiv.querySelector('.dropdown-menu');

            if (dropdownMenu) {
                dropdownMenu.id = `dropdown-menu-${tempId}`;
                dropdownMenu.innerHTML = '';
                dropdownMenu.removeAttribute('data-loaded');
            }
        }
    }
}

function removeRow(btn) {
    showConfirmDialog(
        "Xác nhận xóa"
        ,"Bạn chắc chắn muốn xóa mục này?",
        function(){
            const row = btn.closest('tr');
            const tbody = row.closest('tbody');
            row.remove();
            reindexRows(tbody);
        }
    )
}
function reindexRows(tbody) {
    let index = 1;
    tbody.querySelectorAll('tr.sub-section').forEach(row => {
        row.dataset.position = index;
        const indexSpan = row.querySelector('.item-index, label.fw-bold');
        if (indexSpan) {
            indexSpan.innerText = index + ". ";
        }
        index++;
    });
}

function addTableRow(btn){
    const table = btn.closest('.card-body').querySelector('table');
    const tbody = table.querySelector('tbody');

    const headerCols = table.querySelectorAll("thead tr th")
    const colCount = headerCols.length - 1;

    const tr = document.createElement('tr');
    tr.className = "bg-primary bg-opacity-10";

    let cellsHtml = '';
    for (let i = 0; i < colCount; i++) {
        cellsHtml += `
            <td class="p-0">
                <textarea rows="1"
                   class="form-control border-0 bg-transparent fw-bold shadow-none hybrid-textarea"
                   oninput="resizeHybrid(this)"></textarea>
            </td>
        `;
    }
    cellsHtml += `
        <td class="text-center p-0 action-cell">
            <button type="button" class="btn btn-sm btn-outline-danger border-0 ms-1" onclick="delTableRow(this)">
                <i class="fas fa-trash-alt"></i>
            </button>
        </td>
    `;

    tr.innerHTML = cellsHtml;
    tbody.appendChild(tr);
}

function addTableCol(btn){
    const table = btn.closest('.card-body').querySelector('table');
    const theadRow = table.querySelector('thead tr');
    const tbodyRows = table.querySelectorAll('tbody tr');

    const headerCols = table.querySelectorAll("thead tr th")
    const colCount = headerCols.length - 1;

    const newTh = document.createElement('th');
    newTh.className = "text-center p-0";
    newTh.style.width = "1%";
    newTh.innerHTML = `
        <div class="d-inline-flex justify-content-center w-100">
            <textarea rows="1"
               class="form-control border-0 bg-transparent fw-bold shadow-none hybrid-textarea"
               oninput="resizeHybrid(this)">Cột ${colCount + 1}</textarea>
            <button type="button" class="btn btn-sm btn-outline-danger border-0 ms-1"
                    onclick="delTableCol(this)">
                <i class="fas fa-trash-alt"></i>
            </button>
        </div>
    `

    const actionTh = theadRow.lastElementChild;
    actionTh.before(newTh);

    tbodyRows.forEach(row => {
        const newTd = document.createElement('td');
        newTd.className = "p-0";
        newTd.innerHTML = `
            <td class="p-0">
                <textarea rows="1"
                   class="form-control border-0 bg-transparent fw-bold shadow-none hybrid-textarea"
                   oninput="resizeHybrid(this)"></textarea>
            </td>
        `;
        let actionTd = row.querySelector(".action-cell")
        if(actionTd){
            actionTd.before(newTd);
        }
    });
}

function saveTable(btn){
    const cardBody = btn.closest('.card-body');
    const table = cardBody.querySelector('table');
    const data = extractTableData(table);
//    const mainDraftBtn = document.querySelector('button[onclick*="saveDraft"]');
//    if(mainDraftBtn)
//        mainDraftBtn.click()
}

function delTableCol(btn){
    if (!confirm('Bạn có chắc muốn xóa cột này? Dữ liệu cột sẽ mất hết.')) return;

    const th = btn.closest('th');
    const table = th.closest('table');

    const columnIndex = th.cellIndex;
    th.remove();

    const rows = table.querySelectorAll('tbody tr');
    rows.forEach(r => {
        if (r.cells[columnIndex]) {
            r.cells[columnIndex].remove();
        }
    })
}

function delTableRow(btn){
    if (confirm('Bạn có chắc muốn xóa hàng này?')) {
        const row = btn.closest('tr');
        row.remove();
    }
}

function resizeHybrid(el) {
    // -----------------------------------------------------------
    // PHẦN 1: CHUẨN BỊ THƯỚC ĐO (SPAN)
    // -----------------------------------------------------------
    let measureSpan = document.getElementById('hybrid-measure-span');
    if (!measureSpan) {
        measureSpan = document.createElement('span');
        measureSpan.id = 'hybrid-measure-span';
        measureSpan.style.visibility = 'hidden';
        measureSpan.style.position = 'absolute';
        measureSpan.style.whiteSpace = 'pre'; // Đo trên 1 dòng
        measureSpan.style.top = '-9999px';
        document.body.appendChild(measureSpan);
    }

    // Copy font style để đo chính xác
    const styles = window.getComputedStyle(el);
    measureSpan.style.fontFamily = styles.fontFamily;
    measureSpan.style.fontSize = styles.fontSize;
    measureSpan.style.fontWeight = styles.fontWeight;
    measureSpan.style.letterSpacing = styles.letterSpacing;
    measureSpan.style.paddingLeft = styles.paddingLeft;
    measureSpan.style.paddingRight = styles.paddingRight;

    // Lấy nội dung hiện tại
    measureSpan.textContent = el.value || el.placeholder || '';

    // -----------------------------------------------------------
    // PHẦN 2: XỬ LÝ CO GIÃN CHIỀU NGANG (WIDTH)
    // -----------------------------------------------------------
    const realWidth = measureSpan.offsetWidth;
    const MAX_WIDTH = 300;
    const MIN_WIDTH = 60; // Kích thước tối thiểu

    // Tính toán width mới dựa trên nội dung
    let targetWidth = realWidth + 10; // +Buffer
    if (targetWidth > MAX_WIDTH) targetWidth = MAX_WIDTH;
    if (targetWidth < MIN_WIDTH) targetWidth = MIN_WIDTH;

    // [MẤU CHỐT CO LẠI NGANG]:
    // Khi bạn xóa chữ -> realWidth giảm -> targetWidth giảm.
    // Dòng này gán trực tiếp width bé hơn vào -> Textarea lập tức co lại.
    el.style.minWidth = targetWidth + 'px';

    // -----------------------------------------------------------
    // PHẦN 3: XỬ LÝ CO GIÃN CHIỀU DỌC (HEIGHT)
    // -----------------------------------------------------------

    // [MẤU CHỐT CO LẠI DỌC - QUAN TRỌNG NHẤT]:
    // Bước 1: Phải Reset chiều cao về 'auto' để nó "xẹp" xuống
    el.style.height = 'auto';

    // Bước 2: Đo lại chiều cao thực tế (lúc này đã xẹp)
    let newHeight = el.scrollHeight;

    // Bước 3: Gán chiều cao mới
    el.style.height = newHeight + 'px';
}

function initHybridTextareas() {
    document.querySelectorAll('.hybrid-textarea').forEach(el => {
        el.removeAttribute('style');
        resizeHybrid(el);
    });
}
document.addEventListener('DOMContentLoaded', initHybridTextareas);

function openCreateGroupModal(subSectionId) {
    document.getElementById('target-sub-section-id').value = subSectionId;
    document.getElementById('new-group-name').value = '';
    document.querySelectorAll('.attr-value').forEach(input => input.value = '');
    var myModal = new bootstrap.Modal(document.getElementById('createGroupModal'));
    myModal.show();
}

function addMoreAttrInput(){
    const container = document.getElementById('new-attributes-container');
    const div = document.createElement('div');
    div.className = 'input-group mb-2';
    div.innerHTML = `
        <input type="text" class="form-control attr-value"
                                   placeholder="Giá trị mới">
        <button class="btn btn-primary" onclick="removeAttrInput(this)">Xóa giá trị</button>
    `
    container.appendChild(div);
}

function removeAttrInput(btn){
    const div = btn.closest('div')
    div.remove();
}

function submitNewGroup(){
    const name = document.getElementById('new-group-name').value;
    const values = Array.from(document.querySelectorAll('.attr-value'))
                        .map(input => input.value)
                        .filter(val => val.trim() !== "")
    if(!name){
        showToast("Vui lòng nhập tên nhóm thuộc tính", "danger");
        return;
    }
    if(values.length == 0){
        showToast("Vui lòng nhập ít nhất 1 giá trị", "danger");
        return;
    }

    fetch(`/attribute-group`,{
        method: 'POST',
        headers: {
        'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'name': name,
            'attribute_values': values
        })
    }).then(res => res.json()).then(data =>{
        if(data.status == 200){
            showToast(data.msg, 'success')
            const newGroup = data.data;
            const allSelects = document.querySelectorAll('select[id^="selection-group-"]');
            allSelects.forEach(select => {
                const option = new Option(newGroup.name, newGroup.id);
                select.add(option);
            });
            const targetId = document.getElementById('target-sub-section-id').value;
            const targetSelect = document.getElementById(`selection-group-${targetId}`);
            if(targetSelect) {
                targetSelect.value = newGroup.id;
            }
            bootstrap.Modal.getInstance(document.getElementById('createGroupModal')).hide();
        }else
            showToast(data.err_msg, 'danger')
    }).catch(err => {
        console.error('Lỗi:', err);
        showToast('Mất kết nối đến máy chủ!', 'danger');
    });
}

function updateAttributeGroupForSubSection(selectElement, subSectionId) {
    const newGroupId = selectElement.value;
    const row = selectElement.closest('tr');
    if(row) {
        row.setAttribute('data-group-id', newGroupId);
    }

    const addBtnRight = row.querySelector('button[onclick^="loadOptions"]');
    if(addBtnRight) {
        addBtnRight.setAttribute('onclick', `loadOptions(this, ${subSectionId}, ${newGroupId})`);
    }

    const url = `/attribute-group/${newGroupId}?subsection_id=${subSectionId}`;
    fetch(url,{
        method: 'GET',
        headers: {
        'Content-Type': 'application/json'
        },
    }).then(res => res.json()).then(data => {
        if(data.status == 200){

        }else{
            showToast(data.err_msg, 'danger')
        }
    }).catch(err => {
        console.error('Lỗi:', err);
        showToast('Mất kết nối đến máy chủ!', 'danger');
    });
}

function extractTableData(table){
    if(!table) return;

    const headersCell = table.querySelectorAll('thead tr th:not(:last-child)');
    const headers = Array.from(headersCell).map(th => {
        const input = th.querySelector('textarea.hybrid-textarea');
        return input ? input.value.trim() : "";
    });
    const rowElements = table.querySelectorAll('tbody tr');
    const rows = Array.from(rowElements).map(tr => {
        const cells = tr.querySelectorAll('td:not(:last-child)');
        if (cells.length === 0) return null;
        return Array.from(cells).map(td => {
            const input = td.querySelector('textarea.hybrid-textarea');
            return input ? input.value.trim() : "";
        });
    }).filter(row => row !== null && row.length > 0);;
    return {
        header: headers,
        rows: rows
    }
}