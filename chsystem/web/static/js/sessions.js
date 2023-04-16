function sessionDeleteConfirmed(_id, tr) {
    $.ajax({
        url: "./user-sessions",
        type: 'DELETE',
        timeout: 5000,
        data: JSON.stringify({id: _id}),
        contentType: 'application/json; charset=utf-8',
        success() {
            $(tr).remove()
        },
        error() {
            alert(`Error deleting session ${_id}`)
        }
    })
}

function loadSessions() {
    $.ajax({
        url: "./user-sessions",
        type: 'GET',
        timeout: 5000,
        success(data) {
            let deleteButtonTemplate = '<button type="button" class="fw-bold btn btn-outline-danger"><i class="bi bi-trash"></i></button>'
            let noDeleteButtonTemplate = '<button type="button" class="fw-bold btn btn-outline-secondary" disabled>Current session </button>'

            let tbody = $('#tbodySessions')
            data.sessions.forEach((session) => {
                let tr = $('<tr>')[0]
                let tdHost = $(`<td>${session.host}</td>`)[0]
                let tdCreation = $(`<td>${session.creation}</td>`)[0]
                let tdLastuse = $(`<td>${session.lastuse}</td>`)[0]
                let tdDeleteButton = $('<td>')[0]

                if (session.id === data.current) {
                    $(tr).addClass('bg-secondary table-secondary')
                    let deleteButton = $(noDeleteButtonTemplate)[0]
                    tdDeleteButton.append(deleteButton)
                } else {
                    let deleteButton = $(deleteButtonTemplate)[0]
                    $(deleteButton).click(() => {
                        bootbox.confirm({
                            message: `Are you sure you want to delete the session ${session.id} ?`,
                            buttons: {
                                confirm: {
                                    label: 'Yes',
                                    className: 'btn-danger'
                                },
                                cancel: {
                                    label: 'No',
                                    className: 'btn-secondary'
                                }
                            },
                            callback(result) {
                                if (result) {
                                    $(tdDeleteButton).empty()
                                    $(tdDeleteButton).append($('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>'))
                                    sessionDeleteConfirmed(session.id, tr)
                                }
                            }

                        })
                    })
                    tdDeleteButton.append(deleteButton)
                }

                tr.append(tdHost, tdCreation, tdLastuse, tdDeleteButton)
                tbody.append(tr)
            })
            $('#sessionsLoading').remove()
        },
        error() {
            alert("Error getting sessions data")
        }
    })
}