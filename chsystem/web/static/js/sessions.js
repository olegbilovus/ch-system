function sessionDeleteConfirmed(_id, tr) {
    $.ajax({
        url: `./user-sessions`,
        type: 'DELETE',
        timeout: 5000,
        data: JSON.stringify({id: _id}),
        contentType: 'application/json; charset=utf-8',
        success: function (data) {
            $(tr).remove()
        },
        error: function (xhr, status, error) {
            alert(`Error deleting session ${_id}`)
        }
    })
}

function loadSessions() {
    $.ajax({
        url: `./user-sessions`,
        type: 'GET',
        timeout: 5000,
        success: function (data) {
            let iconDeleteButton = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16"><path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/><path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/></svg>'
            let deleteButtonTemplate = `<button type="button" class="fw-bold btn btn-outline-danger">${iconDeleteButton}</button>`
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
                            callback: function (result) {
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
        error: function (xhr, status, error) {
            alert(`Error getting sessions data`)
        }
    })
}