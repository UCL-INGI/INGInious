var COLOR_COMPILATION_ERROR = 'rgb(236,199,6)';
var COLOR_TIME_LIMIT_EXCEEDED = 'rgb(50,120,202)';
var COLOR_MEMORY_LIMIT_EXCEEDED = 'rgb(119,92,133)';
var COLOR_RUNTIME_ERROR = 'rgb(2,164,174)';
var COLOR_WRONG_ANSWER = 'rgb(227,79,54)';
var COLOR_INTERNAL_ERROR = 'rgb(137,139,37)';
var COLOR_ACCEPTED = 'rgb(35,181,100)';
var COLOR_LABEL = 'rgb(107, 107, 107)';

var errorContainer = $("#plotErrorContainer");

function getDataNormalized(data_entry, data_count_obj){
    return data_entry.count/data_count_obj[data_entry.task_id]*100;
}

function getData(data_entry, data_count_obj){
    return data_entry.count;
}

function createObjectToPlotData(data, data_count_obj, verdict, color_category, get_function) {

    var plotData = {
    x: [],
    y: [],
    marker: {color: color_category},
    name: verdict,
    type: 'bar'
    };

    for(var i = 0; i < data.length; ++i) {

    if(data[i].summary_result === verdict){
        plotData.x.push(data[i].task_id);
        plotData.y.push(get_function(data[i], data_count_obj));
    }
    }
    return plotData;
}

function plotVerdictStatisticsChart(id_div, data, statistic_title, normalized, api_url, generateTable) {

    var data_count_obj = {};

    var yLabel = normalized ? "Percentage of tasks" : "Number of tasks";

    var tasks_ids = [];
    for(var i = 0; i < data.length; i++){
    if(data_count_obj[data[i].task_id] == null){
        data_count_obj[data[i].task_id] = 0;
        tasks_ids.push(data[i].task_id);
    }
    data_count_obj[data[i].task_id] += data[i].count;
    }

    var get_function = normalized ? getDataNormalized : getData;

    var compilation_error_data = createObjectToPlotData(data, data_count_obj,
    "COMPILATION_ERROR", COLOR_COMPILATION_ERROR, get_function);
    var time_limit_data = createObjectToPlotData(data, data_count_obj,
    "TIME_LIMIT_EXCEEDED", COLOR_TIME_LIMIT_EXCEEDED, get_function);
    var memory_limit_data = createObjectToPlotData(data, data_count_obj,
    "MEMORY_LIMIT_EXCEEDED", COLOR_MEMORY_LIMIT_EXCEEDED, get_function);
    var runtime_error_data = createObjectToPlotData(data, data_count_obj,
    "RUNTIME_ERROR", COLOR_RUNTIME_ERROR, get_function);
    var wrong_answer_data = createObjectToPlotData(data, data_count_obj,
    "WRONG_ANSWER", COLOR_WRONG_ANSWER, get_function);
    var internal_error_data = createObjectToPlotData(data, data_count_obj,
    "INTERNAL_ERROR", COLOR_INTERNAL_ERROR, get_function);
    var accepted_data = createObjectToPlotData(data, data_count_obj,
    "ACCEPTED", COLOR_ACCEPTED, get_function);

    var plotData = [compilation_error_data, time_limit_data, memory_limit_data,

    runtime_error_data, wrong_answer_data, internal_error_data, accepted_data];

    var layout = {
    barmode: 'stack',
    title: statistic_title,
    hovermode: 'closest',
    xaxis: {
        title: 'Tasks',
        categoryorder : "array",
        categoryarray : tasks_ids,
        titlefont:{
        size: 16,
        color: COLOR_LABEL
        }
    },
    yaxis: {
        title: yLabel,
        titlefont: {
        size: 16,
        color: COLOR_LABEL
        }
    }
    };

    Plotly.purge(id_div);
    Plotly.newPlot(id_div, plotData, layout);

    var container = $("#" + id_div);


    container.unbind('plotly_click');
    container[0].on('plotly_click', function(data){
        var point = data.points[0];
        var pointNumber = point.pointNumber;
        var taskId = point.data.x[pointNumber];
        var summaryResult = point.data.name;
        $.get(api_url, {
            course_id: adminStatistics.courseId,
            task_id: taskId,
            summary_result: summaryResult
        }, generateTable, "json").fail(function(){
            errorContainer.html(createAlertHtml("alert-danger",
                "Something went wrong while fetching the submission list. Try again later."));
        });
    });

}

