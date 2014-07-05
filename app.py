import web
import frontend
import pages
from frontend.session import sessionManager

urls = (
    '/', 'pages.index.IndexPage',
    '/index', 'pages.index.IndexPage',
    '/course/([^/]+)', 'pages.course.CoursePage',
    '/course/([^/]+)/([^/]+)', 'pages.tasks.TaskPage'
)

app = web.application(urls, globals())
sessionManager.init(app)

if __name__ == "__main__":
    app.run()