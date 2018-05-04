let studio_grader_test_case_sequence = 0;
let grader_test_cases_count = 0;

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

    let test_id = studio_grader_test_case_sequence;

    let inputFile = test_case["input_file"];
    let outputFile = test_case["output_file"];

    if (!inputFile || !outputFile) {
      return;
    }

    let template = $("#test_case_template").html().replace(/TID/g, test_id);

    let templateElement = $(template);
    templateElement.find("#grader_test_cases_" + test_id + "_input_file").val(inputFile);
    templateElement.find("#grader_test_cases_" + test_id + "_output_file").val(outputFile);
    templateElement.find("#grader_test_cases_" + test_id + "_weight").val(
      test_case["weight"]);
    templateElement.find("#grader_test_cases_" + test_id + "_diff_shown").prop('checked',
      test_case["diff_shown"]);

    studio_grader_test_case_sequence++;
    grader_test_cases_count++;

    let first_row = (grader_test_cases_count == 1);

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
    let container = $("#accordion");

    let problems = [];
    $.each(container.children(), function(index, value) {
      let id = value.id;
      let prefix = "subproblem_well_";
      if (!id.startsWith(prefix)) {
        throw new Error("Unable to process problem well: " + id);
      }

      let problemId = id.substring(prefix.length);
      let type = $(value).find("[name='problem[" + problemId + "][type]']").val();

      problems.push({
        "id": problemId,
        "type": type
      });
    });

    let graderSelect = $("#grader_problem_id");
    let currentlySelectedItem = graderSelect.val();

    graderSelect.empty();
    $.each(problems, function(index, problem) {
      if (problem.type === "code_multiple_languages" ||
          problem.type === "code_file_multiple_languages") {
          graderSelect.append($("<option>", {
            "value": problem.id,
            "text": problem.id
          }));
      }
    });

    graderSelect.val(currentlySelectedItem);
}

function studio_set_initial_problem(initialProblemId){
    let selectedItem = '';
    let graderSelect = $("#grader_problem_id");
    let generateGraderIsChecked = $("#generate_grader").is(':checked');

    if(generateGraderIsChecked && initialProblemId){
        selectedItem = initialProblemId;
        graderSelect.append($("<option>", {
            "value": initialProblemId,
            "text": initialProblemId
        }));
    }
    graderSelect.val(selectedItem);
}

function studio_update_grader_files()
{
    $.get('/api/grader_generator/test_file_api', {
        course_id: courseId,
        task_id: taskId
    }, function(files) {
        let inputFileSelect = $("#grader_test_case_in");
        let outputFileSelect = $("#grader_test_case_out");

        inputFileSelect.empty();
        outputFileSelect.empty();

        $.each(files, function(index, file) {
          if (file.is_directory) {
            return;
          }

          let entry = $("<option>", {
            "value": file.complete_name,
            "text": file.complete_name
          });

          inputFileSelect.append(entry);
          outputFileSelect.append(entry.clone());
        });
    }, "json");

}
