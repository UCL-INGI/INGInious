# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

urls = (
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
    r'/admin/([^/]+)/search_user/(.+)', 'inginious.frontend.pages.course_admin.search_user.CourseAdminSearchUserPage'
)
