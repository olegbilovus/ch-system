function createRoleSelect(roleNames, roleColors, selected) {
    let select = $('<select class="form-select">')[0]
    for (let i = 0; i < roleNames.length; i++) {
        let option = $(`<option value="${i}" style="color:${roleColors[i]}">${roleNames[i]}</option>`)[0]
        if (i === selected) {
            $(option).prop('selected', true)
        }
        select.append(option)
    }
    return select
}

function changeRoleUser(username, tdRoleSelect) {
    $.ajax({
        url: "./user-role",
        type: 'POST',
        timeout: 5000,
        data: JSON.stringify({username: username, role: $(tdRoleSelect).val()}),
        contentType: 'application/json; charset=utf-8',
        success() {
            alert(`Role changed to ${username}`)
        },
        error() {
            alert(`Error changing the role to ${username}`)
        }
    })
}

function deleteUser(username, tr) {
    $.ajax({
        url: "./users",
        type: 'DELETE',
        timeout: 5000,
        data: JSON.stringify({username: username}),
        contentType: 'application/json; charset=utf-8',
        success() {
            $(tr).remove()
        },
        error() {
            alert(`Error deleting the user ${username}`)
        }
    })
}

function loadUsers(roleNames, roleColors) {
    $.ajax({
        url: './users',
        type: 'GET',
        timeout: 5000,
        success(data) {
            let deleteButtonTemplate = '<button type="button" class="fw-bold btn btn-outline-danger"><i class="bi bi-trash"></i></button>'
            let tbody = $('#tbodyUserList')

            data.forEach((user) => {
                let tr = $('<tr>')[0]
                let th = $(`<th scope="row">${user.username}</th>`)[0]
                let tdName = $(`<td>${user.userprofile.name}</td>`)[0]
                let tdRole = $("<td>")[0]
                let tdRoleSelect = createRoleSelect(roleNames, roleColors, user.userprofile.role)
                let tdDeleteButton = $('<td>')[0]
                let deleteButton = $(deleteButtonTemplate)[0]

                $(tdRoleSelect).change(() => {
                    changeRoleUser(user.username, tdRoleSelect)
                })

                $(deleteButton).click(() => {
                    bootbox.confirm({
                        message: `Are you sure you want to delete ${user.username} ?`,
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
                                deleteUser(user.username, tr)
                            }
                        }

                    })
                })

                tdRole.append(tdRoleSelect)
                tdDeleteButton.append(deleteButton)
                tr.append(th, tdName, tdRole, tdDeleteButton)
                tbody.append(tr)
            })
            $('#buttonUserList').children()[0].remove()
        },
        error() {
            alert("Error getting users")
        }
    })
}