import web
from inginious.frontend.plugins.utils.admin_api import AdminApi
from inginious.frontend.pages.course_admin.task_edit_file import CourseTaskFiles
from inginious.frontend.plugins.utils import get_mandatory_parameter


class TaskTestCasesFilesApi(AdminApi):

    def API_GET(self):
        """
        Returns a list of files and directories as a JSON list.
        Each entry of the output is an object (representing a file or directory) with the following
        properties:
        - "level": Integer. Indicates the depth level of this entry.
        - "is_directory": Boolean. Indicates whether the current entry is a directory. If False, it
        is a file.
        - "name": The file or directory name.
        - "complete_name": The full path of the entry.
        """
        parameters = web.input()

        courseid = get_mandatory_parameter(parameters, "course_id")
        taskid = get_mandatory_parameter(parameters, "task_id")

        self.get_course_and_check_rights(courseid)

        file_list = CourseTaskFiles.get_task_filelist(self.task_factory, courseid, taskid)
        result = [
            {
                "level": level,
                "is_directory": is_directory,
                "name": name,
                "complete_name": complete_name[1:] if complete_name.startswith("/") else complete_name
            } for level, is_directory, name, complete_name in file_list
        ]

        return 200, result
