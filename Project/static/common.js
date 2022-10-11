function placeholder(_e){
    _e.src = "/static/pfp.jpg"
}

function openDialog(_id){
    document.getElementById(_id).showModal()
}

function closeDialog(_child){
    _child.parentElement.close()
}

function submitForm_(_id){
    document.getElementById(_id).submit()
}