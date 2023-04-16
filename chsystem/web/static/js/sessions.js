function sessionDeleteConfirmed (_id, tr) {
  $.ajax({
    url: './user-sessions',
    type: 'DELETE',
    timeout: 5000,
    data: JSON.stringify({ id: _id }),
    contentType: 'application/json; charset=utf-8',
    success: function (data) {
      $(tr).remove()
    },
    error: function (xhr, status, error) {
      alert(`Error deleting session ${_id}`)
    }
  })
}

function loadSessions () {
  $.ajax({
    url: './user-sessions',
    type: 'GET',
    timeout: 5000,
    success: function (data) {
      const deleteButtonTemplate = '<button type="button" class="fw-bold btn btn-outline-danger"><i class="bi bi-trash"></i></button>'
      const noDeleteButtonTemplate = '<button type="button" class="fw-bold btn btn-outline-secondary" disabled>Current session </button>'

      const tbody = $('#tbodySessions')
      data.sessions.forEach((session) => {
        const tr = $('<tr>')[0]
        const tdHost = $(`<td>${session.host}</td>`)[0]
        const tdCreation = $(`<td>${session.creation}</td>`)[0]
        const tdLastuse = $(`<td>${session.lastuse}</td>`)[0]
        const tdDeleteButton = $('<td>')[0]

        if (session.id === data.current) {
          $(tr).addClass('bg-secondary table-secondary')
          const deleteButton = $(noDeleteButtonTemplate)[0]
          tdDeleteButton.append(deleteButton)
        } else {
          const deleteButton = $(deleteButtonTemplate)[0]
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
      alert('Error getting sessions data')
    }
  })
}
