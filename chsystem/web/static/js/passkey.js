function registerPasswordless() {
    $.ajax({
        url: "./passwordless/register",
        type: 'GET',
        timeout: 5000,
        async success(data) {
            let p = new Passwordless.Client({
                apiKey: data.publicKey
            });
            try {
                await p.register(data.token, '')
            } catch (e) {
                bootbox.alert("Key already in use")
            }
            bootbox.alert("Key added")
        },
        error() {
            bootbox.alert("Error init")
        }
    })
}

function signinPasswordless() {
    $.ajax({
        url: "./passwordless/pbk",
        type: 'GET',
        timeout: 5000,
        async success(data) {
            let p = new Passwordless.Client({
                apiKey: data.publicKey
            });
            try {
                const {token, error} = await p.signinWithDiscoverable()
                if (!error) {
                    $('#verificationToken').val(token)
                    $('#loginForm').submit()
                } else {
                    bootbox.alert("Error")
                }
            } catch (e) {
                bootbox.alert("Error")
            }
        },
        error() {
            bootbox.alert("Error init")
        }
    })
}
