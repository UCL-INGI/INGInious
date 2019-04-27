"use strict";

$("#notifications-checkbox").change(function (e) {
    if ($(e.target).is(":checked")) {
        if (!("Notification" in window)) {
            alert("This browser does not support notifications.");
            return;
        }

        Notification.requestPermission().then(function (permission) {
            if (permission === "granted") {
                localStorage.setItem("taskNotifications", "on");
            }
        });
    } else {
        localStorage.setItem("taskNotifications", "off");
    }
});
