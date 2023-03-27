function minutesToDHM(minutes) {
    let negative = false
    if (minutes < 0) {
        minutes *= -1
        negative = true
    }
    let days = Math.trunc(minutes / 1440)
    minutes %= 1440
    let hours = Math.trunc(minutes / 60)
    minutes %= 60
    let msg = `${days > 0 ? days + 'd ' : ''}${hours > 0 ? hours + 'h ' : ''}${minutes}m`
    if (!negative) {
        return msg
    }
    return '-' + msg
}

function setTdTimerBK(tdTimer, remainingMins) {
    $(tdTimer).removeClass()
    if (remainingMins >= 15) {
        $(tdTimer).addClass('table-success')
    } else if (remainingMins >= 7) {
        $(tdTimer).addClass('table-warning')
    } else if (remainingMins >= -15) {
        $(tdTimer).addClass('table-danger')
    }

}

function timerResetConfirmed(bossname, tdTimer) {
    $.ajax({
        url: `./timer/reset/${bossname}`,
        type: 'PATCH',
        timeout: 5000,
        success: function (data) {
            let minsNow = Math.trunc(new Date().getTime() / 1000 / 60)
            let remainingMins = data.timer - minsNow
            $(tdTimer).empty()
            $(tdTimer).text(minutesToDHM(remainingMins))
            setTdTimerBK(tdTimer, remainingMins)
        },
        error: function (xhr, status, error) {
            alert(`Error resetting ${bossname}`)
        }
    })
}

function loadTimers(_type) {
    $.ajax({
        url: `./timers/${_type}`,
        type: 'GET',
        timeout: 5000,
        success: function (data) {
            let resetButtonTemplate = '<button type="button" class="fw-bold btn btn-outline-danger">↻</button>'

            let tbody = $(`#tbody${_type}`)
            let minsNow = Math.trunc(new Date().getTime() / 1000 / 60)
            data.forEach((timer) => {
                let tr = $('<tr>')[0]
                let th = $(`<th scope="row">${timer.bossname}</th>`)[0]
                let remainingMins = timer.timer - minsNow
                let tdTimer = $(`<td>${timer.timer == null ? 'No Data' : minutesToDHM(remainingMins)}</td>`)[0]
                let tdResetButton = $('<td>')[0]
                let resetButton = $(resetButtonTemplate)[0]

                $(resetButton).click(() => {
                    bootbox.confirm({
                        message: `Are you sure you want to reset ${timer.bossname} ?`,
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
                                $(tdTimer).empty()
                                $(tdTimer).append($('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>'))
                                timerResetConfirmed(timer.bossname, tdTimer)
                            }
                        }

                    })
                })

                if (timer.timer != null) {
                    setTdTimerBK(tdTimer, remainingMins)
                }

                tdResetButton.append(resetButton)
                tr.append(th, tdTimer, tdResetButton)
                tbody.append(tr)
            })
            $(`#button${_type}`).children()[0].remove()
        },
        error: function (xhr, status, error) {
            alert(`Error getting ${_type} timers data`)
        }
    })
}

function loadTimersType() {
    $.ajax({
        url: './timers-type',
        type: 'GET',
        timeout: 5000,
        success: function (data) {
            let accordionBodyTemplate = '<div class="accordion-body row mx-auto table-responsive">'
            let tableTemplate = '<table class="table table-hover">'
            let tableThreadTemplate = '<thead><tr><th scope="col">Name</th><th scope="col">Timer</th><th scope="col">Reset</th></tr></thead>'

            let timersCard = $('#timersCard')[0]
            data.forEach((_type) => {
                let accordionItem = $(`<div class="accordion-item" id="accordion${_type}">`)[0]
                let accordionHeader = $(`<h2 class="accordion-header" id="heading${_type}">`)[0]
                $(accordionHeader).click(() => {
                    $(`#tbody${_type}`).empty()
                    let button = $(`#button${_type}`)
                    if (!$(button).hasClass('collapsed')) {
                        button.prepend('<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>')
                        loadTimers(_type)
                    }
                })

                let collapseType = `collapse${_type}`
                let accordionButton = $(`<button id="button${_type}" class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#${collapseType}" aria-expanded="false" aria-controls="${collapseType}">`)[0]
                accordionButton.append(_type)
                accordionHeader.append(accordionButton)
                accordionItem.append(accordionHeader)

                let accordionCollapse = $(`<div id="collapse${_type}" class="accordion-collapse collapse" aria-labelledby="heading${_type}" data-bs-parent="#timersCard">`)[0]
                let accordionBody = $(accordionBodyTemplate)[0]
                let table = $(tableTemplate)[0]
                let thread = $(tableThreadTemplate)[0]
                let tbody = $(`<tbody id="tbody${_type}">`)[0]
                table.append(thread)
                table.append(tbody)
                accordionBody.append(table)
                accordionCollapse.append(accordionBody)
                accordionItem.append(accordionCollapse)

                timersCard.append(accordionItem)
            })
            $('#timersCardLoading').remove()
        },
        error: function (xhr, status, error) {
            alert('Error getting timers type data')
        }
    })
}