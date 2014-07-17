""" Starts the frontend """

import web

import common.base
import frontend.session


URLS = (
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

APP = web.application(URLS, globals())

if __name__ == "__main__":
    common.base.INGIniousConfiguration.load("./configuration.json")
    frontend.session.init(APP)

    # Must be done after frontend.session.init(app)
    import frontend.base

    def not_found():
        """ Display the error 404 page """
        return web.notfound(frontend.base.renderer.notfound())
    APP.notfound = not_found
    # Idem
    import frontend.submission_manager
    frontend.submission_manager.init_backend_interface()

    APP.run()
