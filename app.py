import web
import frontend
import frontend.pages
from frontend.session import sessionManager

urls = (
    '/', 'frontend.pages.index.IndexPage',
    '/index', 'frontend.pages.index.IndexPage',
    '/course/([^/]+)', 'frontend.pages.course.CoursePage',
    '/course/([^/]+)/([^/]+)', 'frontend.pages.tasks.TaskPage'
)

app = web.application(urls, globals())
sessionManager.init(app)

if __name__ == "__main__":
    app.run()