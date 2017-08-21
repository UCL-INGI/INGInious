# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

""" Pages that allow editing of tasks """
import tempfile
from collections import OrderedDict
import copy
import json
import bson
import os.path
import re
from zipfile import ZipFile
import logging

import web

from inginious.common.base import id_checker
import inginious.common.custom_yaml
from inginious.frontend.webapp.accessible_time import AccessibleTime
from inginious.frontend.webapp.tasks import WebAppTask
from inginious.frontend.webapp.pages.course_admin.task_edit_file import CourseTaskFiles
from inginious.frontend.webapp.pages.course_admin.utils import INGIniousAdminPage
from inginious.frontend.common.task_problems import DisplayableBasicCodeProblem

class CourseEditTask(INGIniousAdminPage):
    """ Edit a task """
    _logger = logging.getLogger("inginious.webapp.task_edit")

    def GET_AUTH(self, courseid, taskid):  # pylint: disable=arguments-differ
        """ Edit a task """
        if not id_checker(taskid):
            raise Exception("Invalid task id")

        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=False)

        try:
            task_data = self.task_factory.get_task_descriptor_content(courseid, taskid)
        except:
            task_data = None
        if task_data is None:
            task_data = {}

        environments = self.containers

        current_filetype = None
        try:
            current_filetype = self.task_factory.get_task_descriptor_extension(courseid, taskid)
        except:
            pass
        available_filetypes = self.task_factory.get_available_task_file_extensions()

        # custom problem-type:
        for pid in task_data.get("problems", {}):
            problem = task_data["problems"][pid]
            if (problem["type"] == "code" and "boxes" in problem) or problem["type"] not in (
                    "code", "code-single-line", "code-file", "code-file-multiple-languages", "match", "multiple-choice"):
                problem_copy = copy.deepcopy(problem)
                for i in ["name", "header"]:
                    if i in problem_copy:
                        del problem_copy[i]
                problem["custom"] = inginious.common.custom_yaml.dump(problem_copy)

        return self.template_helper.get_renderer().course_admin.task_edit(
            course,
            taskid,
            task_data,
            environments,
            json.dumps(
                task_data.get(
                    'problems',
                    {})),
            json.dumps(
                task_data.get('grader_test_cases', [])),
            self.contains_is_html(task_data),
            current_filetype,
            available_filetypes,
            AccessibleTime,
            CourseTaskFiles.get_task_filelist(self.task_factory, courseid, taskid),
            DisplayableBasicCodeProblem._available_languages)

    @classmethod
    def contains_is_html(cls, data):
        """ Detect if the problem has at least one "xyzIsHTML" key """
        for key, val in data.items():
            if key.endswith("IsHTML"):
                return True
            if isinstance(val, (OrderedDict, dict)) and cls.contains_is_html(val):
                return True
        return False

    @classmethod
    def dict_from_prefix(cls, prefix, dictionary):
        """
            >>> from collections import OrderedDict
            >>> od = OrderedDict()
            >>> od["problem[q0][a]"]=1
            >>> od["problem[q0][b][c]"]=2
            >>> od["problem[q1][first]"]=1
            >>> od["problem[q1][second]"]=2
            >>> AdminCourseEditTask.dict_from_prefix("problem",od)
            OrderedDict([('q0', OrderedDict([('a', 1), ('b', OrderedDict([('c', 2)]))])), ('q1', OrderedDict([('first', 1), ('second', 2)]))])
        """
        o_dictionary = OrderedDict()
        for key, val in dictionary.items():
            if key.startswith(prefix):
                o_dictionary[key[len(prefix):].strip()] = val
        dictionary = o_dictionary

        if len(dictionary) == 0:
            return None
        elif len(dictionary) == 1 and "" in dictionary:
            return dictionary[""]
        else:
            return_dict = OrderedDict()
            for key, val in dictionary.items():
                ret = re.search(r"^\[([^\]]+)\](.*)$", key)
                if ret is None:
                    continue
                return_dict[ret.group(1)] = cls.dict_from_prefix("[{}]".format(ret.group(1)), dictionary)
            return return_dict

    def parse_problem(self, problem_content):
        """ Parses a problem, modifying some data """
        del problem_content["@order"]

        # store boolean fields as booleans
        for field in ["optional", "multiple", "centralize"]:
            if field in problem_content:
                problem_content[field] = True

        # Check for a language to submit a problem
        if "languages" in problem_content:
            for language in problem_content["languages"]:
                problem_content["languages"][language] = True

        if "choices" in problem_content:
            problem_content["choices"] = [val for _, val in sorted(iter(problem_content["choices"].items()), key=lambda x: int(x[0]))]
            for choice in problem_content["choices"]:
                if "valid" in choice:
                    choice["valid"] = True
                if "feedback" in choice and choice["feedback"].strip() == "":
                    del choice["feedback"]

        for message in ["error_message", "success_message"]:
            if message in problem_content and problem_content[message].strip() == "":
                del problem_content[message]

        if "limit" in problem_content:
            try:
                problem_content["limit"] = int(problem_content["limit"])
            except:
                del problem_content["limit"]

        if "allowed_exts" in problem_content:
            if problem_content["allowed_exts"] == "":
                del problem_content["allowed_exts"]
            else:
                problem_content["allowed_exts"] = problem_content["allowed_exts"].split(',')

        if "max_size" in problem_content:
            try:
                problem_content["max_size"] = int(problem_content["max_size"])
            except:
                del problem_content["max_size"]

        if problem_content["type"] == "custom":
            try:
                custom_content = inginious.common.custom_yaml.load(problem_content["custom"])
            except:
                raise Exception("Invalid YAML in custom content")
            problem_content.update(custom_content)
            del problem_content["custom"]

        return problem_content

    def parse_grader_test_case(self, test_case_content):
        if not test_case_content["input_file"]:
            raise Exception("Invalid input file in grader test case")

        if not test_case_content["output_file"]:
            raise Exception("Invalid output file in grader test case")

        try:
            test_case_content["weight"] = float(test_case_content["weight"])
        except:
            raise Exception("The weight for grader test cases must be a float")

        test_case_content["diff_shown"] = "diff_shown" in test_case_content

        return test_case_content

    def preprocess_grader_data(self, data):
        try:
            data["grader_diff_max_lines"] = int(data["grader_diff_max_lines"])
        except:
            return json.dumps({"status": "error", "message": "'Maximum diff lines' must be an integer"})

        if data["grader_diff_max_lines"] <= 0:
            return json.dumps({"status": "error", "message": "'Maximum diff lines' must be positive"})

        try:
            data["grader_diff_context_lines"] = int(data["grader_diff_context_lines"])
        except:
            return json.dumps({"status": "error", "message": "'Diff context lines' must be an integer"})

        if data["grader_diff_context_lines"] <= 0:
            return json.dumps({"status": "error", "message": "'Diff context lines' must be positive"})

        data["grader_compute_diffs"] = "grader_compute_diffs" in data
        data["generate_grader"] = "generate_grader" in data

        grader_test_cases = self.dict_from_prefix("grader_test_cases", data) or OrderedDict()

        # Remove test-case dirty entries.
        keys_to_remove = [key for key, _ in data.items() if key.startswith("grader_test_cases[")]
        for key in keys_to_remove:
            del data[key]

        data["grader_test_cases"] = [self.parse_grader_test_case(val) for _, val in grader_test_cases.items()]
        data["grader_test_cases"].sort(key=lambda test_case: (test_case["input_file"], test_case["output_file"]))

        if len(set(test_case["input_file"] for test_case in data["grader_test_cases"])) != len(data["grader_test_cases"]):
            return json.dumps({"status": "error", "message": "Duplicated input files in grader"})

        return None

    def postprocess_grader_data(self, data, task_fs):
        for test_case in data["grader_test_cases"]:
            if not task_fs.exists(test_case["input_file"]):
                return json.dumps(
                    {"status": "error", "message": "Grader input file does not exist: " + test_case["input_file"]})

            if not task_fs.exists(test_case["output_file"]):
                return json.dumps(
                    {"status": "error", "message": "Grader output file does not exist: " + test_case["output_file"]})

        if data["generate_grader"]:
            if data["grader_problem_id"] not in data["problems"]:
                return json.dumps({"status": "error", "message": "Grader: problem does not exist"})

            problem_type = data["problems"][data["grader_problem_id"]]["type"]
            if problem_type not in ['code-multiple-languages', 'code-file-multiple-languages']:
                return json.dumps({"status": "error",
                    "message": "Grader: only Code Multiple Language and Code File Multiple Language problems are supported"})

            current_directory = os.path.dirname(__file__)
            run_file_template_path = os.path.join(current_directory, '../../templates/course_admin/run_file_template.txt')
            run_file_template = None

            with open(run_file_template_path, "r") as f:
                run_file_template = f.read()

            problem_id = data["grader_problem_id"]
            test_cases = [(test_case["input_file"], test_case["output_file"]) for test_case in data["grader_test_cases"]]
            weights = [test_case["weight"] for test_case in data["grader_test_cases"]]
            options = {
                "compute_diff": data["grader_compute_diffs"],
                "diff_max_lines": data["grader_diff_max_lines"],
                "diff_context_lines": data["grader_diff_context_lines"],
                "output_diff_for": [test_case["input_file"] for test_case in data["grader_test_cases"]
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

        return None

    def wipe_task(self, courseid, taskid):
        """ Wipe the data associated to the taskid from DB"""
        submissions = self.database.submissions.find({"courseid": courseid, "taskid": taskid})
        for submission in submissions:
            for key in ["input", "archive"]:
                if key in submission and type(submission[key]) == bson.objectid.ObjectId:
                    self.submission_manager.get_gridfs().delete(submission[key])

        self.database.aggregations.remove({"courseid": courseid, "taskid": taskid})
        self.database.user_tasks.remove({"courseid": courseid, "taskid": taskid})
        self.database.submissions.remove({"courseid": courseid, "taskid": taskid})

        self._logger.info("Task %s/%s wiped.", courseid, taskid)

    def POST_AUTH(self, courseid, taskid):  # pylint: disable=arguments-differ
        """ Edit a task """
        if not id_checker(taskid) or not id_checker(courseid):
            raise Exception("Invalid course/task id")

        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        data = web.input(task_file={})

        # Delete task ?
        if "delete" in data:
            self.task_factory.delete_task(courseid, taskid)
            if data.get("wipe", False):
                self.wipe_task(courseid, taskid)
            raise web.seeother(self.app.get_homepath() + "/admin/"+courseid+"/tasks")

        # Else, parse content
        try:
            try:
                task_zip = data.get("task_file").file
            except:
                task_zip = None
            del data["task_file"]

            problems = self.dict_from_prefix("problem", data)
            limits = self.dict_from_prefix("limits", data)

            data = {key: val for key, val in data.items() if not key.startswith("problem") and not key.startswith("limits")}
            del data["@action"]

            if data["@filetype"] not in self.task_factory.get_available_task_file_extensions():
                return json.dumps({"status": "error", "message": "Invalid file type: {}".format(str(data["@filetype"]))})
            file_ext = data["@filetype"]
            del data["@filetype"]

            if problems is None:
                return json.dumps({"status": "error", "message": "You cannot create a task without subproblems"})

            # Order the problems (this line also deletes @order from the result)
            data["problems"] = OrderedDict([(key, self.parse_problem(val))
                                            for key, val in sorted(iter(problems.items()), key=lambda x: int(x[1]['@order']))])
            data["limits"] = limits
            if "hard_time" in data["limits"] and data["limits"]["hard_time"] == "":
                del data["limits"]["hard_time"]

            # Weight
            try:
                data["weight"] = float(data["weight"])
            except:
                return json.dumps({"status": "error", "message": "Grade weight must be a floating-point number"})

            # Groups
            if "groups" in data:
                data["groups"] = True if data["groups"] == "true" else False

            # Submision storage
            if "store_all" in data:
                try:
                    stored_submissions = data["stored_submissions"]
                    data["stored_submissions"] = 0 if data["store_all"] == "true" else int(stored_submissions)
                except:
                    return json.dumps(
                        {"status": "error", "message": "The number of stored submission must be positive!"})

                if data["store_all"] == "false" and data["stored_submissions"] <= 0:
                    return json.dumps({"status": "error", "message": "The number of stored submission must be positive!"})
                del data['store_all']

            # Submission limits
            if "submission_limit" in data:
                if data["submission_limit"] == "none":
                    result = {"amount": -1, "period": -1}
                elif data["submission_limit"] == "hard":
                    try:
                        result = {"amount": int(data["submission_limit_hard"]), "period": -1}
                    except:
                        return json.dumps({"status": "error", "message": "Invalid submission limit!"})

                else:
                    try:
                        result = {"amount": int(data["submission_limit_soft_0"]), "period": int(data["submission_limit_soft_1"])}
                    except:
                        return json.dumps({"status": "error", "message": "Invalid submission limit!"})

                del data["submission_limit_hard"]
                del data["submission_limit_soft_0"]
                del data["submission_limit_soft_1"]
                data["submission_limit"] = result

            # Accessible
            if data["accessible"] == "custom":
                data["accessible"] = "{}/{}".format(data["accessible_start"], data["accessible_end"])
            elif data["accessible"] == "true":
                data["accessible"] = True
            else:
                data["accessible"] = False
            del data["accessible_start"]
            del data["accessible_end"]

            # Checkboxes
            if data.get("responseIsHTML"):
                data["responseIsHTML"] = True

            # Network grading
            data["network_grading"] = "network_grading" in data
        except Exception as message:
            return json.dumps({"status": "error", "message": "Your browser returned an invalid form ({})".format(str(message))})

        # Get the course
        try:
            course = self.course_factory.get_course(courseid)
        except:
            return json.dumps({"status": "error", "message": "Error while reading course's informations"})

        # Get original data
        try:
            orig_data = self.task_factory.get_task_descriptor_content(courseid, taskid)
            data["order"] = orig_data["order"]
        except:
            pass

        task_fs = self.task_factory.get_task_fs(courseid, taskid)
        task_fs.ensure_exists()

        error = self.preprocess_grader_data(data)
        if error is not None:
            return error

        try:
            WebAppTask(course, taskid, data, task_fs, self.plugin_manager)
        except Exception as message:
            return json.dumps({"status": "error", "message": "Invalid data: {}".format(str(message))})

        if task_zip:
            try:
                zipfile = ZipFile(task_zip)
            except Exception:
                return json.dumps({"status": "error", "message": "Cannot read zip file. Files were not modified"})

            with tempfile.TemporaryDirectory() as tmpdirname:
                try:
                    zipfile.extractall(tmpdirname)
                except Exception:
                    return json.dumps(
                        {"status": "error", "message": "There was a problem while extracting the zip archive. Some files may have been modified"})
                task_fs.copy_to(tmpdirname)

        error = self.postprocess_grader_data(data, task_fs)
        if error is not None:
            return error

        self.task_factory.delete_all_possible_task_files(courseid, taskid)
        self.task_factory.update_task_descriptor_content(courseid, taskid, data, force_extension=file_ext)

        return json.dumps({"status": "ok"})
