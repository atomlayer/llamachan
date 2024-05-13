function highlight(id) {
    document.getElementById(id).style.backgroundColor = '#eedacb';
}


function addBackLink(e) {
    const targetDiv = e.target;

}


function attachClickEvent() {
    const elements = document.querySelectorAll('.post_link');

    elements.forEach(element => {
        element.addEventListener('click', (event) => {
            highlight("no_" + event.target.text[1]);
        });
    });
}

function attachBackLink(node) {

}

function observeDOMChanges() {
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach(node => {
                    if (node.classList && node.classList.contains('post_link')) {
                        attachClickEvent();
                    }
                    if (node.classList && node.classList.contains('post')) {
                        attachBackLink(node)
                    }
                });
            }
        });
    });

    observer.observe(document.body, {childList: true, subtree: true});
}

// Call observeDOMChanges when the page loads
window.onload = function () {
    attachClickEvent();
    observeDOMChanges();
};




function appendPost(postData) {

    let img_html = ""
    if (postData.image_file_name!="")
    {
        img_html = `<img alt="Post Image" class="image" onclick="open_full_image(this)"
                    src="/static/uploads/${postData.image_file_name}">`;
    }



    const postHtml = `
            <div class="post" id="no_${postData.number_in_thread}">
                <div class="post_title">
                    <div class="op_text_title_main">${postData.subject}</div>
                    <div class="op_text_title"> Anonymous&nbsp;${formatDateTime(postData.date_time_of_creation)}</div>
                    <a href="#" onclick="showForm(this); return false;" class="post_number">#${postData.number_in_thread}</a>
                </div>
                <div class="post_text">
                    ${img_html}

                    ${postData.comment}
                </div>
            </div>
        `;

    $(".container").append(postHtml);

    count_of_posts++;
}

function formatDateTime(dateTimeString) {
    const dateTime = new Date(dateTimeString);
    const formattedDate = dateTime.toLocaleDateString();
    const formattedTime = dateTime.toLocaleTimeString();
    return `${formattedDate} ${formattedTime}`;
}

function getPostList() {
    const lastPostNumber = count_of_posts;

    $.ajax({
        type: "POST",
        url: "/get_post_list",
        data: JSON.stringify({
            thread_id: threadId,
            last_post_number: lastPostNumber
        }),
        contentType: "application/json",
        crossDomain: true,
        success: function (data) {
            data.forEach(postData => {
                appendPost(postData);
            });
        },
        error: function (jqXHR, textStatus, errorThrown) {
            console.error("Error getting post list:", errorThrown);
        }
    });
}


function generateMorePosts() {
    const lastPostNumber = count_of_posts;

    showNotification('Generation is running...', true)

    $.ajax({
        type: "POST",
        url: "/get_more_posts",
        data: JSON.stringify({
            thread_id: threadId,
        }),
        contentType: "application/json",
        crossDomain: true,
        success: function (data) {

        },
        error: function (jqXHR, textStatus, errorThrown) {
            console.error("Error getting post list:", errorThrown);
        }
    });
}



$(document).ready(function () {
    function fetchPostsInterval() {
        getPostList();
        setTimeout(fetchPostsInterval, 1000);
    }

    fetchPostsInterval();

});


function showForm(link) {
    var form = document.getElementById('draggableForm');
    form.style.display = 'block';


    var screenWidth = window.innerWidth;
    var screenHeight = window.innerHeight;


    var formWidth = form.offsetWidth;
    var formHeight = form.offsetHeight;


    var top = (screenHeight - formHeight) / 2 + window.scrollY;
    var left = (screenWidth - formWidth) / 2;


    form.style.top = top + 'px';
    form.style.left = left + 'px';

    var linkText = link.textContent;
    var numbers = linkText.match(/\d+/g);

    if (numbers) {
        numbers.forEach(function (number) {
            console.log(number);

            var contextAreaComment = document.getElementById("contextAreaComment")
            contextAreaComment.value = ">>" + numbers.toString()+"\n";
        });
    }


}


window.onload = function () {
    dragElement(document.getElementById('draggableForm'));
};

function dragElement(elmnt) {
    var pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
    if (document.getElementById(elmnt.id + "header")) {
        document.getElementById(elmnt.id + "header").onmousedown = dragMouseDown;
    } else {
        elmnt.onmousedown = dragMouseDown;
    }

    function dragMouseDown(e) {
        if (e.target.tagName.toLowerCase() === 'textarea' || e.target.tagName.toLowerCase() === 'input') {
            return; // Do not initiate drag if clicking on textarea or input
        }

        e = e || window.event;
        e.preventDefault();
        pos3 = e.clientX;
        pos4 = e.clientY;
        document.onmouseup = closeDragElement;
        document.onmousemove = elementDrag;
    }

    function elementDrag(e) {
        e = e || window.event;
        e.preventDefault();
        pos1 = pos3 - e.clientX;
        pos2 = pos4 - e.clientY;
        pos3 = e.clientX;
        pos4 = e.clientY;
        elmnt.style.top = (elmnt.offsetTop - pos2) + "px";
        elmnt.style.left = (elmnt.offsetLeft - pos1) + "px";
    }

    function closeDragElement() {
        document.onmouseup = null;
        document.onmousemove = null;
    }
}

function submitForm() {
    var form = document.querySelector('form');
    var formData = new FormData(form);

    showNotification('Generation is running...', true)

    fetch('/add_post', {
        method: 'POST',
        body: formData,
        mode: 'cors',
        credentials: 'include'
    })
        .then(response => {
            if (response.ok) {
                document.getElementById('draggableForm').style.display = 'none';

            } else {
                // Handle error response
            }
        })
        .catch(error => {
            // Handle network error
        });


}

function closeForm() {
    // Скрываем форму при нажатии на крестик
    document.getElementById('draggableForm').style.display = 'none';
}

function goBack() {
    window.history.back();
}

// Function to scroll to the top
function goToTop() {
    window.scrollTo(0, 0);
}

// Function to refresh the page
function refreshPage() {
    location.reload();
}



//
// // Add an event listener to each image with the 'expandable-image' class
// document.querySelectorAll('.expandable-image').forEach(img => {
//     img.addEventListener('click', function() {
//         // Toggle the 'expanded-image' class on the parent div
//         this.closest('.post_image').classList.toggle('expanded-image');
//     });
// });
//
// // Close the expanded image when clicking outside it
// document.addEventListener('click', function(event) {
//     if (event.target.closest('.expanded-image')) {
//         // Close the expanded image
//         document.querySelector('.expanded-image').classList.remove('expanded-image');
//     }
// });