""" Starts the frontend """

import web

import frontend.pages
import frontend.session


urls = (
    '/', 'frontend.pages.index.IndexPage',
    '/index', 'frontend.pages.index.IndexPage',
    '/course/([^/]+)', 'frontend.pages.course.CoursePage',
    '/course/([^/]+)/([^/]+)', 'frontend.pages.tasks.TaskPage'
)

app = web.application(urls, globals())
frontend.session.init(app)

if __name__ == "__main__":
    app.run()