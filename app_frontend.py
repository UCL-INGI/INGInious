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

#Must be done after frontend.session.init(app)
import frontend.base
def notfound():
    return web.notfound(frontend.base.renderer.notfound())
app.notfound = notfound

if __name__ == "__main__":
    app.run()