# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

urls = (
    r'/?', 'inginious.frontend.pages.index.IndexPage',
    r'/index', 'inginious.frontend.pages.index.IndexPage',
    r'/courselist', 'inginious.frontend.pages.courselist.CourseListPage',
    r'/pages/([^/]+)', 'inginious.frontend.pages.utils.INGIniousStaticPage',
    r'/signin', 'inginious.frontend.pages.utils.SignInPage',
    r'/logout', 'inginious.frontend.pages.utils.LogOutPage',
    r'/register', 'inginious.frontend.pages.register.RegistrationPage',
    r'/auth/signin/([^/]+)', 'inginious.frontend.pages.social.AuthenticationPage',
    r'/auth/callback/([^/]+)', 'inginious.frontend.pages.social.CallbackPage',
    r'/auth/share/([^/]+)', 'inginious.frontend.pages.social.SharePage',
    r'/register/([^/]+)', 'inginious.frontend.pages.course_register.CourseRegisterPage',
    r'/course/([^/]+)', 'inginious.frontend.pages.course.CoursePage',
    r'/course/([^/]+)/([^/]+)', 'inginious.frontend.pages.tasks.TaskPage',
    r'/course/([^/]+)/([^/]+)/(.*)', 'inginious.frontend.pages.tasks.TaskPageStaticDownload',
    r'/group/([^/]+)', 'inginious.frontend.pages.group.GroupPage',
    r'/queue', 'inginious.frontend.pages.queue.QueuePage',
    r'/mycourses', 'inginious.frontend.pages.mycourses.MyCoursesPage',
    r'/preferences', 'inginious.frontend.pages.preferences.utils.RedirectPage',
    r'/preferences/profile', 'inginious.frontend.pages.preferences.profile.ProfilePage',
    r'/preferences/bindings', 'inginious.frontend.pages.preferences.bindings.BindingsPage',
    r'/preferences/delete', 'inginious.frontend.pages.preferences.delete.DeletePage',
    r'/admin/([^/]+)', 'inginious.frontend.pages.course_admin.utils.CourseRedirect',
    r'/admin/([^/]+)/settings', 'inginious.frontend.pages.course_admin.settings.CourseSettings',
    r'/admin/([^/]+)/students', 'inginious.frontend.pages.course_admin.student_list.CourseStudentListPage',
    r'/admin/([^/]+)/student/([^/]+)', 'inginious.frontend.pages.course_admin.student_info.CourseStudentInfoPage',
    r'/submission/([^/]+)', 'inginious.frontend.pages.course_admin.submission.SubmissionPage',
    r'/admin/([^/]+)/submissions', 'inginious.frontend.pages.course_admin.submissions.CourseSubmissionsPage',
    r'/admin/([^/]+)/tasks', 'inginious.frontend.pages.course_admin.task_list.CourseTaskListPage',
    r'/admin/([^/]+)/tags', 'inginious.frontend.pages.course_admin.tags.CourseTagsPage',
    r'/admin/([^/]+)/edit/audience/([^/]+)', 'inginious.frontend.pages.course_admin.audience_edit.CourseEditAudience',
    r'/admin/([^/]+)/edit/task/([^/]+)', 'inginious.frontend.pages.course_admin.task_edit.CourseEditTask',
    r'/admin/([^/]+)/edit/task/([^/]+)/files', 'inginious.frontend.pages.course_admin.task_edit_file.CourseTaskFiles',
    r'/admin/([^/]+)/edit/task/([^/]+)/dd_upload', 'inginious.frontend.pages.course_admin.task_edit_file.CourseTaskFileUpload',
    r'/admin/([^/]+)/danger', 'inginious.frontend.pages.course_admin.danger_zone.CourseDangerZonePage',
    r'/admin/([^/]+)/stats', 'inginious.frontend.pages.course_admin.statistics.CourseStatisticsPage',
    r'/admin/([^/]+)/search_user/(.+)', 'inginious.frontend.pages.course_admin.search_user.CourseAdminSearchUserPage',
    r'/api/v0/auth_methods', 'inginious.frontend.pages.api.auth_methods.APIAuthMethods',
    r'/api/v0/authentication', 'inginious.frontend.pages.api.authentication.APIAuthentication',
    r'/api/v0/courses', 'inginious.frontend.pages.api.courses.APICourses',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)', 'inginious.frontend.pages.api.courses.APICourses',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks', 'inginious.frontend.pages.api.tasks.APITasks',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks/([a-zA-Z_\-\.0-9]+)', 'inginious.frontend.pages.api.tasks.APITasks',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks/([a-zA-Z_\-\.0-9]+)/submissions', 'inginious.frontend.pages.api.submissions.APISubmissions',
    r'/api/v0/courses/([a-zA-Z_\-\.0-9]+)/tasks/([a-zA-Z_\-\.0-9]+)/submissions/([a-zA-Z_\-\.0-9]+)',
        'inginious.frontend.pages.api.submissions.APISubmissionSingle',
    r'/lti/([^/]+)/([^/]+)', 'inginious.frontend.pages.lti.LTILaunchPage',
    r'/lti/bind', 'inginious.frontend.pages.lti.LTIBindPage',
    r'/lti/task', 'inginious.frontend.pages.lti.LTITaskPage',
    r'/lti/login', 'inginious.frontend.pages.lti.LTILoginPage',
    r'/lti/asset/(.*)', 'inginious.frontend.pages.lti.LTIAssetPage',
    r'/marketplace', 'inginious.frontend.pages.marketplace.Marketplace',
    r'/marketplace/([^/]+)', 'inginious.frontend.pages.marketplace_course.MarketplaceCourse'
)

urls_maintenance = (
    '/.*', 'inginious.frontend.pages.maintenance.MaintenancePage'
)
