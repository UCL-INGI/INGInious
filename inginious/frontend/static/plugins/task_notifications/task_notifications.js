"use strict";

var notificationCheckbox = document.getElementById("notification-checkbox");

var notificationsEnabled = Notification.permission === "granted" && localStorage.getItem("taskNotifications") === "on";
notificationCheckbox.checked = notificationsEnabled;

notificationCheckbox.addEventListener("change", function (e) {
    if (e.target.checked) {
        if (!("Notification" in window)) {
            e.target.checked = false;
            alert("This browser does not support notifications.");
            return;
        }

        Notification.requestPermission().then(function (permission) {
            if (permission === "granted") {
                if (localStorage.getItem("taskNotifications") === null) {
                    new Notification("Task notifications are now enabled", {
                        body: "You will now receive a notification any time a task you have submitted has finished running. " +
                              "The notification will only display if you are not currently looking at the task's tab. " +
                              "\n\n" +
                              "This explanation will only show up once.",
                        icon: "/static/images/header.png",
                    });
                }

                localStorage.setItem("taskNotifications", "on");
            } else {
                e.target.checked = false;
                alert("Your browser has not granted INGInious the permission to send you notifications. " +
                      "Please check your browser's settings.");
            }
        });
    } else {
        localStorage.setItem("taskNotifications", "off");
    }
});
