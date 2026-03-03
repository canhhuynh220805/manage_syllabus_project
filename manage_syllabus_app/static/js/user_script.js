

function updateSection(subsection_id){
    let content = document.getElementById(`content-${subsection_id}`)
    fetch(`/text-subsection/${subsection_id}`,{
         method: 'PATCH',
        headers: {
        'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'content': content.value,
        })
    }).then(res => res.json()).then(data =>{
        if(data.status == 200){
            showToast(data.msg, 'success')
        }else
            showToast(data.err_msg, 'danger')
    }).catch(err => {
        console.error('Lỗi:', err);
        showToast('Mất kết nối đến máy chủ!', 'danger');
    });
}

function updateCourseObjective(co_id){
    let content = document.getElementById(`content-co${co_id}`);
    fetch(`/course-objective/${co_id}`,{
         method: 'PATCH',
        headers: {
        'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'content': content.value,
        })
    }).then(res => res.json()).then(data =>{
        if(data.status == 200){
            showToast(data.msg, 'success')
        }else
            showToast(data.err_msg, 'danger')
    }).catch(err => {
        console.error('Lỗi:', err);
        showToast('Mất kết nối đến máy chủ!', 'danger');
    });
}

function updateCourseLearningOutcome(clo_id){
    let content = document.getElementById(`content-clo${clo_id}`)
    fetch(`/course-learning-outcome/${clo_id}`,{
         method: 'PATCH',
        headers: {
        'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'content': content.value,
        })
    }).then(res => res.json()).then(data =>{
        if(data.status == 200){
            showToast(data.msg, 'success')
        }else
            showToast(data.err_msg, 'danger')
    }).catch(err => {
        console.error('Lỗi:', err);
        showToast('Mất kết nối đến máy chủ!', 'danger');
    });
}

function clearInputLearningMaterial(){
    const content = document.getElementById('learning-material-name');
    content.value = "";
}

function removeLearningMaterial(syllabus_id, material_id){
    fetch(`/syllabus/${syllabus_id}/learning-material/${material_id}`,{
        method: 'DELETE',
        headers: {
        'Content-Type': 'application/json'
        },
    }).then(res => res.json()).then(data =>{
        if(data.status == 200){
            showToast(data.msg, 'success')
            location.reload();
        }else
            showToast(data.err_msg, 'danger')
    }).catch(err => {
        console.error('Lỗi:', err);
        showToast('Mất kết nối đến máy chủ!', 'danger');
    });
}

function addLearningMaterial(syllabus_id){
    const content = document.getElementById('learning-material-name').value;
    const type =  document.getElementById('new-type-learning-material').value;
    if(!content){
        showToast("Vui lòng nhập tên tài liệu!!", "danger")
        return;
    }

    fetch(`/syllabus/${syllabus_id}/learning-material`,{
        method: 'POST',
        headers: {
        'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'name': content,
            'type_id': type
        })
    }).then(res => res.json()).then(data =>{
        if(data.status == 200){
            showToast(data.msg, 'success')
            location.reload();
        }else
            showToast(data.err_msg, 'danger')
    }).catch(err => {
        console.error('Lỗi:', err);
        showToast('Mất kết nối đến máy chủ!', 'danger');
    });
}

function updateLearningMaterial(material_id){
    let content = document.getElementById(`name-learning-material${material_id}`)

    fetch(`/learning-material/${material_id}`,{
        method: 'PATCH',
        headers: {
        'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'name': content.value,
        })
    }).then(res => res.json()).then(data =>{
        if(data.status == 200){
            showToast(data.msg, 'success')
        }else
            showToast(data.err_msg, 'danger')
    }).catch(err => {
        console.error('Lỗi:', err);
        showToast('Mất kết nối đến máy chủ!', 'danger');
    });
}

