# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.


import tarfile
import mimetypes
import urllib.request, urllib.parse, urllib.error
import tempfile
import copy
import web

from inginious.frontend.common.parsable_text import ParsableText
from inginious.frontend.webapp.pages.course_admin.utils import INGIniousAdminPage

class CourseBatchOperations(INGIniousAdminPage):
    """ Batch operation management """

    def GET_AUTH(self, courseid):  # pylint: disable=arguments-differ
        """ GET request """

        course, _ = self.get_course_and_check_rights(courseid)

        web_input = web.input()
        if "drop" in web_input:  # delete an old batch job
            try:
                self.batch_manager.drop_batch_job(web_input["drop"])
            except:
                pass

        operations = []
        for entry in list(self.batch_manager.get_all_batch_jobs_for_course(courseid)):
            ne = {"container_name": entry["container_name"],
                  "bid": str(entry["_id"]),
                  "submitted_on": entry["submitted_on"]}
            if "result" in entry:
                ne["status"] = "ok" if entry["result"]["retval"] == 0 else "ko"
            else:
                ne["status"] = "waiting"
            operations.append(ne)
        operations = sorted(operations, key=(lambda o: o["submitted_on"]), reverse=True)

        return self.template_helper.get_renderer().course_admin.batch(course, operations, self.batch_manager.get_all_batch_containers_metadata())


class CourseBatchJobCreate(INGIniousAdminPage):
    """ Creates new batch jobs """

    def GET_AUTH(self, courseid, container_name):  # pylint: disable=arguments-differ
        """ GET request """
        course, container_title, container_description, container_args = self.get_basic_info(courseid, container_name)
        return self.page(course, container_name, container_title, container_description, container_args)

    def POST_AUTH(self, courseid, container_name):  # pylint: disable=arguments-differ
        """ POST request """
        course, container_title, container_description, container_args = self.get_basic_info(courseid, container_name)
        errors = []

        # Verify that we have the right keys
        try:
            file_args = {key: {} for key in container_args if key != "submissions" and key != "course" and container_args[key]["type"] == "file"}
            batch_input = web.input(**file_args)
            for key in container_args:
                if (key != "submissions" and key != "course") or container_args[key]["type"] != "file":
                    if key not in batch_input:
                        raise Exception("It lacks a field")
                    if container_args[key]["type"] == "file":
                        batch_input[key] = batch_input[key].file.read()
        except:
            errors.append("Please fill all the fields.")

        if len(errors) == 0:
            try:
                self.batch_manager.add_batch_job(course, container_name, batch_input,
                                                 self.user_manager.session_username(),
                                                 self.user_manager.session_email())
            except:
                errors.append("An error occurred while starting the job")

        if len(errors) == 0:
            raise web.seeother('/admin/{}/batch'.format(courseid))
        else:
            return self.page(course, container_name, container_title, container_description, container_args, errors)

    def get_basic_info(self, courseid, container_name):
        course, _ = self.get_course_and_check_rights(courseid, allow_all_staff=False)
        try:
            metadata = self.batch_manager.get_batch_container_metadata(container_name)
            if metadata == (None, None, None):
                raise Exception("Container not found")
        except:
            raise web.notfound()

        container_title = metadata[0]
        container_description = ParsableText(metadata[1].encode('utf-8').decode("unicode_escape"), 'rst')

        container_args = copy.deepcopy(metadata[2])  # copy it
        for val in container_args.values():
            if "description" in val:
                val['description'] = ParsableText(val['description'].encode('utf-8').decode("unicode_escape"), 'rst').parse()

        return course, container_title, container_description, container_args

    def page(self, course, container_name, container_title, container_description, container_args, error=None):

        if "submissions" in container_args and container_args["submissions"]["type"] == "file":
            del container_args["submissions"]
        if "course" in container_args and container_args["course"]["type"] == "file":
            del container_args["course"]

        return self.template_helper.get_renderer().course_admin.batch_create(course, container_name, container_title, container_description,
                                                                             container_args, error)


class CourseBatchJobDownload(INGIniousAdminPage):
    """ Get the file of a batch job """

    def GET_AUTH(self, courseid, bid, path=""):  # pylint: disable=arguments-differ
        """ GET request """

        self.get_course_and_check_rights(courseid) # simply verify rights
        batch_job = self.batch_manager.get_batch_job_status(bid)

        if batch_job is None:
            raise web.notfound()

        if "result" not in batch_job or "file" not in batch_job["result"]:
            raise web.notfound()

        f = self.gridfs.get(batch_job["result"]["file"])

        # hack for index.html:
        if path == "/":
            path = "/index.html"

        if path == "":
            web.header('Content-Type', 'application/x-gzip', unique=True)
            web.header('Content-Disposition', 'attachment; filename="' + bid + '.tar.gz"', unique=True)
            return f.read()
        else:
            path = path[1:]  # remove the first /
            if path.endswith('/'):  # remove the last / if it exists
                path = path[0:-1]

            try:
                tar = tarfile.open(fileobj=f, mode='r:gz')
                file_info = tar.getmember(path)
            except:
                raise web.notfound()

            if file_info.isdir():  # tar.gz the dir and return it
                tmp = tempfile.TemporaryFile()
                new_tar = tarfile.open(fileobj=tmp, mode='w:gz')
                for m in tar.getmembers():
                    new_tar.addfile(m, tar.extractfile(m))
                new_tar.close()
                tmp.seek(0)
                return tmp
            elif not file_info.isfile():
                raise web.notfound()
            else:  # guess a mime type and send it to the browser
                to_dl = tar.extractfile(path).read()
                mimetypes.init()
                mime_type = mimetypes.guess_type(urllib.request.pathname2url(path))
                web.header('Content-Type', mime_type[0])
                return to_dl


class CourseBatchJobSummary(INGIniousAdminPage):
    """ Get the summary of a batch job """

    def GET_AUTH(self, courseid, bid):  # pylint: disable=arguments-differ
        """ GET request """

        course, _ = self.get_course_and_check_rights(courseid)
        batch_job = self.batch_manager.get_batch_job_status(bid)

        if batch_job is None:
            raise web.notfound()

        done = False
        submitted_on = batch_job["submitted_on"]
        container_name = batch_job["container_name"]
        container_title = container_name
        container_description = ""

        file_list = None
        retval = 0
        stdout = ""
        stderr = ""

        try:
            container_metadata = self.batch_manager.get_batch_container_metadata(container_name)
            if container_metadata == (None, None, None):
                container_title = container_metadata[0]
                container_description = container_metadata[1]
        except:
            pass

        if "result" in batch_job:
            done = True
            retval = batch_job["result"]["retval"]
            stdout = batch_job["result"].get("stdout", "")
            stderr = batch_job["result"].get("stderr", "")

            if "file" in batch_job["result"]:
                f = self.gridfs.get(batch_job["result"]["file"])
                try:
                    tar = tarfile.open(fileobj=f, mode='r:gz')
                    file_list = set(tar.getnames()) - set([''])
                    tar.close()
                except:
                    pass
                finally:
                    f.close()

        return self.template_helper.get_renderer().course_admin.batch_summary(course, bid, done, container_name, container_title,
                                                                              container_description, submitted_on, retval, stdout, stderr, file_list)
