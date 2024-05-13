
function add_new_board_handler(form) {
    var formData = new FormData(form);

    fetch('/add_new_board', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok.');
        }
        showNotification("Board added", true)
    })
    .catch(error => {
        showNotification("Errors occurred when adding a board", true)
        console.error('There was a problem with your fetch operation:', error);
    });

    // Prevent the default form submission
    event.preventDefault();
}