function loadOptions(btn, subsection_id, attribute_group_id){
    const menu = document.getElementById(`dropdown-menu-${subsection_id}`);
    if (menu.getAttribute('data-loaded') === 'true') return;
    const url = `/attribute-group/${attribute_group_id}?subsection_id=${subsection_id}`;
    fetch(url,{
        method: 'GET',
        headers: {
        'Content-Type': 'application/json'
        },
    }).then(res => res.json()).then(data => {
        if(data.status == 200){
            menu.innerHTML = '';
            const listItems = data.results;
            if (!listItems || listItems.length === 0) {
                menu.innerHTML = '<li><span class="dropdown-item text-muted">Không có dữ liệu</span></li>';
                return;
            }

            listItems.forEach(item => {
                const li = document.createElement('li');
                li.innerHTML = `
                    <a class="dropdown-item" href="javascript:void(0)"
                       onclick="selectItem('${subsection_id}', '${item.id}', '${item.name_value}')">
                       ${item.name_value}
                    </a>
                `;
                menu.appendChild(li);
            })
        }else{
            showToast(data.err_msg, 'danger')
        }
    }).catch(err => {
        console.error('Lỗi:', err);
        showToast('Mất kết nối đến máy chủ!', 'danger');
    });
}

function selectSubject(subsectionId, subjectId, subjectName) {
    document.getElementById(`new-subject-${subsectionId}`).value = subjectId;
    const displaySpan = document.getElementById(`display-subject-${subsectionId}`);
    displaySpan.innerText = subjectName;
    displaySpan.classList.remove('text-muted');
    displaySpan.classList.add('text-dark', 'fw-bold');
}

function selectType(subsectionId, typeId, typeName) {
    document.getElementById(`new-type-${subsectionId}`).value = typeId;
    const displaySpan = document.getElementById(`display-type-${subsectionId}`);
    displaySpan.innerText = typeName;
}

function selectItem(subsection_id, item_id, item_value){
    fetch('/subsection/attribute',{
        method: 'POST',
        headers: {
        'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'subsection_id': subsection_id,
            'attribute_id': item_id,
        })
    }).then(res => res.json()).then(data => {
        if(data.status == 200){
            const container = document.getElementById(`display-list-${subsection_id}`);
            const badge = document.createElement('span');
            badge.className = "badge bg-success text-white border p-2 me-1 mb-1 fs-6";
            badge.setAttribute('data-id', item_id);
            badge.innerHTML = `
                ${item_value}
                <a href="javascript:void(0)" onclick="removeSelection(this, '${subsection_id}', '${item_id}')" class="text-white ms-1 text-decoration-none">&times;</a>
            `;
            container.appendChild(badge);
            showToast(data.msg, 'success')
        }else
            showToast(data.err_msg, 'danger')
    })
}

function removeSelection(element, subsection_id, attribute_id){
    fetch('/subsection/attribute',{
        method: 'DELETE',
        headers: {
        'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'subsection_id': subsection_id,
            'attribute_id': attribute_id,
        })
    }).then(res => res.json()).then(data => {
        if(data.status == 200){
            element.parentElement.remove();
            showToast(data.msg, 'success')
        }else
            showToast(data.err_msg, 'danger')
    })
}

function saveCredits(credit_id) {
    const theory = document.getElementById(`theory-${credit_id}`).value;
    const practice = document.getElementById(`practice-${credit_id}`).value;
    const selfStudy = document.getElementById(`self-study-${credit_id}`).value;

    fetch('/syllabus/update-credits', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            'credit_id': credit_id,
            'theory': parseInt(theory) || 0,
            'practice': parseInt(practice) || 0,
            'self_study': parseInt(selfStudy) || 0
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 200) {
            showToast(data.msg, "success")
            document.getElementById(`total-credits-${credit_id}`).value = data.total;
        } else {
            showToast(data.err_msg, "danger");
        }
    })
    .catch(err => {
        showToast("Lỗi kết nối server" + err, "danger");
    });
}

