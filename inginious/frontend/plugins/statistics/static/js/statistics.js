var CsvConverter = (function () {
    function CsvConverter(data) {
        this.data = data;
    }

    CsvConverter.prototype.downloadCsv = function () {
        var filename = 'export.csv';

        var csv = Papa.unparse(this.data);
        csv = 'data:text/csv;charset=utf-8,' + csv;

        var data = encodeURI(csv);

        var link = document.createElement('a');
        link.setAttribute('href', data);
        link.setAttribute('download', filename);
        link.click();
    };

    return CsvConverter;
}());

var Statistic = (function () {
    function Statistic() {
        this._cachedPromise = null;
    }

    Statistic.prototype._fetchAndCacheData = function () {
        if (this._cachedPromise == null) {
            this._cachedPromise = this._fetchData();
        }

        return this._cachedPromise;
    };

    Statistic.prototype.plotAsync = function () {
        var statistic = this;
        this._fetchAndCacheData().then(function (data) {
            statistic._plotData(data);
        });
    };

    Statistic.prototype._fetchCsvData = function () {
        return this._fetchAndCacheData();
    };

    Statistic.prototype.downloadCsvAsync = function () {
        this._fetchCsvData().then(function (data) {
            var csvConverter = new CsvConverter(data);
            csvConverter.downloadCsv();
        });
    };

    Statistic.prototype._plotData = function (data) {
        throw 'Not implemented';
    };

    Statistic.prototype._fetchData = function () {
        throw 'Not implemented';
    };

    return Statistic;
})();

function createSubmissionLink(courseId, userName, taskId, submissionId) {
    var urlTemplate = _.template("/admin/${ courseId }/student/${ userName }/${ taskId }/${ submissionId }");

    return urlTemplate({
        courseId: courseId,
        userName: userName,
        taskId: taskId,
        submissionId: submissionId
    });
}

function generateVerdictSubmissionTable(tableId, submissions){
    var table = $("#" + tableId);

    table.html("<thead><tr><th>Username</th><th>Grade</th><th>Status</th><th>Summary result</th><th>Submitted on</th><th>Submission</th></tr></thead>");
    var tableBody = $("<tbody/>");

    for(var i = 0; i < submissions.length; ++i) {
        var row = $("<tr/>");
        var entry = submissions[i];

        var cells = [entry.username, entry.grade, entry.status || '-', entry.summary_result || '-',
            entry.submitted_on || '-'];

        for(var j = 0; j < cells.length; ++j) {
            var cell = $("<td/>");
            cell.text(cells[j]);
            row.append(cell);
        }

        var submissionCell = $("<td/>");
        if (entry.id) {
            var submissionLink = $("<a>", {
                text: entry.id,
                href: createSubmissionLink(adminStatistics.courseId, entry.username,
                    entry.taskId, entry.id)
            });

            submissionCell.append(submissionLink);
        } else {
            submissionCell.text('No submission available');
        }

        row.append(submissionCell);

        tableBody.append(row);
    }

    table.append(tableBody);
}

function generateSubmissionTable(tableId, userTasks) {
    var table = $("#" + tableId);

    table.html("<thead><tr><th>Username</th><th>Grade</th><th>Status</th><th>Summary result</th><th>Submitted on</th><th>Submission</th></tr></thead>");
    var tableBody = $("<tbody/>");

    for(var i = 0; i < userTasks.length; ++i) {
        var row = $("<tr/>");
        var entry = userTasks[i];
        var submission = entry.submission || {};

        var cells = [entry.username, entry.grade, submission.status || '-', submission.summary_result || '-',
            submission.submitted_on || '-'];

        for(var j = 0; j < cells.length; ++j) {
            var cell = $("<td/>");
            cell.text(cells[j]);
            row.append(cell);
        }

        var submissionCell = $("<td/>");
        if (submission.id) {
            var submissionLink = $("<a>", {
                text: submission.id,
                href: createSubmissionLink(adminStatistics.courseId, entry.username,
                    submission.taskId, submission.id)
            });

            submissionCell.append(submissionLink);
        } else {
            submissionCell.text('No submission available');
        }

        row.append(submissionCell);

        tableBody.append(row);
    }

    table.append(tableBody);
}

function createAlertHtml(alertClass, content) {
    var alertHtml = '<div class="alert ' + alertClass + ' alert-dismissible" role="alert">' +
        '<button type="button" class="close" data-dismiss="alert" aria-label="Close"><span aria-hidden="true">&times;</span></button>' +
        content + '</div>';

    return alertHtml;
}
