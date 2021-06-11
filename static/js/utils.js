function login(){
    user = {
        user_id: document.getElementById("user_id"),
        api_key: document.getElementById("api_key")
    }

    $.ajax({url: './login', type: 'POST', contentType: 'application/json', data: JSON.stringify(user), timeout: 10000, success: function(result){
			console.log("login: " + result)
			for (let boss of allBosses){
				document.getElementById(boss).innerHTML = getTimerMinutes(timers[boss])
			}
		}, error: function(xhr, status, error){
			displayError()
		}
	});

}