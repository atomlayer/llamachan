


function formatDateTime(dateTimeString) {
    const dateTime = new Date(dateTimeString);
    const formattedDate = dateTime.toLocaleDateString();
    const formattedTime = dateTime.toLocaleTimeString();
    return `${formattedDate} ${formattedTime}`;
}

function generate_more_threads() {
//
//    $("#loading-indicator").show();

    $.ajax({
        type: "POST",
        url: "/generate_more_threads",
        data: JSON.stringify({
            board_name: board_name,
        }),
        contentType: "application/json",
        crossDomain: true,
        success: function (data) {
//            $("#loading-indicator").hide();
            location.reload();
        },
        error: function (jqXHR, textStatus, errorThrown) {
//            $("#loading-indicator").hide();
            console.error("Error getting post list:", errorThrown);
        }
    });
}




$(document).ready(function () {

});