var GradeDistributionStatistic = (function() {
    function GradeDistributionStatistic(containerId) {
        Statistic.call(this);
        this.containerId = containerId;
    }

    GradeDistributionStatistic.prototype = Object.create(Statistic.prototype);

    GradeDistributionStatistic.prototype._plotData = function(data) {
        var plotData = _.map(data, function(item) {
            return {
                y: item.grades,
                taskId: item.task_id,
                name: item.task_name,
                boxmean: true,
                type: 'box',
                marker: {
                    outliercolor: 'rgba(219, 64, 82, 0.6)',
                    line: {
                        outliercolor: 'rgba(219, 64, 82, 1.0)',
                        outlierwidth: 2
                    }
                },
                boxpoints: 'all'
            };
        });

        var layout = {
            xaxis: {title: 'Task name', type: 'category'},
            yaxis: {title: 'Grade', type: 'linear', range: [-10, 110], zeroline: false}
        };

        Plotly.newPlot(this.containerId, plotData, layout);

        var container = $("#" + this.containerId);

        container.unbind('plotly_click');
        container[0].on('plotly_click', function(data) {
            var point = data.points[0];
            var taskId = point.data.taskId;

            errorContainer.empty();

            $.get('/api/stats/admin/grade_distribution_details', {
                course_id: adminStatistics.courseId,
                task_id: taskId
            }, function(result) {
                generateSubmissionTable("statisticsGradeDistributionTable", result);
            }, "json").fail(function() {
                errorContainer.html(createAlertHtml("alert-danger", "Something went wrong while fetching the submission list. Try again later."));
            });;
        });
    };

    GradeDistributionStatistic.prototype._fetchData = function() {
        return $.get('/api/stats/admin/grade_distribution', {course_id: adminStatistics.courseId}, null, "json");
    };

    return GradeDistributionStatistic;
})();

GradeDistributionStatistic.prototype._fetchData = function() {
    return $.get('/api/stats/admin/grade_distribution', {course_id: adminStatistics.courseId}, null, "json");
};

GradeDistributionStatistic.prototype._fetchCsvData = function() {
    return this._fetchAndCacheData().then(function(data) {
        // Unwrap each grade so the CSV is properly generated.
        return _.flatMap(data, function(taskElement) {
            return _.map(taskElement.grades, function(grade) {
                return {
                    task_id: taskElement.task_id,
                    task_name: taskElement.task_name,
                    grade: grade
                };
            });
        });
    });
};

var SubmissionsVerdictStatistic = (function() {
    function SubmissionsVerdictStatistic (containerId) {
        Statistic.call(this);
        this.toggle_normalize_submissions_per_tasks = false;
        this.containerId = containerId;
    }

    SubmissionsVerdictStatistic.prototype = Object.create(Statistic.prototype);

    SubmissionsVerdictStatistic.prototype._plotData = function(data) {

            var title = "Submissions Vs Verdicts (ALL)";

            var api_url = "/api/stats/admin/submissions_verdict_details";

            var tableGenerator = generateVerdictSubmissionTable;

            var table_id = "submissionsVerdictTable";


            plotVerdictStatisticsChart(this.containerId, data,title,
                this.toggle_normalize_submissions_per_tasks, api_url, function(result){
                tableGenerator(table_id, result);
                });

    };

    SubmissionsVerdictStatistic.prototype._fetchData = function() {
        return $.get('/api/stats/admin/submissions_verdict', {course_id: adminStatistics.courseId}, null, "json");
    };
    
    SubmissionsVerdictStatistic.prototype.toggleNormalize = function(){
        this.toggle_normalize_submissions_per_tasks = !this.toggle_normalize_submissions_per_tasks;
        this.plotAsync();
    }

    return SubmissionsVerdictStatistic ;
})();

