function showNotification(notification_text, showing_time=false) {

  setTimeout(function() {
      var notification = document.createElement("div");
      notification.className = "notification";
      notification.innerHTML = notification_text;

      document.body.appendChild(notification);

      if (showing_time==true){
          setTimeout(function() {
               notification.remove();
          }, 5000);
      }

  }, 1000);


}