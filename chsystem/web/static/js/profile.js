function deleteKey(credential, tr) {
    $.ajax({
        url: "./passwordless/delete",
        type: 'DELETE',
        timeout: 5000,
        data: JSON.stringify({credential: credential}),
        contentType: 'application/json; charset=utf-8',
        success() {
            $(tr).remove()
        },
        error() {
            bootbox.alert(`Error deleting`)
        }
    })
}

function loadKeys() {
    $.ajax({
        url: './passwordless/credentials',
        type: 'GET',
        timeout: 5000,
        success(data) {
            let deleteButtonTemplate = '<button type="button" class="fw-bold btn btn-outline-danger"><i class="bi bi-trash"></i></button>'
            let tbody = $('#tbodyKeyList')

            data.forEach((credential) => {
                let tr = $('<tr>')[0]
                let th = $(`<th scope="row">${credential.origin}</th>`)[0]
                let tdCreation = $(`<td>${credential.creation}</td>`)[0]
                let tdLastuse = $(`<td>${credential.lastuse}</td>`)[0]

                let tdDeleteButton = $('<td>')[0]
                let deleteButton = $(deleteButtonTemplate)[0]

                $(deleteButton).click(() => {
                    bootbox.confirm({
                        message: `Are you sure you want to delete?`,
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
                                $(deleteButton).empty()
                                $(deleteButton).append($('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>'))
                                deleteKey(credential.id, tr)
                            }
                        }

                    })
                })

                tdDeleteButton.append(deleteButton)
                tr.append(th, tdCreation, tdLastuse, tdDeleteButton)
                tbody.append(tr)
            })
            $('#buttonKeyList').children()[0].remove()
        },
        error() {
            bootbox.alert("Error getting credentials")
        }
    })
}
