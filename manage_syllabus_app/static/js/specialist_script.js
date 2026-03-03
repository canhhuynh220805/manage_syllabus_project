var hotInstances = {};
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
            const subItemId = subDiv.dataset.id;
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
                const data = saveHandsontable(subItemId);
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
    console.log(data)
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
                    setTimeout(() => {
                        window.location.href = '/specialist';
                    }, 1500);
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

function createTemplate(){
    showConfirmDialog(
    "Xác nhận tạo mới","Tạo mới từ phiên bản này" ,
    function(){
        const data = collectSyllabus();
    }
    )
}

function saveTable(btn) {
    const subSection = btn.closest('.sub-section');
    if (subSection) {
        const subItemId = subSection.dataset.id;
        saveHandsontable(subItemId);
        showToast('Đã lưu dữ liệu bảng thành công!', 'success');
    }
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
    newRow.dataset.id = tempId;
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
    else if (type === 'table') {
        const container = newRow.querySelector('div[id^="hot-container"]');
        const dataInput = newRow.querySelector('input[id^="hot-data"]');
        const saveBtn = newRow.querySelector('button[onclick^="saveHandsontable"]');
        if (container) container.id = `hot-container-${tempId}`;
        if (dataInput) {
            dataInput.id = `hot-data-${tempId}`;
            dataInput.value = JSON.stringify({ header: ["Cột 1", "Cột 2"], rows: [["", ""]] });
        }

        if (saveBtn) saveBtn.setAttribute('onclick', `saveHandsontable('${tempId}')`);

        setTimeout(() => {
            initHandsontable(tempId, true);
        }, 1000);
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

function initHandsontable(subItemId, isEditing){
    const userInfo = document.getElementById('user-info').value;
    const container = document.getElementById(`hot-container-${subItemId}`);
    const dataInput = document.getElementById(`hot-data-${subItemId}`);
    if(!container || !dataInput) return;

    let rawData = { cornerHeader: "STT", header: ["Cột 1", "Cột 2"], rows: [["1", "1"]] };
    try {
        const parsed = JSON.parse(dataInput.value);
        if (parsed) rawData = parsed;
        if (!rawData.cornerHeader) rawData.cornerHeader = "STT";
        if (!rawData.mergeCells) rawData.mergeCells = [];
    } catch(e) { console.warn("Lỗi parse data table", e); }

    let tableData = [rawData.header].concat(rawData.rows);
    const hot = new Handsontable(container, {
        data: tableData,
        licenseKey: 'non-commercial-and-evaluation',
        rowHeaders: true,
        colHeaders: false,
        mergeCells: rawData.mergeCells.length > 0 ? rawData.mergeCells : true,
        width: '100%',
        wordWrap: true,
        autoRowSize: true,
        stretchH: 'all',
        autoWrapRow: true,
        autoWrapCol: true,
        readOnly: !isEditing,
        rowHeights: 40,
        colWidths: 80,
        rowHeaderWidth: 60,
        contextMenu: isEditing ? {
        items: {
                "row_above": { name: "Thêm hàng trên", disabled: function() { return this.getSelectedLast()[0] === 0; } },
                "row_below": { name: "Thêm hàng dưới" },
                "sp1": { name: "---------" },
                "col_left": { name: "Thêm cột trái" },
                "col_right": { name: "Thêm cột phải" },
                "sp2": { name: "---------" },
                "remove_row": { name: "Xóa hàng", disabled: function() { return this.getSelectedLast()[0] === 0 || this.countRows() <= 2; } },
                "remove_col": { name: "Xóa cột", disabled: function() { return this.countCols() <= 1; } },
                "mergeCells": { name: "Gộp / Bỏ gộp ô" },
                "sp3": { name: "---------" },
                "undo": { name: "Hoàn tác" },
                "redo": { name: "Làm lại" },
                "alignment": { name: "Căn lề" }
            }
        } : false,
        afterGetRowHeader: function(row, TH) {
            const cornerText = rawData.cornerHeader || "STT";

            if (row === 0) {
                if (isEditing) {
                    TH.innerHTML = `
                        <input type="text"
                               id="corner-input-${subItemId}"
                               value="${cornerText}"
                               style="min-width: 45px; width: ${cornerText.length + 2}ch; border: none; background: transparent; text-align: center; font-weight: bold; outline: none; padding: 0;"
                               placeholder="..."
                               onmousedown="event.stopPropagation()">`;
                } else {
                    TH.innerHTML = `<div class="text-center fw-bold w-100">${cornerText}</div>`;
                }
            } else {
                TH.innerHTML = `<div class="text-center w-100">${row}</div>`;
            }
        },

        cells(row, col) {
            const cellProperties = {};
            if (row === 0) {
                cellProperties.renderer = function(instance, td, row, col, prop, value, cellProperties) {
                    Handsontable.renderers.TextRenderer.apply(this, arguments);
                    td.style.fontWeight = 'bold';
                    td.style.background = '#e9ecef';
                    td.style.textAlign = 'center';
                    td.style.verticalAlign = 'middle';
                };
            }
            return cellProperties;
        }
    });

    hotInstances[subItemId] = hot;
    setTimeout(() => {
        hot.render();
    }, 100);
}

function saveHandsontable(subItemId) {
    const hot = hotInstances[subItemId];
    if (!hot) return;
    const allData = hot.getData();
    const cornerInput = document.getElementById(`corner-input-${subItemId}`);
    const cornerHeaderValue = cornerInput ? cornerInput.value : "STT";
    const newHeader = allData[0];
    const newRows = allData.slice(1);
    const mergePlugin = hot.getPlugin('mergeCells');
    const mergedCellsArray = mergePlugin.mergedCellsCollection.mergedCells.map(item => ({
        row: item.row,
        col: item.col,
        rowspan: item.rowspan,
        colspan: item.colspan
    }));

    const formatData = {
        cornerHeader: cornerHeaderValue,
        header: hot.getRowHeader(),
        rows: hot.getData(),
        mergeCells: mergedCellsArray
    };

    const hiddenInput = document.getElementById(`hot-data-${subItemId}`);
    if(hiddenInput) {
        hiddenInput.value = JSON.stringify(formatData);
    }
    return formatData;
}

function submitTableData(subItemId){
    const formatData = saveHandsontable(subItemId);
    if (!formatData) return;
    fetch(`/table-subsection/${subItemId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data_table: formatData })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 200) {
            showToast(data.msg, "success");
        } else {
            showToast(data.err_msg, "danger");
        }
    })
    .catch(err => showToast(err, "danger"));
}
function initAllExistingTables() {
    const tableSections = document.querySelectorAll('.sub-section[data-type*="table" i]');
    tableSections.forEach(section => {
        const subItemId = section.dataset.id;
        if (subItemId && !hotInstances[subItemId]) {
            initHandsontable(subItemId, true);
        }
    });
}

document.addEventListener("DOMContentLoaded", function() {
    initAllExistingTables();
});