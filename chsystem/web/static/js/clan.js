function getMinutesFromDHM(days, hours, minutes) {
    return (parseInt(days.val()) * 24 * 60) + (parseInt(hours.val()) * 60) + parseInt(minutes.val())
}

function addTimer() {
    let form = $('#formAddTimer')
    let respawnD = $('#respawnDays')
    let respawnH = $('#respawnHours')
    let respawnM = $('#respawnMinutes')
    let respawn = getMinutesFromDHM(respawnD, respawnH, respawnM)
    $('#respawn').val(respawn)
    disableInputs(respawnD, respawnH, respawnM)

    let windowD = $('#windowDays')
    let windowH = $('#windowHours')
    let windowM = $('#windowMinutes')
    let window = getMinutesFromDHM(windowD, windowH, windowM)
    $('#window').val(window)
    disableInputs(windowD, windowH, windowM)

    form.submit()
}

function saveTimer(bossname, respawn, window, saveButton) {
    $.ajax({
        url: "./timers",
        type: 'PATCH',
        timeout: 5000,
        data: JSON.stringify({bossname, respawn: parseInt(respawn), window: parseInt(window)}),
        contentType: 'application/json; charset=utf-8',
        success() {
            $(saveButton).empty()
            $(saveButton).append($('<i class="bi bi-save">'))
            bootbox.alert(`Saved changes to ${bossname}`)
        },
        error() {
            bootbox.alert(`Error saving changes to the timer ${bossname}`)
        }
    })
}

function deleteTimer(bossname, tr) {
    $.ajax({
        url: "./timers",
        type: 'DELETE',
        timeout: 5000,
        data: JSON.stringify({bossname}),
        contentType: 'application/json; charset=utf-8',
        success() {
            $(tr).remove()
        },
        error() {
            bootbox.alert(`Error deleting the timer ${bossname}`)
        }
    })
}

function loadTimers() {
    $.ajax({
        url: './timers',
        type: 'GET',
        timeout: 5000,
        success(data) {
            let deleteButtonTemplate = '<button type="button" class="fw-bold btn btn-outline-danger"><i class="bi bi-trash"></i></button>'
            let saveButtonTemplate = '<button type="button" class="fw-bold btn btn-outline-success"><i class="bi bi-save"></i></button>'
            let tbody = $('#tbodyTimerList')

            data.forEach((timer) => {
                let tr = $('<tr>')[0]
                let th = $(`<th scope="row">${timer.bossname}</th>`)[0]

                let tdType = $(`<td>${timer.type}</td>`)[0]

                let tdRespawn = $(`<td><input type="number" class="form-control" min="0" value="${timer.respawntimeminutes}"></td>`)[0]
                let tdWindow = $(`<td><input type="number" class="form-control" min="0" value="${timer.windowminutes}"></td>`)[0]

                let tdSaveButton = $('<td>')[0]
                let saveButton = $(saveButtonTemplate)[0]
                $(saveButton).click(() => {
                    bootbox.confirm({
                        message: `Are you sure you want to save the changes made to ${timer.bossname} ?`,
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
                                $(saveButton).empty()
                                $(saveButton).append($('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>'))
                                saveTimer(th.textContent, tdRespawn.children[0].value, tdWindow.children[0].value, saveButton)
                            }
                        }

                    })
                })

                let tdDeleteButton = $('<td>')[0]
                let deleteButton = $(deleteButtonTemplate)[0]
                $(deleteButton).click(() => {
                    bootbox.confirm({
                        message: `Are you sure you want to delete ${timer.bossname} ?`,
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
                                deleteTimer(timer.bossname, tr)
                            }
                        }

                    })
                })

                tdSaveButton.append(saveButton)
                tdDeleteButton.append(deleteButton)
                tr.append(th, tdType, tdRespawn, tdWindow, tdSaveButton, tdDeleteButton)
                tbody.append(tr)
            })
            $('#buttonTimerList').children()[0].remove()
        },
        error() {
            bootbox.alert("Error getting users")
        }
    })
}

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
        data: JSON.stringify({username, role: $(tdRoleSelect).val()}),
        contentType: 'application/json; charset=utf-8',
        success() {
            bootbox.alert(`Role changed to ${username}`)
        },
        error() {
            bootbox.alert(`Error changing the role to ${username}`)
        }
    })
}

function deleteUser(username, tr) {
    $.ajax({
        url: "./users",
        type: 'DELETE',
        timeout: 5000,
        data: JSON.stringify({username}),
        contentType: 'application/json; charset=utf-8',
        success() {
            $(tr).remove()
        },
        error() {
            bootbox.alert(`Error deleting the user ${username}`)
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
            bootbox.alert("Error getting users")
        }
    })
}