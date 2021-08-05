const BOSSES = {
  110: 30,
  115: 35,
  120: 40,
  125: 45,
  130: 50,
  140: 55,
  155: 60,
  160: 65,
  165: 70,
  170: 80,
  180: 90,
  185: 75,
  190: 85,
  195: 95,
  200: 105,
  205: 115,
  210: 125,
  215: 135,
  aggy: 1894,
  mord: 2160,
  hrung: 2160,
  necro: 2160,
  prot: 1190,
  gele: 2880,
  bt: 4320,
  dino: 4320
}

function createUser () {
  const user = {
    user_id: document.getElementById('user_id_create').value,
    role: parseInt(document.getElementById('role').value),
    main: document.getElementById('main').value
  }
  $.ajax({
    url: './user/create',
    type: 'POST',
    data: JSON.stringify(user),
    contentType: 'application/json; charset=utf-8',
    timeout: 5000,
    success: function (apiKey) {
      const viewer = document.getElementById('apikey_value')
      viewer.classList.remove('d-none')
      viewer.classList.add('d-block')
      viewer.innerHTML = apiKey.split('"')[1]
    },
    error: function (xhr, status, error) {
      alert('Error')
    }
  })
}

function deleteUser (_user_id) {
  $.ajax({
    url: './user/delete',
    type: 'POST',
    data: JSON.stringify({ user_id: _user_id }),
    contentType: 'application/json; charset=utf-8',
    timeout: 5000,
    success: function (apiKey) {
      document.getElementById('userD' + _user_id).remove()
      alert('Deleted')
    },
    error: function (xhr, status, error) {
      alert('Error')
    }
  })
}

function boss_sub (_boss) {
  $.ajax({
    url: './boss/sub',
    type: 'POST',
    data: JSON.stringify({ boss: _boss }),
    contentType: 'application/json; charset=utf-8',
    timeout: 5000,
    success: function (apiKey) {
      alert('Subed to ' + _boss)
    },
    error: function (xhr, status, error) {
      alert('Error')
    }
  })
}

function boss_unsub (_boss) {
  $.ajax({
    url: './boss/unsub',
    type: 'POST',
    data: JSON.stringify({ boss: _boss }),
    contentType: 'application/json; charset=utf-8',
    timeout: 5000,
    success: function (apiKey) {
      alert('Unsubed from ' + _boss)
    },
    error: function (xhr, status, error) {
      alert('Error')
    }
  })
}

function boss_reset (_boss, _timer) {
  $.ajax({
    url: './boss/set',
    type: 'POST',
    data: JSON.stringify({ boss: _boss, timer: BOSSES[_boss].toString() }),
    contentType: 'application/json; charset=utf-8',
    timeout: 5000,
    success: function (apiKey) {
      alert(_boss + ' reset')
    },
    error: function (xhr, status, error) {
      alert('Error')
    }
  })
}
