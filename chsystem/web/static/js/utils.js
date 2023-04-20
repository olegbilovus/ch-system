function formValidate() {
    'use strict'

    // Fetch all the forms we want to apply custom Bootstrap validation styles to
    let forms = document.querySelectorAll('.needs-validation')

    // Loop over them and prevent submission
    Array.prototype.slice.call(forms)
        .forEach(function (form) {
            form.addEventListener('submit', function (event) {
                if (!form.checkValidity()) {
                    event.preventDefault()
                    event.stopPropagation()
                }

                form.classList.add('was-validated')

            }, false)
        })
}


function pwEye(e) {
    let icon = e.currentTarget
    let pw = e.currentTarget.previousElementSibling
    if (pw.type === 'password') {
        pw.type = 'text'
        icon.classList.remove('bi-eye-slash')
        icon.classList.add('bi-eye')
    } else {
        pw.type = 'password'
        icon.classList.remove('bi-eye')
        icon.classList.add('bi-eye-slash')
    }
}

function toLower(e) {
    e.target.value = e.target.value.toLowerCase()
}

function toUpper(e) {
    e.target.value = e.target.value.toUpperCase()
}

function disableInputs(...inputs) {
    inputs.forEach((input) => {
        input.prop('disabled', true)
    })
}

function minutesToDHM(minutes, numbers) {
    let negative = false
    if (minutes < 0) {
        minutes *= -1
        negative = true
    }
    let days = Math.trunc(minutes / 1440)
    minutes %= 1440
    let hours = Math.trunc(minutes / 60)
    minutes %= 60

    if (numbers === true) {
        return {days, hours, minutes, negative}
    }

    let msg = `${days > 0 ? days + 'd ' : ''}${hours > 0 ? hours + 'h ' : ''}${minutes}m`
    if (negative) {
        msg = '-' + msg
    }
    return msg
}