function addRequirementSubject(subsection_id, syllabus_id){
    const subjectInput = document.getElementById(`new-subject-${subsection_id}`);
    const subjectId = subjectInput.value;
    const typeId = document.getElementById(`new-type-${subsection_id}`).value;
    fetch(`/syllabus/${syllabus_id}/requirement-subject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            'subject_id': subjectId,
            'type_id': typeId
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 200) {
            showToast(data.msg, "success");
            const tbody = document.getElementById(`req-table-body-${subsection_id}`);
            const noDataRow = document.getElementById(`empty-row-${subsection_id}`);
            if (noDataRow) noDataRow.remove();

            const newIndex = tbody.rows.length + 1;

            const newRowHtml = `
                <tr id="req-row-${subjectId}" class="align-middle animate__animated animate__fadeIn">
                    <td class="text-center text-muted row-index">${newIndex}</td>
                    <td class="fw-medium text-dark">${data.subject.name} / ${data.type.name}</td>
                    <td class="fw-medium text-dark">${subjectId}</td>
                    <td class="text-center">
                        <button class="btn btn-link text-danger p-0"
                            onclick="removeReqRow(this, '${syllabus_id}', '${subjectId}', '${subsection_id}')">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </td>
                </tr>
            `;
            tbody.insertAdjacentHTML('beforeend', newRowHtml);
            const itemToRemove = document.getElementById(`item-subject-${subsection_id}-${subjectId}`);
            if (itemToRemove) {
                itemToRemove.remove();
            }
            const displaySpan = document.getElementById(`display-subject-${subsection_id}`);
            displaySpan.innerText = "-- Chọn môn học --";
            displaySpan.classList.add('text-muted');
            displaySpan.classList.remove('text-dark', 'fw-bold');
            subjectInput.value = "";

            const listContainer = document.getElementById(`list-subject-${subsection_id}`);
            const remainingItems = listContainer.querySelectorAll('li');
            if (remainingItems.length === 0) {
                listContainer.innerHTML = `<li class="text-center text-muted small py-2">Đã thêm hết các môn</li>`;
            }

        } else {
            showToast(data.err_msg, "danger");
        }
    })
    .catch(err => {
        console.error(err);
        showToast("Lỗi kết nối server", "danger");
    });
}

function removeReqRow(btn, syllabus_id, req_subject_id, subsection_id){
    showConfirmDialog(
        "Xác nhận xóa",
        "Bạn có chắc muốn xóa môn học này?",
        function(){
            fetch(`/syllabus/${syllabus_id}/requirement-subject/${req_subject_id}`,{
                method: "DELETE",
                headers: { 'Content-Type': 'application/json' }
            }).then(res => res.json()).then(data =>{
                if (data.status === 200) {
                    showToast(data.msg, "success");
                    const row = document.getElementById(`req-row-${req_subject_id}`);
                    const rawText = row.cells[1].innerText;
                    const subjectName = rawText.split('/')[0].trim();
                    row.remove();
                    const listContainer = document.getElementById(`list-subject-${subsection_id}`);

                    if (listContainer) {
                        const emptyMessage = listContainer.querySelector('li.text-center');
                        if (emptyMessage) {
                            emptyMessage.remove();
                        }
                        const li = document.createElement("li");
                        li.id = `item-subject-${subsection_id}-${req_subject_id}`;
                        li.innerHTML = `
                            <a class="dropdown-item rounded-2 small py-2 subject-item"
                               href="javascript:void(0)"
                               onclick="selectSubject('${subsection_id}', '${req_subject_id}', '${subjectName}')">
                                <span class="fw-bold">${req_subject_id}</span> - ${subjectName}
                            </a>
                        `;
                        listContainer.appendChild(li);
                    }
                } else {
                    showToast(data.err_msg, "danger");
                }
            })
        }
    )
}

function selectPLO(plo_id, co_id){
    const list = document.getElementById(`list-plo-co${co_id}`)
    fetch(`/course-objective/${co_id}/plo`,{
        method: 'POST',
        headers: {
        'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'plo_id': plo_id,
        })
    }).then(res => res.json()).then(data =>{
        if(data.status == 200){
            showToast(data.msg, 'success')
            setTimeout(() => {
                location.reload();
            }, 300);
        }else
            showToast(data.err_msg, 'danger')
    }).catch(err => {
        showToast("Lỗi kết nối server" + err, "danger");
    });
}

function deletePLO(co_id, plo_id){
     const list = document.getElementById(`list-plo-co${co_id}`);
     fetch(`/course-objective/${co_id}/delete-plo/${plo_id}`,{
        method: 'DELETE',
        headers: {
        'Content-Type': 'application/json'
        },
     }).then(res => res.json()).then(data =>{
        if(data.status == 200){
            showToast(data.msg, 'success')
            setTimeout(() => {
                location.reload();
            }, 300);
        }else
            showToast(data.err_msg, 'danger')
     }).catch(err => {
        showToast("Lỗi kết nối server" + err, "danger");
    });
}

function selectPloItem(plo_id){
    const listPlos = document.getElementById('list-plos');
    const placeholder = document.getElementById('plo-placeholder');
    if(placeholder)
        placeholder.remove();

    const badgeId = `select-plo-${plo_id}`;
    if (document.getElementById(badgeId)) {
        showToast("PLO này đã được chọn!", "danger");
        return;
    }

    const span = document.createElement('span')
    span.className = 'badge rounded-pill bg-success bg-opacity-10 text-success border border-success px-3 py-2 d-flex align-items-center';
    span.id = `select-plo-${plo_id}`
    span.innerHTML = `
        PLO.${plo_id}
        <a class="dropdown-item" href="javascript:void(0)" onclick="removeSelectPloItem(${plo_id})"><i class="fas fa-times ms-2 cursor-pointer"></i></a>
    `
    listPlos.appendChild(span);
}

function removeSelectPloItem(plo_id){
    const badgeId = `select-plo-${plo_id}`;
    badge = document.getElementById(badgeId);
    badge.remove();
    const listPlos = document.getElementById('list-plos');
    if (listPlos.children.length === 0) {
             listPlos.innerHTML = '<span id="plo-placeholder" class="text-muted small fst-italic align-self-center ms-2">Chưa chọn PLO nào</span>';
    }
}

function clearInputCourseObjective(){
    location.reload();
}

function addCourseObjective(subject_id){
    const content = document.getElementById('description-co').value;
    if(!content){
        showToast("Thiếu mô tả mục tiêu môn học", "danger")
        return
    }
    const ploIds = []
    const badges = document.querySelectorAll('span[id^="select-plo-"]');
    if(badges.length === 0){
        showToast("Chưa có PLO nào được chọn", "danger")
        return
    }
    for(const badge of badges){
        const id = parseInt(badge.id.replace('select-plo-', ''));
        ploIds.push(id);
    }
    fetch(`/subject/${subject_id}/course-objective`,{
        method: 'POST',
        headers: {
        'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'content': content,
            'plo_ids': ploIds
        })
    }).then(res =>res.json()).then(data =>{
        if (data.status === 200) {
            showToast(data.msg, "success");
            location.reload();
        } else {
            showToast(data.err_msg, "danger");
        }
    }).catch(err => {
        console.error(err);
        showToast("Lỗi kết nối server", "danger");
    });
}

function deleteCourseObjective(subject_id, co_id){
showConfirmDialog(
    "Xác nhận xóa",
    "Bạn có chắc muốn xóa mục tiêu môn học này",
    function(){
        fetch(`/subject/${subject_id}/course-objective/${co_id}`,{
            method: 'DELETE',
            headers: {
            'Content-Type': 'application/json'
            },
        }).then(res =>res.json()).then(data =>{
            if (data.status === 200) {
                showToast(data.msg, "success");
                location.reload();
            } else {
                showToast(data.err_msg, "danger");
            }
        }).catch(err => {
            console.error(err);
            showToast("Lỗi kết nối server", "danger");
        });
    }
)
}

function clearAddCLO(co_id){
    const content = document.getElementById(`co-${co_id}-clo-content`);
    content.value = "";
}

function addCLO(co_id){
    const content = document.getElementById(`co-${co_id}-clo-content`).value;

    fetch(`/course-objective/${co_id}/clo`,{
        method: 'POST',
        headers: {
        'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'content': content,
        })
    }).then(res =>res.json()).then(data =>{
        if (data.status === 200) {
            showToast(data.msg, "success");
            location.reload();
        } else {
            showToast(data.err_msg, "danger");
        }
    }).catch(err => {
        console.error(err);
        showToast("Lỗi kết nối server", "danger");
    });
}

function removeCLO(co_id, clo_id){
showConfirmDialog(
    "Xác nhận xóa",
    "Bạn có chắc chắn muốn xóa CĐR môn học này?",
    function(){
        fetch(`/course-objective/${co_id}/clo/${clo_id}`,{
            method: 'DELETE',
            headers: {
            'Content-Type': 'application/json'
            },
        }).then(res =>res.json()).then(data =>{
            if (data.status === 200) {
                showToast(data.msg, "success");
                location.reload();
            } else {
                showToast(data.err_msg, "danger");
            }
        }).catch(err => {
            console.error(err);
            showToast("Lỗi kết nối server", "danger");
        });
    }
)
}

function updateRating(clo_id, plo_id){
    const rating = document.getElementById(`rating-${clo_id}-${plo_id}`).value;
    if(rating <= 0){
        showToast("Điểm đánh giá phải lớn hơn 0!!", "danger")
        rating = 0
        return;
    }
    fetch(`/clo/${clo_id}/plo/${plo_id}`,{
        method: 'PUT',
        headers: {
        'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            'rating': rating,
        })
    }).then(res =>res.json()).then(data =>{
        if (data.status === 200) {
            showToast(data.msg, "success");
        } else {
            showToast(data.err_msg, "danger");
        }
    }).catch(err => {
        console.error(err);
        showToast("Lỗi kết nối server", "danger");
    });
}

function addAssessment(typeAssessId, syllabusId){
    const container = document.getElementById(`assessment-container-${typeAssessId}`);
    const emptyMsg = document.getElementById(`empty-msg-${typeAssessId}`);
    const tempId = Date.now();
    const newAssessmentHTML = `
        <div class="border rounded p-3 bg-light bg-opacity-50 assessment-item mt-3" id="assessment-${tempId}" data-type-id="${typeAssessId}">
            <div class="d-flex justify-content-between align-items-center mb-3 border-bottom pb-2">
                <h6 class="fw-bold mb-0 text-dark">Bài đánh giá</h6>
                <div class="d-flex gap-2 align-items-center">
                    <div class="d-flex gap-2 align-items-center">
                        <span class="badge bg-success bg-opacity-10 text-success border border-success px-2 py-1">
                            Tổng trọng số: 0%
                        </span>
                        <button class="btn btn-sm btn-outline-danger border-0" onclick="this.closest('.assessment-item').remove()">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>

            <table class="table table-sm table-bordered table-hover mb-2 bg-white">
                <thead class="table-light text-secondary">
                    <tr>
                        <th class="text-center align-middle">Phương pháp</th>
                        <th style="width: 20%;" class="text-center align-middle">Thời gian</th>
                        <th class="text-center align-middle">CĐR  môn học/CLOS</th>
                        <th style="width: 20%;" class="text-center align-middle">Trọng số (%)</th>
                        <th class="text-center align-middle" style="width: 80px;">Thao tác</th>
                    </tr>
                </thead>
                <tbody id="method-tbody-${tempId}">
                    <tr>
                        <td colspan="5" class="text-center text-muted small py-2">Vui lòng thêm phương pháp</td>
                    </tr>
                </tbody>
            </table>

            <button class="btn btn-sm btn-outline-secondary" onclick="addMethod('${tempId}', '${typeAssessId}', '${syllabusId}')">
                <i class="fas fa-plus me-1"></i> Thêm phương pháp
            </button>
        </div>
    `;

    if (emptyMsg) emptyMsg.classList.add('d-none');
    container.insertAdjacentHTML('beforeend', newAssessmentHTML);
}

function deleteAssessment(assessmentId){
    showConfirmDialog(
    "Xác nhận xóa",
    "Bạn có chắc muốn xóa bài đánh giá này, các phương pháp sẽ bị xóa theo?",
    function(){
        fetch(`/assessment/${assessmentId}/`,{
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
        }).then(res =>res.json()).then(data =>{
            if (data.status === 200) {
                showToast(data.msg, "success");
                setTimeout(() => {
                    location.reload();
                }, 1000);
            } else {
                showToast(data.err_msg, "danger");
            }
        }).catch(err => {
            console.error(err);
            showToast("Lỗi kết nối server", "danger");
        });
    }
    )
}

function addMethod(assessmentId, typeAssessId, syllabusId) {
    const tbody = document.getElementById(`method-tbody-${assessmentId}`);
    const tempMethodId = 'method_' + Date.now();

    const emptyRow = tbody.querySelector('td[colspan="5"]');
    if (emptyRow) {
        emptyRow.closest('tr').remove();
    }

    const cloDropdownItems = availableCLOs.map(clo => `
        <li id="li-method-${tempMethodId}-clo-${clo.id}">
            <a class="dropdown-item" href="javascript:void(0)"
               onclick="selectCLO('${tempMethodId}', '${clo.id}', '${clo.name}')">
               ${clo.name}
            </a>
        </li>
    `).join('');

    const newRowHTML = `
        <tr class="method-item" id="method-row-${tempMethodId}">
            <td>
                <input type="text" class="form-control form-control-sm method-name" placeholder="VD: kiểm tra máy">
            </td>
            <td>
                <input type="text" class="form-control form-control-sm method-time" placeholder="VD: 60 phút, 2 tuần...">
            </td>
            <td class="ms-auto align-middle">
                <div class="d-flex flex-wrap gap-2 mb-2" id="list-clo-${tempMethodId}"></div>
                <div class="dropdown">
                    <button type="button" class="btn btn-link text-primary text-decoration-none p-0 small dropdown-toggle" data-bs-toggle="dropdown">
                        <i class="fas fa-plus me-1"></i>CLO
                    </button>
                    <ul class="dropdown-menu shadow-sm">
                        ${cloDropdownItems}
                    </ul>
                </div>
            </td>
            <td>
                <div class="input-group input-group-sm">
                    <input type="number" class="form-control method-weight" placeholder="0" min="0" max="100">
                    <span class="input-group-text">%</span>
                </div>
            </td>
            <td class="text-center align-middle" style="width: 100px;">
                <div class="d-flex justify-content-center align-items-center gap-2">
                    <button type="button" class="btn btn-sm btn-outline-primary py-0 px-2 fw-medium" onclick="saveMethod(this, 'null','${assessmentId}', '${typeAssessId}', '${syllabusId}')">
                        Lưu
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-danger py-0 px-2 fw-medium" onclick="deleteMethodRecord(this, 'null')">
                        Xóa
                    </button>
                </div>
            </td>
        </tr>
    `;

    tbody.insertAdjacentHTML('beforeend', newRowHTML);
}

function saveMethod(btnElement, methodId, assessmentId, typeAssessId, syllabusId) {
    const tr = btnElement.closest('tr');

    const methodName = tr.querySelector('.method-name').value.trim();
    const methodTime = tr.querySelector('.method-time').value.trim();
    const methodWeight = tr.querySelector('.method-weight').value;

    const cloInputs = tr.querySelectorAll('.method-clo-input');
    const cloIds = Array.from(cloInputs).map(input => input.value);

    if (!methodName || !methodWeight || !methodTime || cloIds.length == 0) {
        showToast('Vui lòng nhập đầy đủ thông tin', "danger");
        return;
    }

    const payload = {
        syllabusId: syllabusId,
        assessmentId: assessmentId,
        typeAssessId: typeAssessId,
        methodId: methodId,
        methodName: methodName,
        methodTime: methodTime,
        weight: parseInt(methodWeight),
        cloIds: cloIds
    };

    fetch(`/syllabus/${syllabusId}/assessment/`,{
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    }).then(res =>res.json()).then(data =>{
        if (data.status === 200) {
            showToast(data.msg, "success");
            setTimeout(() => {
                location.reload();
            }, 300);
        } else {
            showToast(data.err_msg, "danger");
        }
    }).catch(err => {
        console.error(err);
        showToast("Lỗi kết nối server", "danger");
    });

}

function deleteMethodRecord(btnElement, methodId) {
    const tr = btnElement.closest('tr');
    if (!methodId || methodId === 'null') {
        tr.remove();
        return;
    }

    fetch(`/methods/${methodId}`,{
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
    }).then(res =>res.json()).then(data =>{
        if (data.status === 200) {
            showToast(data.msg, "success");
            location.reload()
        } else {
            showToast(data.err_msg, "danger");
        }
    }).catch(err => {
        console.error(err);
        showToast("Lỗi kết nối server", "danger");
    });
}

function selectCLO(methodId, cloId, cloName) {
    const listContainer = document.getElementById(`list-clo-${methodId}`);

    if (listContainer.querySelector(`#badge-${methodId}-clo-${cloId}`)) {
        return;
    }

    const badgeHTML = `
        <span class="badge rounded-pill bg-success bg-opacity-10 text-success border border-success px-3 py-2 d-flex align-items-center"
              id="badge-${methodId}-clo-${cloId}">
            ${cloName}
            <a href="javascript:void(0)" class="ms-2 text-success text-decoration-none fw-bold"
               onclick="deleteCLO('${methodId}', '${cloId}')">
                &times;
            </a>

            <input type="hidden" class="method-clo-input" value="${cloId}">
        </span>
    `;

    listContainer.insertAdjacentHTML('beforeend', badgeHTML);
}

