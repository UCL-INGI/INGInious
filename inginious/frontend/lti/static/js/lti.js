//
// This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
// more information about the licensing of this file.
//
"use strict";

$(function()
{
    init_common();
    init_lti();
});

function init_lti()
{

}

function init_download_page() {
    // Setaction for download page submit button
    $('form#download').submit(function() {
        downloadSubmissions();
        return false;
    });
}

// Set alert message to display on top on download page
function updateDownloadStatus(type, htmlmsg) {
    $('#content').css('height', 'auto');
    $('#downloadmsg').removeClass().addClass("alert alert-" + type);
    $('#downloadmsg').html(htmlmsg);

    $('html, body').animate(
    {
        scrollTop: $('#downloadmsg').offset().top
    }, 200);
}

// Wait for for the download archive to be ready for download
function waitForDownload(tag) {
    setTimeout(function()
    {
        jQuery.post('', {"status": true, "tag": tag}, null, "json")
            .done(function(data) {
                if(data["status"] == "done" && ! data["result"])
                    waitForDownload(tag);
                else if(data["status"] == "done" && data["result"])
                {
                    updateDownloadStatus("success", "Archive is ready. ");
                    jQuery('<a/>', {
                        href: "?archive=" + tag,
                        style: "color:white;",
                        text: 'Click here to download.'
                    }).appendTo('#downloadmsg');
                }
                else if(data["status"] == "error")
                    updateDownloadStatus("error", data["msg"]);
            })
            .fail(function() {
                updateDownloadStatus("error", "Internal error.");
            });
    }, 1000);
}

// Post the download form and initiate download archive waiting
function downloadSubmissions() {
    $('form#download').ajaxSubmit(
    {
        dataType: 'json',
        success: function(data) {
            if(data["status"] == "error")
                updateDownloadStatus("error", data["msg"]);
            else {
                updateDownloadStatus("warning", "Preparing archive...");
                waitForDownload(data["tag"]);
            }
        },
        error: function() {
            updateDownloadStatus("error", "Internal error.");
        }
    });
}
