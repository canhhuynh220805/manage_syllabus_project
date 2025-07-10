
function showSection(sectionId){
    document.querySelectorAll("section").forEach(section =>{
        section.classList.remove("active");
    })
    document.getElementById(sectionId).classList.add('active');
    if(sectionId !== 'subjects')
        hideForm();
}

function showForm(){
    document.getElementById('subject-form').classList.add("active");
}

function hideForm(){
    document.getElementById('subject-form').classList.remove("active");
    document.getElementById('subject-form').reset();
}

function addSubject(){

}