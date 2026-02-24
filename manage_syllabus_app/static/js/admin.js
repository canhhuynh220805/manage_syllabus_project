function changeUserRole(userId){
    const role = document.querySelector(
      `input[name="role_${userId}"]:checked`
    ).value;
    fetch(`/admin/user/${userId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            'role_name': role
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 200) {
            showToast(data.msg, "success");
            setTimeout(() => {
                location.reload();
            }, 300);
        } else {
            showToast(data.err_msg, "danger");
        }
    })
    .catch(err => {
        console.error(err);
        showToast("Lỗi kết nối server", "danger");
    });
}

function deleteUser(userId){
    fetch(`/admin/user/${userId}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 200) {
            showToast(data.msg, "success");
            setTimeout(() => {
                location.reload();
            }, 300);
        } else {
            showToast(data.err_msg, "danger");
        }
    })
    .catch(err => {
        console.error(err);
        showToast("Lỗi kết nối server", "danger");
    });
}


function updateSubject(subject_id){
    const name = document.getElementById('subjectName').value;
    const numberTheory = document.getElementById('numberTheory').value;
    const numberPractice = document.getElementById('numberPractice').value;
    const hourSelfStudy = document.getElementById('hourSelfStudy').value;

    fetch(`/admin/subject/${subject_id}`,{
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            'name': name,
            'numberTheory': numberTheory,
            'numberPractice': numberPractice,
            'hourSelfStudy': hourSelfStudy
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 200) {
            showToast(data.msg, "success");
            setTimeout(() => {
                location.reload();
            }, 300);
        } else {
            showToast(data.err_msg, "danger");
        }
    })
    .catch(err => {
        console.error(err);
        showToast("Lỗi kết nối server", "danger");
    });
}


function createSubject(){
    const name = document.getElementById('subjectName').value;
    const subjectId = document.getElementById('subjectCode').value;
    const numberTheory = document.getElementById('numberTheory').value;
    const numberPractice = document.getElementById('numberPractice').value;
    const hourSelfStudy = document.getElementById('hourSelfStudy').value;

    fetch('/admin/subject',{
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            'name': name,
            'subjectId': subjectId,
            'numberTheory': numberTheory,
            'numberPractice': numberPractice,
            'hourSelfStudy': hourSelfStudy
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 200) {
            showToast(data.msg, "success");
            setTimeout(() => {
                location.reload();
            }, 300);
        } else {
            showToast(data.err_msg, "danger");
        }
    })
    .catch(err => {
        console.error(err);
        showToast("Lỗi kết nối server", "danger");
    });
}

function createMajor(){
    const name = document.getElementById('majorName').value;
    const majorCode = document.getElementById('majorCode').value;
    const facBox = document.getElementById('faculty');
    const facId = facBox.value;
    fetch('/admin/major',{
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            'name': name,
            'majorCode': majorCode,
            'facultyId': facId
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 200) {
            showToast(data.msg, "success");
            setTimeout(() => {
                location.reload();
            }, 300);
        } else {
            showToast(data.err_msg, "danger");
        }
    })
    .catch(err => {
        console.error(err);
        showToast("Lỗi kết nối server", "danger");
    });
}

function updateMajor(majorId){
    const name = document.getElementById('majorName').value;
    const facBox = document.getElementById('faculty');
    const facId = facBox.value;
    fetch(`/admin/major/${majorId}`,{
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            'name': name,
            'facultyId': facId
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 200) {
            showToast(data.msg, "success");
            setTimeout(() => {
                location.reload();
            }, 300);
        } else {
            showToast(data.err_msg, "danger");
        }
    })
    .catch(err => {
        console.error(err);
        showToast("Lỗi kết nối server", "danger");
    });
}

function updateProgram(programId){
    const name = document.getElementById('programName').value;
    const academicYear = document.getElementById('academicYear').value;
    const majorBox = document.getElementById('major');
    const majorId = majorBox.value;
    const oldProgramBox = document.getElementById('program');
    const oldProgramId = oldProgramBox.value;
    const currentYear = new Date().getFullYear();

    if(academicYear < currentYear){
        showToast("Khóa mới phải lớn hơn hoặc bằng năm hiện tại", "danger");
        setTimeout(() => {
            location.reload();
        }, 300);
    }

    fetch(`admin/training-program/${programId}`,{
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            'name': name,
            'academicYear': academicYear,
            'majorId': majorId,
            'oldProgramId': oldProgramId
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 200) {
            showToast(data.msg, "success");
            setTimeout(() => {
                location.reload();
            }, 300);
        } else {
            showToast(data.err_msg, "danger");
        }
    })
    .catch(err => {
        console.error(err);
        showToast("Lỗi kết nối server", "danger");
    });
}

function createProgram(){
    const name = document.getElementById('programName').value;
    const academicYear = document.getElementById('academicYear').value;
    const majorBox = document.getElementById('major');
    const majorId = majorBox.value;
    const oldProgramBox = document.getElementById('program');
    const oldProgramId = oldProgramBox.value;
    const currentYear = new Date().getFullYear();

    if(academicYear < currentYear){
        showToast("Khóa mới phải lớn hơn hoặc bằng năm hiện tại", "danger");
        setTimeout(() => {
            location.reload();
        }, 300);
    }

    fetch('admin/training-program',{
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            'name': name,
            'academicYear': academicYear,
            'majorId': majorId,
            'oldProgramId': oldProgramId
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 200) {
            showToast(data.msg, "success");
            setTimeout(() => {
                location.reload();
            }, 300);
        } else {
            showToast(data.err_msg, "danger");
        }
    })
    .catch(err => {
        console.error(err);
        showToast("Lỗi kết nối server", "danger");
    });
}