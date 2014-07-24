""" Starts the frontend """

import web

from frontend.plugins.plugin_manager import PluginManager
import common.base
import frontend
import frontend.session

import frontend.base

urls = (
    '/', 'frontend.pages.index.IndexPage',
    '/index', 'frontend.pages.index.IndexPage',
    '/course/([^/]+)', 'frontend.pages.course.CoursePage',
    '/course/([^/]+)/([^/]+)', 'frontend.pages.tasks.TaskPage',
    '/admin/([^/]+)', 'frontend.pages.admin_course.AdminCourseStudentListPage',
    '/admin/([^/]+)/student/([^/]+)', 'frontend.pages.admin_course.AdminCourseStudentInfoPage',
    '/admin/([^/]+)/student/([^/]+)/([^/]+)', 'frontend.pages.admin_course.AdminCourseStudentTaskPage',
    '/admin/([^/]+)/tasks', 'frontend.pages.admin_course.AdminCourseTaskListPage',
    '/admin/([^/]+)/task/([^/]+)', 'frontend.pages.admin_course.AdminCourseTaskInfoPage',
)

app = None

def init_app(config_file):
    global app
    app = web.application(urls, globals(), autoreload=False)
    common.base.INGIniousConfiguration.load(config_file)

    frontend.base.init_database()
    frontend.session.init(app)
    
    from frontend import submission_manager
    def not_found():
        """ Display the error 404 page """
        return web.notfound(frontend.base.renderer.notfound())
    app.notfound = not_found

    submission_manager.init_backend_interface()

    # Must be done after everything else
    PluginManager(app, common.base.INGIniousConfiguration.get("plugins", []))

if __name__ == "__main__":
    init_app("./configuration.json")
    app.run()
