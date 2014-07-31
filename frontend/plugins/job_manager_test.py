""" JobManagerTest plugin """
import frontend.submission_manager


class JobManagerTest(object):

    """ Returns stats about the job manager for distant tests """

    def GET(self):
        """ GET request """
        return str(frontend.submission_manager.get_job_manager().get_waiting_jobs_count())


def init(plugin_manager, _):
    """ Init the plugin """
    plugin_manager.add_page("/tests/stats", "frontend.plugins.job_manager_test.JobManagerTest")
    print "Started JobManagerTest plugin"
