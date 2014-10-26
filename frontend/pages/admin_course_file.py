""" Send a zip file containing course data """
from StringIO import StringIO
import os.path
import zipfile
import web
from common.base import INGIniousConfiguration, id_checker
from common.task_file_managers.tasks_file_manager import TaskFileManager
from frontend.custom.courses import FrontendCourse
import frontend.user as User


def make_zipfile(output_filename, source_dir, exclude):
    """
        Make a new zipfile from a source_dir, excluding files in the "exclude" list.
        Source: http://stackoverflow.com/questions/1855095/how-to-create-a-zip-archive-of-a-directory-in-python
    """
    exclude = [os.path.abspath(os.path.join(source_dir, f)) for f in exclude]
    relroot = os.path.abspath(os.path.join(source_dir))
    with zipfile.ZipFile(output_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_dir):
            # add directory (needed for empty dirs)
            zipf.write(root, os.path.relpath(root, relroot))
            for dfile in files:
                if os.path.abspath(os.path.join(root, dfile)) in exclude:
                    continue
                filename = os.path.join(root, dfile)
                if os.path.isfile(filename):  # regular files only
                    arcname = os.path.join(os.path.relpath(root, relroot), dfile)
                    zipf.write(filename, arcname)


class AdminDownloadTaskFiles(object):

    """ Send a zip file containing course data """

    def GET(self, courseid, taskid):
        """ GET """
        if not id_checker(taskid):
            raise Exception("Invalid task id")
        if not id_checker(courseid):
            raise Exception("Invalid task id")

        try:
            course = FrontendCourse(courseid)
            if not User.is_logged_in() or User.get_username() not in course.get_admins():
                raise web.notfound()
        except:
            raise web.notfound()

        exclude = ["task.{}".format(subclass.get_ext()) for subclass in TaskFileManager.__subclasses__()]
        dir_path = os.path.join(INGIniousConfiguration["tasks_directory"], courseid, taskid)

        stringio = StringIO()
        make_zipfile(stringio, dir_path, exclude)
        web.header('Content-Type', 'application/zip')
        web.header('Content-disposition', 'attachment; filename={}-{}.zip'.format(courseid, taskid))
        return stringio.getvalue()