function deleteCLO(methodId, cloId) {
    const badge = document.getElementById(`badge-${methodId}-clo-${cloId}`);
    if (badge) {
        badge.remove();
    }
}


$(document).ready(function () {
    $('#new-type-learning-material').select2({
        theme: 'bootstrap-5',
        width: '100%'
    });
    $('.select2-lecturer').select2({
        theme: 'bootstrap-5',
        width: '100%'
    });
    $('.select2-lecturer').on('change', function() {
        const syllabusId = $(this).data('syllabus-id');
        const lecturerId = $(this).val();
        assignLecturer(syllabusId, lecturerId);
    });
});


function deleteSession(btn, sessionId){

}

function saveSession(btn, sessionId){

}

function addNewSessionCard(groupId){

}


function addTag(btnElement) {
    const container = btnElement.closest('.custom-tag-group');
    const selectedArea = container.querySelector('.selected-tags');
    const hiddenSelect = container.querySelector('.hidden-select');

    const value = btnElement.getAttribute('data-value');
    const text = btnElement.innerText.replace(/^\+?\s*/, '').trim();
    const color = container.getAttribute('data-color') || 'primary';
    const badge = document.createElement('span');
    badge.className = `badge bg-${color} bg-opacity-10 text-${color} border border-${color} d-inline-flex align-items-center px-2 py-1 fw-normal tag-item text-wrap text-start lh-base`;        badge.setAttribute('data-value', value);
    badge.innerHTML = `${text} <i class="fas fa-times ms-2 cursor-pointer remove-tag" onclick="removeTag(this)"></i>`;
    selectedArea.appendChild(badge);

    const option = document.createElement('option');
    option.value = value;
    option.text = text;
    option.selected = true;
    hiddenSelect.appendChild(option);

    btnElement.remove();
}


function removeTag(iconElement) {
    const badge = iconElement.closest('.tag-item');
    const container = badge.closest('.custom-tag-group');
    const availableArea = container.querySelector('.available-tags');
    const hiddenSelect = container.querySelector('.hidden-select');

    const value = badge.getAttribute('data-value');
    const text = badge.childNodes[0].nodeValue.trim();

    const btn = document.createElement('button');
    btn.type = "button";
    btn.className = "btn btn-sm btn-outline-secondary px-2 py-1 fw-normal add-tag";
    btn.setAttribute('data-value', value);
    btn.setAttribute('onclick', 'addTag(this)');
    btn.innerText = `+ ${text}`;
    availableArea.appendChild(btn);

    const option = hiddenSelect.querySelector(`option[value="${value}"]`);
    if (option) {
        option.remove();
    }

    badge.remove();
}