var BestSubmissionsVerdictStatistic = (function() {
    function BestSubmissionsVerdictStatistic (containerId) {
        Statistic.call(this);
        this.toggle_normalize_best_submissions_per_tasks = false;
        this.containerId = containerId;
    }

    BestSubmissionsVerdictStatistic.prototype = Object.create(Statistic.prototype);

    BestSubmissionsVerdictStatistic.prototype._plotData = function(data) {

            var title = "Submissions Vs Verdicts (BEST)";
            var api_url = "/api/stats/admin/best_submissions_verdict_details";
            var tableGenerator = generateSubmissionTable;
            var table_id = "bestSubmissionsVerdictTable";

            plotVerdictStatisticsChart(this.containerId, data, title,
                this.toggle_normalize_best_submissions_per_tasks, api_url, function(result){
                tableGenerator(table_id, result);
                });

    };

    BestSubmissionsVerdictStatistic.prototype._fetchData = function() {
        return $.get('/api/stats/admin/best_submissions_verdict', {course_id: adminStatistics.courseId}, null, "json");
    };

    BestSubmissionsVerdictStatistic.prototype.toggleNormalize = function(){
        this.toggle_normalize_best_submissions_per_tasks = !this.toggle_normalize_best_submissions_per_tasks;
        this.plotAsync();
    }

    return BestSubmissionsVerdictStatistic ;
})();

var GradeCountStatistic = (function() {
    function GradeCountStatistic(containerId) {
        Statistic.call(this);
        this.containerId = containerId;
    }

    GradeCountStatistic.prototype = Object.create(Statistic.prototype);

    GradeCountStatistic.prototype._plotData = function(data) {
        var allGrades = _.flatMap(data, function(item) {
            return item.grades;
        });

        var studentCountToPixels = 1e-03 * _.meanBy(allGrades, function(item) {
            return item.count;
        });

        var plotData = {
            mode: 'markers',
            x: [],
            y: [],
            taskIds: [],
            text: [],
            marker: {
                sizemode: "area",
                size: [],
                sizeref: studentCountToPixels
            }
        };

        for(var i = 0; i < data.length; ++i) {
            var grades = data[i].grades;
            for(var j = 0; j < grades.length; ++j) {
                plotData.x.push(data[i].task_name);
                plotData.y.push(grades[j].grade);
                plotData.taskIds.push(data[i].task_id);
                plotData.text.push("Students: " + grades[j].count);
                plotData.marker.size.push(grades[j].count);
            }
        }

        var layout = {
            xaxis: {title: 'Task name', type: 'category'},
            yaxis: {title: 'Grade', type: 'linear', range: [-10, 110]},
            hovermode: 'closest'
        };

        Plotly.newPlot(this.containerId, [plotData], layout);

        var container = $("#" + this.containerId);

        container.unbind('plotly_click');
        container[0].on('plotly_click', function(data) {
            var point = data.points[0];
            var pointNumber = point.pointNumber;
            var taskId = point.data.taskIds[pointNumber];
            var grade = point.y;

            errorContainer.empty();

            $.get('/api/stats/admin/grade_count_details', {
                course_id: adminStatistics.courseId,
                task_id: taskId,
                grade: grade
            }, function(result) {
                generateSubmissionTable("statisticsGradeTable", result);
            }, "json").fail(function() {
                errorContainer.html(createAlertHtml("alert-danger", "Something went wrong while fetching the submission list. Try again later."));
            });
        });
    };

    GradeCountStatistic.prototype._fetchData = function() {
        return $.get('/api/stats/admin/grade_count', {course_id: adminStatistics.courseId}, null, "json");
    };

    GradeCountStatistic.prototype._fetchCsvData = function() {
        return this._fetchAndCacheData().then(function(data) {
            // Unwrap each grade so the CSV is properly generated.
            return _.flatMap(data, function(taskElement) {
                return _.map(taskElement.grades, function(gradeElement) {
                    return {
                        task_id: taskElement.task_id,
                        task_name: taskElement.task_name,
                        grade: gradeElement.grade,
                        count: gradeElement.count
                    };
                });
            });
        });
    };

    return GradeCountStatistic;
})();

var gradeCountStatistic = new GradeCountStatistic("statisticsGradeDiv");
var gradeDistributionStatistic = new GradeDistributionStatistic("statisticsGradeDistributionDiv");
var submissionsVerdictStatistic = new SubmissionsVerdictStatistic("submissionsVerdictDiv");
var bestSubmissionsVerdictStatistic = new BestSubmissionsVerdictStatistic("bestSubmissionsVerdictDiv");

var tabToStatistic = {
    "gradeCount": gradeCountStatistic,
    "gradeDistribution": gradeDistributionStatistic,
    "submissionsVerdict": submissionsVerdictStatistic,
    "bestSubmissionsVerdict": bestSubmissionsVerdictStatistic
};

$(function() {
    $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        var statistic = tabToStatistic[e.target.getAttribute("aria-controls")];

        if (statistic) {
            statistic.plotAsync();
        }
    });
    $('.active > a[data-toggle="tab"]').trigger('shown.bs.tab');
});
