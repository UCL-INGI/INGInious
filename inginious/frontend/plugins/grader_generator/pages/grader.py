import json
import tempfile
import os
from inginious.frontend.pages.course_admin.task_edit import CourseEditTask
from collections import OrderedDict


_PLUGIN_PATH = os.path.dirname(__file__)
_BASE_RENDERER_PATH = _PLUGIN_PATH
_RUN_FILE_TEMPLATE_PATH = os.path.join(_PLUGIN_PATH, 'run_file_template.txt')


class InvalidGraderTestCaseError(Exception):
    def __init__(self, message, *args):
        super().__init__(message, *args)

        self.message = message


def parse_grader_test_case(test_case_content):
    if not test_case_content.get("input_file", None):
        raise InvalidGraderTestCaseError("Invalid input file in grader test case")

    if not test_case_content.get("output_file", None):
        raise InvalidGraderTestCaseError("Invalid output file in grader test case")

    try:
        test_case_content["weight"] = float(test_case_content.get("weight", 1.0))
    except (ValueError, TypeError):
        raise InvalidGraderTestCaseError("The weight for grader test cases must be a float")

    if test_case_content["weight"] < 0:
        raise InvalidGraderTestCaseError("The weight for grader test cases must be non-negative")

    test_case_content["diff_shown"] = "diff_shown" in test_case_content

    return test_case_content


def generate_grader(task_data, task_fs):
    if "grader_problem_id" not in task_data:
        return json.dumps({"status": "error", "message": "Grader: the problem was not specified"})

    if task_data["grader_problem_id"] not in task_data["problems"]:
        return json.dumps({"status": "error", "message": "Grader: problem does not exist"})

    problem_type = task_data["problems"][task_data["grader_problem_id"]]["type"]
    if problem_type not in ['code_multiple_languages', 'code_file_multiple_languages']:
        return json.dumps({"status": "error",
                           "message": "Grader: only Code Multiple Language and Code File Multiple Language " +
                                      "problems are supported"})

    with open(_RUN_FILE_TEMPLATE_PATH, "r") as f:
        run_file_template = f.read()

    problem_id = task_data["grader_problem_id"]
    test_cases = [(test_case["input_file"], test_case["output_file"])
                  for test_case in task_data["grader_test_cases"]]
    weights = [test_case["weight"] for test_case in task_data["grader_test_cases"]]
    options = {
        "compute_diff": task_data["grader_compute_diffs"],
        "treat_non_zero_as_runtime_error": task_data["treat_non_zero_as_runtime_error"],
        "diff_max_lines": task_data["grader_diff_max_lines"],
        "diff_context_lines": task_data["grader_diff_context_lines"],
        "output_diff_for": [test_case["input_file"] for test_case in task_data["grader_test_cases"]
                            if test_case["diff_shown"]]
    }

    if len(test_cases) == 0:
        return json.dumps(
            {"status": "error", "message": "You must provide test cases to autogenerate the grader"})

    with tempfile.TemporaryDirectory() as temporary_folder_name:
        run_file_name = 'run'
        target_run_file = os.path.join(temporary_folder_name, run_file_name)

        with open(target_run_file, "w") as f:
            f.write(run_file_template.format(
                problem_id=repr(problem_id), test_cases=repr(test_cases),
                options=repr(options), weights=repr(weights)))

        task_fs.copy_to(temporary_folder_name)


def on_task_editor_submit(course, taskid, task_data, task_fs):
    try:
        task_data["grader_diff_max_lines"] = int(task_data.get("grader_diff_max_lines", None))
    except (ValueError, TypeError):
        return json.dumps({"status": "error", "message": "'Maximum diff lines' must be an integer"})

    if task_data["grader_diff_max_lines"] <= 0:
        return json.dumps({"status": "error", "message": "'Maximum diff lines' must be positive"})

    try:
        task_data["grader_diff_context_lines"] = int(task_data.get("grader_diff_context_lines", None))
    except (ValueError, TypeError):
        return json.dumps({"status": "error", "message": "'Diff context lines' must be an integer"})

    if task_data["grader_diff_context_lines"] <= 0:
        return json.dumps({"status": "error", "message": "'Diff context lines' must be positive"})

    task_data["grader_compute_diffs"] = "grader_compute_diffs" in task_data
    task_data["treat_non_zero_as_runtime_error"] = "treat_non_zero_as_runtime_error" in task_data
    task_data["generate_grader"] = "generate_grader" in task_data

    grader_test_cases = CourseEditTask.dict_from_prefix("grader_test_cases", task_data) or OrderedDict()

    # Transform grader_test_cases[] entries into an actual array (they are sent as separate keys).
    keys_to_remove = [key for key, _ in task_data.items() if key.startswith("grader_test_cases[")]
    for key in keys_to_remove:
        del task_data[key]

    try:
        task_data["grader_test_cases"] = [parse_grader_test_case(val) for _, val in grader_test_cases.items()]
    except InvalidGraderTestCaseError as e:
        return json.dumps({"status": "error", "message": e.message})

    task_data["grader_test_cases"].sort(key=lambda test_case: (test_case["input_file"], test_case["output_file"]))

    input_files_are_unique = (len(set(test_case["input_file"] for test_case in task_data["grader_test_cases"])) ==
                              len(task_data["grader_test_cases"]))

    if not input_files_are_unique:
        return json.dumps({"status": "error", "message": "Duplicated input files in grader"})

    for test_case in task_data["grader_test_cases"]:
        if not task_fs.exists(test_case["input_file"]):
            return json.dumps(
                {"status": "error", "message": "Grader input file does not exist: " + test_case["input_file"]})

        if not task_fs.exists(test_case["output_file"]):
            return json.dumps(
                {"status": "error", "message": "Grader output file does not exist: " + test_case["output_file"]})

    if task_data["generate_grader"]:
        return generate_grader(task_data, task_fs)

    return None


def grader_generator_tab(course, taskid, task_data, template_helper):
    tab_id = 'tab_grader'
    link = '<i class="fa fa-check-circle fa-fw"></i>&nbsp; Grader'
    grader_test_cases_dump = json.dumps(task_data.get('grader_test_cases', []))
    content = template_helper.get_custom_renderer(_BASE_RENDERER_PATH, layout=False).grader(task_data,
                                                                                            grader_test_cases_dump,
                                                                                            course, taskid)
    template_helper.add_javascript('/grader_generator/static/js/grader_generator.js')

    return tab_id, link, content


def grader_footer(course, taskid, task_data, template_helper):
    return template_helper.get_custom_renderer(_BASE_RENDERER_PATH, layout=False).grader_templates()

