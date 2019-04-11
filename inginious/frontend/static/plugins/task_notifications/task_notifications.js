"use strict";

$("#notifications-checkbox").change((e) => {
    if ($(e.target).is(":checked")) {
        Notification.requestPermission().then(permission => {
            if (permission === "granted") {
                localStorage.setItem("taskNotifications", "on");
            }
        });
    } else {
        localStorage.setItem("taskNotifications", "off");
    }
});
