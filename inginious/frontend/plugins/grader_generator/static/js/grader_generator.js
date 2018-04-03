var studio_grader_test_case_sequence = 0;
var grader_test_cases_count = 0;

function studio_add_test_case_from_form()
{
    studio_add_test_case({
      "input_file": $("#grader_test_case_in").val(),
      "output_file": $("#grader_test_case_out").val()
    });
}

function studio_add_test_case(test_case)
{
    test_case = $.extend({
      "input_file": null,
      "output_file": null,
      "weight": 1.0,
      "diff_shown": false
    }, test_case);

    var test_id = studio_grader_test_case_sequence;

    var inputFile = test_case["input_file"];
    var outputFile = test_case["output_file"];

    if (!inputFile || !outputFile) {
      return;
    }

    var template = $("#test_case_template").html().replace(/TID/g, test_id);

    var templateElement = $(template);
    templateElement.find("#grader_test_cases_" + test_id + "_input_file").val(inputFile);
    templateElement.find("#grader_test_cases_" + test_id + "_output_file").val(outputFile);
    templateElement.find("#grader_test_cases_" + test_id + "_weight").val(
      test_case["weight"]);
    templateElement.find("#grader_test_cases_" + test_id + "_diff_shown").prop('checked',
      test_case["diff_shown"]);

    studio_grader_test_case_sequence++;
    grader_test_cases_count++;

    var first_row = (grader_test_cases_count == 1);

    if(first_row){
      $('#grader_test_cases_header').show();
    }

    $('#grader_test_cases_container').append(templateElement);
}

function studio_load_grader_test_cases(test_cases) {
    $.each(test_cases, function(_, test_case) {
      studio_add_test_case(test_case);
    });
}

function studio_remove_test_case(id) {
    $("#grader_test_cases_" + id).remove();
    grader_test_cases_count--;
    if(grader_test_cases_count == 0){
      $('#grader_test_cases_header').hide();
    }
}

function studio_update_grader_problems() {
    var container = $("#accordion");

    var problems = [];
    $.each(container.children(), function(index, value) {
      var id = value.id;
      var prefix = "subproblem_well_";
      if (!id.startsWith(prefix)) {
        throw new Error("Unable to process problem well: " + id);
      }

      var problemId = id.substring(prefix.length);
      var type = $(value).find("[name='problem[" + problemId + "][type]']").val();

      problems.push({
        "id": problemId,
        "type": type
      });
    });

    var graderSelect = $("#grader_problem_id");
    var currentlySelectedItem = graderSelect.val();

    graderSelect.empty();
    $.each(problems, function(index, problem) {
      if (problem.type === "code-multiple-languages" ||
          problem.type === "code-file-multiple-languages") {
          graderSelect.append($("<option>", {
            "value": problem.id,
            "text": problem.id
          }));
      }
    });

    graderSelect.val(currentlySelectedItem);
}

function studio_update_grader_files()
{
    $.ajax({
      success: function(files) {
        var inputFileSelect = $("#grader_test_case_in");
        var outputFileSelect = $("#grader_test_case_out");

        inputFileSelect.empty();
        outputFileSelect.empty();

        $.each(files, function(index, file) {
          if (file.is_directory) {
            return;
          }

          var entry = $("<option>", {
            "value": file.complete_name,
            "text": file.complete_name
          });

          inputFileSelect.append(entry);
          outputFileSelect.append(entry.clone());
        });
      },
      method: "GET",
      data: {
        "action": "list_as_json"
      },
      dataType: "json",
      url: location.pathname + "/files"
    });
}
